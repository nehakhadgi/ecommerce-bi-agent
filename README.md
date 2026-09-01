# 📊 E-Commerce AI Business Intelligence (BI) Agent

An enterprise-grade, autonomous AI Business Intelligence Agent designed to analyze real-world e-commerce transaction datasets. Built using **Streamlit**, **Pandas**, and the flagship **Google GenAI SDK (Gemini 3.6)**, this agent parses natural language business questions, dynamically decides which internal data-analysis tools to execute, handles complex visualizations, and provides data-backed, conversational insights.

Live Demo: [View Live Dashboard on Streamlit Cloud](https://share.streamlit.io/)

---

## 🚀 Key Features

* **Natural Language BI Queries:** Users can ask conversational business questions (e.g., "What is our overall profit margin?" or "Which product category makes the most profit?") and receive exact, data-backed summaries.
* **Autonomous Tool Orchestration:** Powered by Google's native function calling, the agent dynamically decides when to run calculation metrics versus plotting charts based on user intent.
* **On-Demand Visualizations:** Generates high-fidelity Matplotlib bar and line graphs representing monthly trends, category sales, and regional revenue breakdowns.
* **State Preservation:** Keeps chat history and rendered charts persistently active on-screen during active Streamlit user sessions.

---

## 🛠️ Advanced Architectural Decisions (Developer Highlights)

This application implements several advanced patterns to resolve complex API, deployment, and cloud-provider challenges:

### 1. The "Absorber Pattern" (Tool Argument Protection)
To bypass LLM parameter hallucination (where Gemini passes unmapped parameters like `{"profit": true}` to simple metadata tools), all Python tool mapping lambdas are secured with catch-all argument unpacking (`*args, **kwargs`). This ensures hallucinated parameters are safely absorbed and discarded without triggering Python `TypeError` crashes.

### 2. Gemini 3.6 API Gateway Schema Alignment
Google recently deprecated and restricted the `"tool"` role on newer v1beta developer endpoints. To ensure full compatibility with `gemini-3.6-flash`, the tool execution payload maps all structural `FunctionResponse` objects to the `"user"` role prior to sending final inference completions.

### 3. Matplotlib Headless "Agg" Backend Integration
To prevent severe application crashes inside Streamlit's headless Linux cloud server environment (where no GUI window exists), Matplotlib is explicitly configured to use the non-interactive `"Agg"` backend via `matplotlib.use("Agg")`.

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
Inside the `.env` file, paste your Gemini API key (ensure you isolate this inside a dedicated, new project on Google AI Studio to separate your daily quotas):
```text
GOOGLE_API_KEY="your_isolated_gemini_api_key"
```

### 5. Launch the Local Server
```powershell
streamlit run app.py
```

---

## ☁️ Streamlit Cloud Deployment Guide

1. Push your repository to **GitHub** (confirming that `.env` and `venv/` are correctly ignored by checking `git status`).
2. Connect your repository to **Streamlit Community Cloud**.
3. Under your Streamlit application's **Settings > Secrets** panel, securely configure your API key:
   ```toml
   GOOGLE_API_KEY = "your_isolated_gemini_api_key"
   ```
4. Click Save and let your dashboard build!
