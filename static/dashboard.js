const state = {
  products: [],
  selectedId: null,
  alerts: [],
};

const $ = (sel) => document.querySelector(sel);
const fmtMoney = (n) => "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });
const fmtTime = (iso) => new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// ---------------------------------------------------------------- fetching
async function loadProducts() {
  const res = await fetch("/api/products");
  state.products = await res.json();
  if (!state.selectedId && state.products.length) {
    state.selectedId = state.products[0].id;
  }
  render();
}

async function loadAlerts() {
  const res = await fetch("/api/alerts");
  state.alerts = await res.json();
  renderAlerts();
}

async function refreshAll() {
  await Promise.all([loadProducts(), loadAlerts()]);
}

// ------------------------------------------------------------------ actions
async function addProduct(name, targetPrice) {
  const res = await fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, target_price: targetPrice }),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error || "Could not add product.");
  state.selectedId = body.product_id;
  await refreshAll();
}

async function checkPriceNow(productId) {
  const res = await fetch(`/api/products/${productId}/check`, { method: "POST" });
  if (!res.ok) return;
  await refreshAll();
}

// ------------------------------------------------------------------ render
function render() {
  renderWatchlist();
  renderDetail();
}

function renderWatchlist() {
  const list = $("#watchlist");
  if (!state.products.length) {
    list.innerHTML = `<li class="empty-row">No products yet — add one above.</li>`;
    return;
  }
  list.innerHTML = state.products
    .map((p) => {
      const d = p.latest_decision;
      const badge = d ? `<span class="badge ${d.verdict}">${d.verdict.replace("_", " ")}</span>` : "";
      const price = d ? fmtMoney(d.current_price) : fmtMoney(p.seed_price);
      const active = p.id === state.selectedId ? "active" : "";
      return `
        <li class="row ${active}" data-id="${p.id}">
          <span class="row-name">${escapeHtml(p.name)}</span>
          <span class="row-sub"><span>${price}</span>${badge}</span>
        </li>`;
    })
    .join("");

  list.querySelectorAll(".row").forEach((el) => {
    el.addEventListener("click", () => {
      state.selectedId = Number(el.dataset.id);
      render();
    });
  });
}

function renderDetail() {
  const pane = $("#detail-pane");
  const product = state.products.find((p) => p.id === state.selectedId);

  if (!product) {
    pane.innerHTML = `
      <div class="empty-state">
        <p>Select a product on the left, or add one to begin.</p>
        <p class="empty-sub">The agent will observe a price, analyze history, decide, and explain — automatically, and every 20s after that.</p>
      </div>`;
    return;
  }

  const d = product.latest_decision;
  const history = product.price_history || [];
  const current = d ? d.current_price : product.seed_price;
  const avg = d ? d.avg_price : product.seed_price;
  const change = d ? d.price_change : 0;
  const verdict = d ? d.verdict : "WAIT";
  const reasoning = d ? d.reasoning : "Waiting on the first price check…";
  const changeClass = change > 0 ? "up" : change < 0 ? "down" : "";
  const changeSign = change > 0 ? "+" : "";

  pane.innerHTML = `
    <div class="detail-header">
      <div>
        <h2>${escapeHtml(product.name)}</h2>
        <div class="since">watching since ${new Date(product.created_at).toLocaleString()}</div>
      </div>
      <button class="check-btn" id="check-now">Check price now</button>
    </div>

    <div class="stat-grid">
      <div class="stat"><div class="label">Current price</div><div class="value">${fmtMoney(current)}</div></div>
      <div class="stat"><div class="label">Target price</div><div class="value">${fmtMoney(product.target_price)}</div></div>
      <div class="stat"><div class="label">Historical average</div><div class="value">${fmtMoney(avg)}</div></div>
      <div class="stat"><div class="label">Change since last check</div><div class="value ${changeClass}">${changeSign}${fmtMoney(change)}</div></div>
    </div>

    <div class="verdict-panel">
      <span class="badge verdict-badge ${verdict}">${verdict.replace("_", " ")}</span>
      <div>
        <div class="reasoning-label">agent reasoning</div>
        <p>${escapeHtml(reasoning)}</p>
      </div>
    </div>

    <div class="section-title">Price history</div>
    <div class="chart-wrap">${sparkline(history, product.target_price)}</div>

    <table class="history">
      <thead><tr><th>Time</th><th>Price</th></tr></thead>
      <tbody>
        ${history.slice().reverse().slice(0, 12).map(h => `
          <tr><td>${fmtTime(h.observed_at)}</td><td>${fmtMoney(h.price)}</td></tr>
        `).join("") || `<tr><td colspan="2">No observations yet.</td></tr>`}
      </tbody>
    </table>
  `;

  $("#check-now").addEventListener("click", async (e) => {
    e.target.disabled = true;
    e.target.textContent = "Checking…";
    await checkPriceNow(product.id);
  });
}

function renderAlerts() {
  const list = $("#alerts-list");

  const count = document.getElementById("alert-count");

if (count) {
    count.textContent = state.alerts.length;
}
  if (!state.alerts.length) {
    list.innerHTML = `<li class="empty-row">No alerts yet.</li>`;
    return;
  }
  list.innerHTML = state.alerts
    .slice(0, 25)
    .map(
      (a) => `
      <li class="alert-card ${a.verdict}">
        <div class="alert-meta">${escapeHtml(a.product_name)} · ${fmtTime(a.created_at)}</div>
        ${escapeHtml(a.message)}
      </li>`
    )
    .join("");
}

function sparkline(history, targetPrice) {
  if (!history.length) {
    return `<svg viewBox="0 0 400 100" width="100%" height="100"></svg>`;
  }
  const prices = history.map((h) => h.price);
  const min = Math.min(...prices, targetPrice);
  const max = Math.max(...prices, targetPrice);
  const range = max - min || 1;
  const w = 400, h = 100, pad = 6;

  const pt = (i, price) => {
    const x = prices.length === 1 ? w / 2 : pad + (i / (prices.length - 1)) * (w - pad * 2);
    const y = h - pad - ((price - min) / range) * (h - pad * 2);
    return [x, y];
  };

  const points = prices.map((p, i) => pt(i, p));
  const linePath = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const targetY = h - pad - ((targetPrice - min) / range) * (h - pad * 2);

  return `
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="100" preserveAspectRatio="none">
      <line x1="0" y1="${targetY.toFixed(1)}" x2="${w}" y2="${targetY.toFixed(1)}"
            stroke="#ff6b6b" stroke-width="1" stroke-dasharray="4 3" />
      <path d="${linePath}" fill="none" stroke="#8b7fff" stroke-width="1.75" />
      ${points.map(([x, y]) => `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.2" fill="#8b7fff" />`).join("")}
    </svg>`;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// ------------------------------------------------------------------- init
$("#add-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#add-btn");
  const errEl = $("#form-error");
  errEl.textContent = "";
  const name = $("#product-name").value.trim();
  const targetPrice = $("#target-price").value;

  btn.disabled = true;
  btn.textContent = "Adding…";
  try {
    await addProduct(name, targetPrice);
    $("#add-form").reset();
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "+ Add product";
  }
});

refreshAll();
setInterval(refreshAll, 6000); // picks up background-monitor updates automatically
