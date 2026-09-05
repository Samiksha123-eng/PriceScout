"""
database.py
-----------
All persistence for PriceScout lives here: a single SQLite file with four
tables. No ORM — plain sqlite3 so the whole data layer is readable in one
file.

Tables:
    products       one row per product the agent is watching
    price_history  one row per price observation (the agent's "memory")
    decisions      one row per decision the Decision Agent has made
    alerts         one row per alert the Notification Agent has raised
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = "pricescout.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                target_price    REAL NOT NULL,
                seed_price      REAL NOT NULL,
                created_at      TEXT NOT NULL,
                active          INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price           REAL NOT NULL,
                observed_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS decisions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                current_price   REAL NOT NULL,
                avg_price       REAL NOT NULL,
                price_change    REAL NOT NULL,
                verdict         TEXT NOT NULL,
                reasoning       TEXT NOT NULL,
                decided_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id      INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                message         TEXT NOT NULL,
                verdict         TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                seen            INTEGER NOT NULL DEFAULT 0
            );
            """
        )


# ---------------------------------------------------------------- products
def add_product(name: str, target_price: float, seed_price: float) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, target_price, seed_price, created_at, active) "
            "VALUES (?, ?, ?, ?, 1)",
            (name, target_price, seed_price, _now()),
        )
        return cur.lastrowid


def list_products(active_only: bool = True):
    with get_conn() as conn:
        q = "SELECT * FROM products"
        if active_only:
            q += " WHERE active = 1"
        q += " ORDER BY created_at DESC"
        return [dict(r) for r in conn.execute(q).fetchall()]


def get_product(product_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None


def deactivate_product(product_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))


# ------------------------------------------------------------ price history
def add_price(product_id: int, price: float):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price, observed_at) VALUES (?, ?, ?)",
            (product_id, price, _now()),
        )


def get_price_history(product_id: int, limit: int = 200):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT price, observed_at FROM price_history "
            "WHERE product_id = ? ORDER BY id ASC LIMIT ?",
            (product_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


# --------------------------------------------------------------- decisions
def add_decision(product_id: int, current_price: float, avg_price: float,
                  price_change: float, verdict: str, reasoning: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO decisions "
            "(product_id, current_price, avg_price, price_change, verdict, reasoning, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (product_id, current_price, avg_price, price_change, verdict, reasoning, _now()),
        )
        return cur.lastrowid


def get_latest_decision(product_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM decisions WHERE product_id = ? ORDER BY id DESC LIMIT 1",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None


# ------------------------------------------------------------------ alerts
def add_alert(product_id: int, message: str, verdict: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (product_id, message, verdict, created_at, seen) "
            "VALUES (?, ?, ?, ?, 0)",
            (product_id, message, verdict, _now()),
        )
        return cur.lastrowid


def list_alerts(product_id: int = None, limit: int = 50):
    with get_conn() as conn:
        if product_id is None:
            rows = conn.execute(
                "SELECT alerts.*, products.name AS product_name FROM alerts "
                "JOIN products ON products.id = alerts.product_id "
                "ORDER BY alerts.id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE product_id = ? ORDER BY id DESC LIMIT ?",
                (product_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
