# app.py — Streamlit Web UI for Multi-Agent Research Assistant

import os
import streamlit as st

from agents.pipeline import build_pipeline, ResearchState
from utils.memory import ResearchMemory
from utils.report_saver import save_markdown, save_pdf

# ── Page config ──
st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide",
)

# ── CSS ──
st.markdown("""
<style>
body { background: #0d0f14; color: #e8eaf0; }

.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #a78bfa;
    text-align: center;
}

.hero-sub {
    color: #6b7280;
    text-align: center;
    margin-bottom: 20px;
}

/* Report card */
.report-card {
    background: #13161e;
    border: 1px solid #1f2330;
    border-radius: 12px;
    padding: 1.5rem;
    white-space: pre-wrap;
}

/* Section boxes */
.section-box {
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
}

.keypoints-box { border-left: 5px solid #3b82f6; background: #13161e; }
.sources-box { border-left: 5px solid #f59e0b; background: #13161e; }
.confidence-box { border-left: 5px solid #22c55e; background: #13161e; }

</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "memory" not in st.session_state:
    st.session_state.memory = ResearchMemory()
if "results" not in st.session_state:
    st.session_state.results = []

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ Configuration")

    groq_key = st.text_input("Groq API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")

    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key

# ── Main UI ──
st.markdown('<div class="hero-title">Multi-Agent Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">⚡ Parallel fact-checking · 🧠 Smart memory · 📊 Structured reports</div>', unsafe_allow_html=True)

query = st.text_input("🔍 Enter your research query")

# ── Run pipeline ──
if st.button("🚀 Generate Report"):

    if not query.strip():
        st.warning("Please enter a query")
    elif not os.getenv("GROQ_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        st.error("Please enter API keys in sidebar")
    else:
        with st.spinner("Generating report..."):

            # 🔄 Show steps (cool UI)
            st.write("🔍 Searching...")
            st.write("🧠 Summarizing...")
            st.write("✅ Fact-checking...")
            st.write("📄 Generating report...")

            pipeline = build_pipeline()

            initial: ResearchState = {
                "query": query,
                "memory_context": st.session_state.memory.get_context(),
                "search_results": [],
                "fact_check_raw": [],
                "summary": "",
                "fact_check": "",
                "final_report": "",
                "key_points": "",
                "sources": [],
                "confidence": "",
                "status": "Starting..."
            }

            result = pipeline.invoke(initial)

            # Save memory
            st.session_state.memory.add_interaction(query, result["summary"])
            st.session_state.results.insert(0, result)

# ── Display ──
if st.session_state.results:

    latest = st.session_state.results[0]

    # 📄 REPORT
    st.subheader("📄 Research Report")
    st.markdown(
        f'<div class="report-card">{latest["final_report"]}</div>',
        unsafe_allow_html=True
    )

    # 📌 KEY POINTS
    st.markdown('<div class="section-box keypoints-box">', unsafe_allow_html=True)
    st.subheader("📌 Key Insights")
    st.write(latest.get("key_points", "Not available"))
    st.markdown('</div>', unsafe_allow_html=True)

    # 📊 CONFIDENCE
    st.markdown('<div class="section-box confidence-box">', unsafe_allow_html=True)
    st.subheader("📊 Confidence Level")
    st.success(latest.get("confidence", "N/A"))
    st.markdown('</div>', unsafe_allow_html=True)

    # 🔗 SOURCES
    st.markdown('<div class="section-box sources-box">', unsafe_allow_html=True)
    st.subheader("🔗 Sources Used")
    for s in latest.get("sources", []):
        st.write(f"🔗 {s}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 🧠 MEMORY DISPLAY (BONUS)
    if st.session_state.memory.has_history:
        st.subheader("🧠 Previous Queries")
        st.text(st.session_state.memory.get_context())

    # 📥 DOWNLOADS (FIXED)
    md_path = save_markdown(latest["query"], latest["final_report"], latest["fact_check"])
    pdf_path = save_pdf(latest["query"], latest["final_report"], latest["fact_check"])

    with open(md_path, "r", encoding="utf-8") as f:
        md_data = f.read()

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    st.download_button(
        label="📄 Download Markdown",
        data=md_data,
        file_name="report.md",
        mime="text/markdown"
    )

    st.download_button(
        label="📕 Download PDF",
        data=pdf_data,
        file_name="report.pdf",
        mime="application/pdf"
    )