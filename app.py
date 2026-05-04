import os
import streamlit as st
 
from agents.pipeline import build_pipeline, ResearchState
from utils.memory import ResearchMemory
from utils.report_saver import save_markdown, save_pdf
 
st.set_page_config(page_title="Research Assistant", layout="wide")
 
# ── Session State ──
if "memory" not in st.session_state:
    st.session_state.memory = ResearchMemory()
 
if "results" not in st.session_state:
    st.session_state.results = []
 
if "files" not in st.session_state:
    st.session_state.files = {"md": None, "pdf": None}
 
st.title("🔬 Multi-Agent Research Assistant")
 
# ── Sidebar ──
with st.sidebar:
    st.header("🔑 API Keys")
 
    groq_key = st.text_input("Groq API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")
 
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
 
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key
 
    st.markdown("---")
    if st.button("🗑️ Clear Memory"):
        st.session_state.memory.clear()
        st.success("Memory cleared!")
 
# ── Input ──
query = st.text_input("📌 Enter your research topic")
 
# ── Run Pipeline ──
if st.button("🚀 Generate Research Paper"):
    if not query:
        st.warning("⚠️ Please enter a research topic")
    else:
        status = st.empty()
 
        def update(msg):
            status.info(msg)
 
        try:
            pipeline = build_pipeline(progress_callback=update)
 
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
                "status": "Starting...",
                "architecture_data": {},
                "ablation_data": {},
                "performance_data": {},
            }
 
            result = pipeline.invoke(initial)
 
            # Save memory
            st.session_state.memory.add_interaction(query, result["summary"])
 
            # Store result
            st.session_state.results = [result]
 
            # Reset file cache
            st.session_state.files = {"md": None, "pdf": None}
 
            status.success("✅ Research paper generated!")
 
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
 
 
# ── Display Results ──
if st.session_state.results:
    r = st.session_state.results[0]
    query_text = r.get("query", "research")
 
    tab1, tab2, tab3 = st.tabs(["📄 Research Paper", "📊 Visual Insights", "📥 Download"])
 
    with tab1:
        st.subheader("📄 Research Paper")
        st.write(r.get("final_report", ""))
 
        st.subheader("📌 Key Points")
        st.write(r.get("key_points", ""))
 
        st.subheader("📊 Confidence")
        conf = r.get("confidence", "N/A")
        if conf == "High":
            st.success(conf)
        elif conf == "Medium":
            st.warning(conf)
        else:
            st.error(conf)
 
        st.subheader("🔗 Sources")
        for s in r.get("sources", []):
            st.write(s)
 
    with tab2:
        st.subheader("📊 Visual Insights (Topic-Specific)")
 
        graph1 = "output/performance_graph.png"
        graph2 = "output/ablation_graph.png"
        diagram = "output/architecture.png"
 
        col1, col2 = st.columns(2)
 
        with col1:
            if os.path.exists(graph1):
                perf_data = r.get("performance_data", {})
                st.image(graph1, caption=perf_data.get("title", "Performance Graph"))
 
        with col2:
            if os.path.exists(graph2):
                abl_data = r.get("ablation_data", {})
                st.image(graph2, caption=abl_data.get("title", "Ablation Study"))
 
        if os.path.exists(diagram):
            arch_data = r.get("architecture_data", {})
            st.image(diagram, caption=arch_data.get("title", "Architecture Diagram"))
 
    with tab3:
        st.subheader("📥 Download Research Paper")
 
        # Generate files ONLY once
        if st.session_state.files["pdf"] is None:
            md_path = save_markdown(query_text, r["final_report"], r["fact_check"])
            pdf_path = save_pdf(
                query_text,
                r["final_report"],
                r["fact_check"],
                architecture_data=r.get("architecture_data"),
                ablation_data=r.get("ablation_data"),
                performance_data=r.get("performance_data"),
            )
            st.session_state.files["md"] = md_path
            st.session_state.files["pdf"] = pdf_path
 
        with open(st.session_state.files["md"], "r", encoding="utf-8") as f:
            md_data = f.read()
 
        with open(st.session_state.files["pdf"], "rb") as f:
            pdf_data = f.read()
 
        st.info("📄 The PDF includes topic-specific architecture diagram, ablation study, and performance graph.")
 
        st.download_button(
            "📄 Download Markdown",
            md_data,
            "research_paper.md",
            mime="text/markdown"
        )
 
        st.download_button(
            "📕 Download PDF",
            pdf_data,
            "research_paper.pdf",
            mime="application/pdf"
        )