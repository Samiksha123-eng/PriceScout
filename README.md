# 🤖 PriceScout

## Autonomous AI Price Monitoring Agent

PriceScout is an autonomous AI agent that monitors product prices, analyzes price information, and evaluates the user's target price.

It uses multiple specialized agents to make purchase-related decisions and provide AI-generated reasoning and recommendations.

---

## 🤖 Agents

### 1. Price Agent
Monitors and manages product price information.

Obtains the current price and provides the required price data for further analysis.

### 2. Analysis Agent
Analyzes current and historical price information.

Identifies price conditions and provides analysis to the decision-making agent.

### 3. Decision Agent
Makes the purchase-related decision based on price analysis and the user's target price.

Determines whether the user should buy, wait, or continue monitoring.

### 4. Notification Agent
Handles price alerts and notifications.

Informs the user when a favorable price condition is detected.

### 5. Orchestrator Agent
Coordinates all the specialized agents and manages the complete autonomous workflow.

Connects the Price, Analysis, Decision, and Notification agents into one workflow.

---

## 🧠 LLM

**LLM:** Price Monitoring Agent
---

## 🛠️ Tools

- Python
- Flask
- Anthropic API
- HTML
- CSS
- JavaScript
- SQLite
- Git
- GitHub
- VS Code

---

## 🔄 Agent Workflow

```text
User
 ↓
Price Agent
 ↓
Analysis Agent
 ↓
Decision Agent
 ↓
LLM Reasoning
 ↓
Notification Agent
 ↓
User
```

---

## 📁 Project Structure

```text
PriceScout/
│
├── agents/
│   ├── __init__.py
│   ├── price_agent.py
│   ├── analysis_agent.py
│   ├── decision_agent.py
│   ├── notification_agent.py
│   ├── orchestrator.py
│   └── llm_reasoning.py
│
├── static/
│   ├── dashboard.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── app.py
├── database.py
├── requirements.txt
├── test_workflow.py
├── README.md
└── .gitignore
```

---

## ▶️ VS Code Running Commands

### 1. Open the project

```powershell
cd PriceScout
```

### 2. Create virtual environment

```powershell
python -m venv .venv
```

### 3. Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run the project

```powershell
python app.py
```

### 6. Open in browser

```text
http://localhost:5000
```

---

## 💻 Terminal Input

After running:

```powershell
python app.py
```

Enter:

```text
Enter product name (or 'exit'): Sony
Enter target price: 2222
```

To exit:

```text
exit
```

---

## 🧪 Testing

Run:

```powershell
python test_workflow.py
```

---

## 🔄 Git Commands

Check status:

```powershell
git status
```

Add changes:

```powershell
git add .
```

Commit:

```powershell
git commit -m "Update PriceScout"
```

Push to GitHub:

```powershell
git push
```