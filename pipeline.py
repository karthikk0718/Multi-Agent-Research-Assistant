# agents/pipeline.py
 
import asyncio
import os
import json
import re
from typing import TypedDict, List, Callable, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
 
load_dotenv()
 
 
# ── LLM SETUP ──
def _build_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("❌ GROQ_API_KEY not found. Set it in .env or Streamlit.")
 
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.3,
        max_tokens=2000
    )
 
 
# ── SEARCH SETUP ──
def _build_search():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("❌ TAVILY_API_KEY not found. Set it in .env or Streamlit.")
 
    return TavilySearchResults(
        max_results=6,
        tavily_api_key=api_key
    )
 
 
# ── STATE ──
class ResearchState(TypedDict):
    query: str
    memory_context: str
    search_results: List[str]
    fact_check_raw: List[str]
    summary: str
    fact_check: str
    final_report: str
    key_points: str
    sources: List[str]
    confidence: str
    status: str
    # New fields for topic-specific visual data
    architecture_data: dict
    ablation_data: dict
    performance_data: dict
 
 
# ── SEARCH AGENT ──
def search_agent(state: ResearchState) -> ResearchState:
    state["status"] = "🔍 Searching the web..."
 
    search = _build_search()
    results = search.invoke(state["query"])
 
    contents = []
    sources = []
 
    for r in results:
        if isinstance(r, dict):
            contents.append(r.get("content", ""))
            sources.append(r.get("url", "N/A"))
        elif isinstance(r, str):
            contents.append(r)
            sources.append("N/A")
 
    state["search_results"] = contents
    state["sources"] = sources
 
    return state
 
 
# ── FACT CHECK ──
async def _fact_check_single(llm, claim: str, query: str) -> str:
    prompt = f"""
Context: {query}
 
Verify this claim.
Respond with: TRUE / PARTIAL / FALSE + short reason
 
Claim:
{claim}
"""
    response = await llm.ainvoke(prompt)
    return response.content
 
 
async def parallel_fact_check(state: ResearchState) -> ResearchState:
    state["status"] = "✅ Fact-checking..."
 
    llm = _build_llm()
 
    tasks = [
        _fact_check_single(llm, str(s), state["query"])
        for s in state["search_results"][:5]
    ]
 
    results = await asyncio.gather(*tasks)
    state["fact_check_raw"] = list(results)
 
    return state
 
 
# ── SUMMARIZER ──
def summarizer_agent(state: ResearchState) -> ResearchState:
    state["status"] = "🧠 Summarizing..."
 
    llm = _build_llm()
 
    combined = "\n\n".join([str(x) for x in state["search_results"][:5]])
 
    prompt = f"""
Previous Context:
{state['memory_context']}
 
Summarize clearly.
 
Provide:
1. A paragraph summary
2. 5 bullet key points
 
Data:
{combined}
"""
 
    response = llm.invoke(prompt).content
 
    lines = response.split("\n")
    state["summary"] = lines[0]
 
    bullets = [
        l.strip() for l in lines
        if l.strip().startswith("-") or l.strip().startswith("•")
    ]
 
    state["key_points"] = "\n".join(bullets) if bullets else "Not available"
 
    return state
 
 
# ── VISUAL DATA GENERATOR ──
def _extract_json(text: str) -> dict:
    """Safely extract JSON from LLM response, stripping markdown fences."""
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {}
 
 
def visual_data_agent(state: ResearchState) -> ResearchState:
    state["status"] = "📊 Generating visual data for topic..."
 
    llm = _build_llm()
    query = state["query"]
    summary = state["summary"]
 
    # ── Architecture Data ──
    arch_prompt = f"""
You are a research assistant. Based on the topic below, generate a system/pipeline architecture
that would be used in a research paper about this topic.
 
Topic: {query}
Summary: {summary}
 
Return ONLY a valid JSON object (no explanation, no markdown, no backticks) in this exact format:
{{
  "title": "Architecture title for this topic",
  "components": [
    {{"name": "Component 1", "description": "What it does"}},
    {{"name": "Component 2", "description": "What it does"}},
    {{"name": "Component 3", "description": "What it does"}},
    {{"name": "Component 4", "description": "What it does"}},
    {{"name": "Component 5", "description": "What it does"}}
  ],
  "flow": [
    ["Component 1", "Component 2"],
    ["Component 2", "Component 3"],
    ["Component 3", "Component 4"],
    ["Component 4", "Component 5"]
  ]
}}
"""
    arch_response = llm.invoke(arch_prompt).content
    state["architecture_data"] = _extract_json(arch_response)
 
    # ── Ablation Data ──
    ablation_prompt = f"""
You are a research assistant. Based on the topic below, generate a realistic ablation study
that would appear in a research paper about this topic. An ablation study shows how removing
each component affects performance.
 
Topic: {query}
 
Return ONLY a valid JSON object (no explanation, no markdown, no backticks) in this exact format:
{{
  "title": "Ablation Study title",
  "metric_name": "Name of performance metric (e.g. Accuracy, F1-Score, BLEU Score, mAP)",
  "variants": [
    {{"label": "Full Model", "score": 91.5}},
    {{"label": "Without [key component 1]", "score": 78.0}},
    {{"label": "Without [key component 2]", "score": 82.3}},
    {{"label": "Without [key component 3]", "score": 74.1}},
    {{"label": "Baseline Only", "score": 65.0}}
  ]
}}
Use realistic scores relevant to this topic. Full Model must have the highest score.
"""
    ablation_response = llm.invoke(ablation_prompt).content
    state["ablation_data"] = _extract_json(ablation_response)
 
    # ── Performance Data ──
    perf_prompt = f"""
You are a research assistant. Based on the topic below, generate realistic performance metrics
showing how results improve as a key variable increases (e.g. more data, more layers, more epochs, more features).
 
Topic: {query}
 
Return ONLY a valid JSON object (no explanation, no markdown, no backticks) in this exact format:
{{
  "title": "Performance graph title",
  "x_label": "Name of the variable on X axis (e.g. Training Epochs, Dataset Size, Model Depth)",
  "y_label": "Name of metric on Y axis (e.g. Accuracy (%), F1-Score, Loss)",
  "x_values": [1, 2, 3, 4, 5, 6, 7, 8],
  "y_values": [55.0, 63.2, 70.5, 76.8, 82.1, 86.4, 89.0, 91.5]
}}
Use realistic values that trend upward. Values should make sense for this topic.
"""
    perf_response = llm.invoke(perf_prompt).content
    state["performance_data"] = _extract_json(perf_response)
 
    return state
 
 
