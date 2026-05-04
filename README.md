# 🔬 Multi-Agent Research Assistant

A production-ready AI research pipeline using a **multi-agent architecture** to search, verify, and generate structured reports.

---

## 🚀 Key Features

| Feature | Implementation |
|---|---|
| 🧠 **Memory System** | Stores previous queries for contextual responses |
| 🔍 **Real-Time Search** | Tavily API for live web data |
| ⚡ **Parallel Fact-Checking** | Uses `asyncio.gather` for faster verification |
| 📌 **Key Points Extraction** | Generates bullet-point insights |
| 📊 **Confidence Score** | Indicates reliability of results |
| 🔗 **Source Transparency** | Displays URLs used in research |
| 💾 **Report Export** | Saves output as `.md` and `.pdf` |
| 🌐 **Web UI** | Streamlit-based interactive dashboard |
| 🤖 **LLM (Groq)** | Uses LLaMA 3.1 via `langchain-groq` |

---

## 🏗️ Architecture


```
User Query
↓
🔍 Search Agent → Tavily web search (real-time results)
↓
⚡ Fact-Check Agent ×N → Parallel verification (asyncio)
↓
🧠 Summarizer Agent → Generates structured summary + key points
↓
📄 Report Agent → Final formatted report
↓
📊 Confidence + 🔗 Sources
↓
💾 Saved as .md + .pdf
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
# Edit .env and add your keys:
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here   ← Free at tavily.com
```

---

## Usage

### 🌐 Web UI (Streamlit)
```bash
python -m streamlit run app.py```

Then open http://localhost:8501 in your browser.

### 💻 Command Line
```bash
python main.py
```

---

## Project Structure

```
multi_agent_research/
├── app.py                  # Streamlit UI
├── main.py                 # CLI interface
├── requirements.txt
├── .env
├── agents/
│   └── pipeline.py         # Multi-agent pipeline (LangGraph)
├── utils/
│   ├── memory.py           # Memory handling
│   └── report_saver.py     # Markdown + PDF export
└── output/                 # Generated reports
```

---

## Get API Keys

Groq (LLM): https://console.groq.com
Tavily Search: https://app.tavily.com (free tier available)
