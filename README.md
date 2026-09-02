
# 📊 E-Commerce AI Business Intelligence (BI) Agent

An enterprise-grade, autonomous AI Business Intelligence Agent designed to analyze real-world e-commerce transaction datasets. Built using **Streamlit**, **Pandas**, and the flagship **Google GenAI SDK (Gemini 3.6)**, this agent parses natural language business questions, dynamically decides which internal data-analysis tools to execute, handles complex visualizations, and provides data-backed, conversational insights.

Live Demo: [View Live Dashboard on Streamlit Cloud](https://share.streamlit.io/)

---

## 🚀 Key Features

* **Natural Language BI Queries:** Users can ask conversational business questions (e.g., "What is our overall profit margin?" or "Which product category makes the most profit?") and receive exact, data-backed summaries.
* **Autonomous Tool Orchestration:** Powered by Google's native function calling, the agent dynamically decides when to run calculation metrics versus plotting charts based on user intent.
* **On-Demand Visualizations:** Generates high-fidelity Matplotlib bar and line graphs representing monthly trends, category sales, and regional revenue breakdowns.
* **Multi-Turn Stateful Memory:** Features a high-fidelity memory pipeline that preserves past text and complex tool execution structures, enabling users to ask follow-up questions (e.g., "Explain that chart in detail").
* **Automated Key Rotation & Resiliency:** Cycles through up to 5 unique API keys silently when encountering daily quotas, ensuring continuous service without application downtime.
* **Secure Diagnostic Panel:** Features a sidebar diagnostic panel displaying the key rotation index, validation status, and key lengths—while completely masking actual key characters for enterprise security.

---

## 🛠️ Advanced Architectural Decisions (Developer Highlights)

This application implements several advanced patterns to resolve complex API, deployment, and cloud-provider challenges:

### 1. High-Fidelity Stateful Memory Pipeline (`api_history`)
By default, LLM APIs are stateless. To enable complex follow-up queries (such as asking the agent to explain a chart it just generated), this app implements a dual-state architecture. It uses Streamlit's `session_state` to render clean UI turns while maintaining a separate, structured `api_history` array. This array explicitly preserves intermediate `FunctionCall` and `FunctionResponse` payloads, giving the model full visibility of retrieved data.

### 2. Robust Content Extraction & Stateless Fallback
Under heavy server load, a retried request may occasionally succeed in connecting but return an empty content block. To prevent application crashes or `None` responses, the agent implements a custom `extract_text_safely` pipeline. If a multi-turn history block fails, the system automatically falls back to a stateless execution containing the active user prompt and raw tool output.

### 3. The "Absorber Pattern" (Tool Argument Protection)
To bypass LLM parameter hallucination (where Gemini passes unmapped parameters like `{"profit": true}` to simple metadata tools), all Python tool mapping lambdas are secured with catch-all argument unpacking (`*args, **kwargs`). This ensures hallucinated parameters are safely absorbed and discarded without triggering Python `TypeError` crashes.

### 4. Resilient 503 Server Error Backoff Handler
Shared Free Tier instances frequently experience brief server traffic spikes. This agent wraps all LLM generation executions in an automated retry wrapper that intercepts HTTP 503 responses, displays a friendly UI warning, and triggers an exponential backoff loop before throwing fatal errors.

### 5. Multi-Type Serialization Pipeline
Since Pandas DataFrames and Series are not natively JSON-serializable by the Gemini SDK, a custom serialization layer is implemented inside `app.py`. DataFrames are coerced through an optimized JSON-string roundtrip (`json.loads(df.to_json())`) to translate numeric datatypes cleanly into standard Python primitives.

---

## 📂 Project Structure

```text
├── app.py                      # Streamlit frontend UI & GenAI Agent Orchestration
├── tools.py                    # Pandas analytical tools & Matplotlib rendering logic
├── ecommerce_sales_data.csv    # Target transactional dataset (3,500+ records)
├── .env                        # Local secret configurations (Git-ignored!)
├── .gitignore                  # Active Git ignore rules safeguarding keys & venv
└── requirements.txt            # System dependencies
```

---

## ⚙️ Local Installation & Setup (Windows PowerShell)

Ensure you have **Python 3.10+** installed on your system.

### 1. Clone the Repository
```powershell
git clone https://github.com/yourusername/ecommerce-bi-agent.git
cd ecommerce-bi-agent
```

### 2. Configure Your Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Local Environment Variables
Create a file named `.env` in the root folder:
```powershell
code .env
```
Inside the `.env` file, paste your list of 53-character Gemini API keys (comma-separated, no spaces, no inner quotes):
```text
GOOGLE_API_KEYS="AQ.Ab8RN...,AQ.Ab8RN..."
```

### 5. Launch the Local Server
```powershell
streamlit run app.py
```

---

## ☁️ Streamlit Cloud Deployment Guide

1. Push your repository to **GitHub** (confirming that `.env` and `venv/` are correctly ignored by checking `git status`).
2. Connect your repository to **Streamlit Community Cloud**.
3. Under your Streamlit application's **Settings > Secrets** panel, securely configure your API keys:
   ```toml
   GOOGLE_API_KEYS = "AQ.Ab8RN...,AQ.Ab8RN..."
   ```
4. Click Save and let your dashboard build!