# ── REPORT GENERATOR ──
def report_agent(state: ResearchState) -> ResearchState:
    state["status"] = "📄 Generating research paper..."
 
    llm = _build_llm()
 
    prompt = f"""
Generate a HIGH-QUALITY IEEE-style research paper on the topic below.
 
STRICT REQUIREMENTS:
- EACH SECTION must be 200-250 words minimum
- NO filler content
- Deep explanation with clarity
- Clear paragraph separation
- Academic tone
- Write about the TOPIC, not about any tool or assistant
 
STRUCTURE:
 
Title
 
Author and Affiliation
 
Abstract (200 words)
 
Keywords
 
1. Introduction (200-250 words)
2. Related Work (150-200 words)
3. Methodology (200-250 words)
4. Algorithm / Pseudocode (detailed, with step-by-step explanation)
5. Mathematical Formulation (relevant equations with explanation)
6. Architecture Description (describe the architecture — refer to the architecture diagram in the paper)
7. Ablation Study Analysis (analyse the ablation results — refer to the ablation table in the paper)
8. Performance Evaluation (analyse the performance graph — refer to the performance graph in the paper)
9. Results and Discussion (deep insights, 200 words)
10. Conclusion (150-200 words)
11. References (at least 8 real references)
 
IMPORTANT:
- Leave ONE blank line between paragraphs
- DO NOT merge sections
- DO NOT generate short content
- The architecture diagram, ablation study table, and performance graph will be inserted separately as figures.
  Refer to them naturally in sections 6, 7, and 8 (e.g. "As shown in Figure 1...", "Table 1 presents...")
 
Topic: {state['query']}
Summary: {state['summary']}
Fact-check insights: {state['fact_check_raw']}
"""
 
    response = llm.invoke(prompt)
    report = response.content if hasattr(response, "content") else str(response)
 
    state["final_report"] = report
 
    # Confidence logic
    fact_text = " ".join(state["fact_check_raw"]).lower()
    if "false" in fact_text:
        state["confidence"] = "Low"
    elif "partial" in fact_text:
        state["confidence"] = "Medium"
    else:
        state["confidence"] = "High"
 
    state["fact_check"] = "\n".join(state["fact_check_raw"])
    state["status"] = "✅ Research Paper Generated"
 
    return state
 
 
# ── PIPELINE ──
def build_pipeline(progress_callback: Optional[Callable[[str], None]] = None):
 
    def wrap(fn):
        def inner(state):
            result = fn(state)
            if progress_callback:
                progress_callback(result["status"])
            return result
        return inner
 
    graph = StateGraph(ResearchState)
 
    graph.add_node("search", wrap(search_agent))
    graph.add_node("factcheck", lambda s: asyncio.run(parallel_fact_check(s)))
    graph.add_node("summarize", wrap(summarizer_agent))
    graph.add_node("visuals", wrap(visual_data_agent))
    graph.add_node("report", wrap(report_agent))
 
    graph.set_entry_point("search")
    graph.add_edge("search", "factcheck")
    graph.add_edge("factcheck", "summarize")
    graph.add_edge("summarize", "visuals")
    graph.add_edge("visuals", "report")
    graph.add_edge("report", END)
 
    return graph.compile()
 
 
# ── CLI SUPPORT ──
def run_cli(query: str, memory_context: str = ""):
    pipeline = build_pipeline()
 
    initial = {
        "query": query,
        "memory_context": memory_context,
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
 
    return pipeline.invoke(initial)