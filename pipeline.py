# agents/pipeline.py

import asyncio
import os
from typing import TypedDict, List, Callable, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END

load_dotenv()

# ── LLM & Tool setup ──

def _build_llm():
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,
        max_tokens=700
    )


def _build_search():
    return TavilySearchResults(
        max_results=6,
        tavily_api_key=os.getenv("TAVILY_API_KEY", "")
    )


# ── Shared State ──

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


# ── Agents ──

def search_agent(state: ResearchState) -> ResearchState:
    state["status"] = "🔍 Searching the web..."
    search = _build_search()
    results = search.invoke(state["query"])

    state["search_results"] = [r["content"] for r in results if "content" in r]
    state["sources"] = [r.get("url", "N/A") for r in results]

    return state


async def _fact_check_single(llm, claim: str, query: str) -> str:
    prompt = f"""
Check the accuracy of this content for the query: {query}

Give a short verification (1–2 lines).

Content:
{claim}
"""
    response = await llm.ainvoke(prompt)
    return response.content


async def parallel_fact_check(state: ResearchState) -> ResearchState:
    state["status"] = "✅ Fact-checking..."

    llm = _build_llm()

    tasks = [
        _fact_check_single(llm, s, state["query"])
        for s in state["search_results"][:3]
    ]

    results = await asyncio.gather(*tasks)
    state["fact_check_raw"] = list(results)

    return state


def summarizer_agent(state: ResearchState) -> ResearchState:
    state["status"] = "🧠 Summarizing..."

    llm = _build_llm()

    combined = "\n\n".join(state["search_results"][:3])

    prompt = f"""
Summarize the following information clearly.

Provide:
1. Clean paragraph summary
2. Key Points (5 bullet points)

Data:
{combined}
"""

    response = llm.invoke(prompt).content

    if "Key Points" in response:
        parts = response.split("Key Points")
        state["summary"] = parts[0].strip()
        points = parts[1]
    else:
        state["summary"] = response
        points = ""

    # Clean bullet points
    cleaned_points = []
    for p in points.split("\n"):
        p = p.strip("-• ")
        if p:
            cleaned_points.append(f"• {p}")

    state["key_points"] = "\n".join(cleaned_points) if cleaned_points else "Not available"

    return state


def report_agent(state: ResearchState) -> ResearchState:
    state["status"] = "📄 Generating report..."

    llm = _build_llm()

    prompt = f"""
Generate a professional research report.

Follow this structure STRICTLY:

1. Executive Summary
2. Introduction
3. Key Findings
4. Detailed Analysis
5. Advantages and Limitations
6. Use Cases
7. Future Scope
8. Conclusion

Make it:
- Well formatted
- Clear headings
- Easy to read
- Professional

Query: {state['query']}

Summary:
{state['summary']}

Fact-check insights:
{state['fact_check_raw']}
"""

    report = llm.invoke(prompt).content

    # Add section styling
    report = report.replace("Executive Summary", "\n━━━━━━━━━━━━━━\n📌 EXECUTIVE SUMMARY\n━━━━━━━━━━━━━━")
    report = report.replace("Introduction", "\n━━━━━━━━━━━━━━\n📖 INTRODUCTION\n━━━━━━━━━━━━━━")
    report = report.replace("Key Findings", "\n━━━━━━━━━━━━━━\n🔍 KEY FINDINGS\n━━━━━━━━━━━━━━")
    report = report.replace("Detailed Analysis", "\n━━━━━━━━━━━━━━\n📊 DETAILED ANALYSIS\n━━━━━━━━━━━━━━")
    report = report.replace("Advantages", "\n━━━━━━━━━━━━━━\n⚖️ ADVANTAGES & LIMITATIONS\n━━━━━━━━━━━━━━")
    report = report.replace("Conclusion", "\n━━━━━━━━━━━━━━\n📌 CONCLUSION\n━━━━━━━━━━━━━━")

    # Append sources
    sources_text = "\n\n━━━━━━━━━━━━━━\n🔗 SOURCES\n━━━━━━━━━━━━━━\n"
    sources_text += "\n".join(state["sources"])

    report += sources_text

    state["final_report"] = report

    # Confidence score
    count = len(state["search_results"])
    if count >= 5:
        state["confidence"] = "High"
    elif count >= 3:
        state["confidence"] = "Medium"
    else:
        state["confidence"] = "Low"

    state["fact_check"] = "\n\n".join(state["fact_check_raw"])
    state["status"] = "✅ Done!"

    return state


# ── Pipeline ──

def build_pipeline(progress_callback: Optional[Callable[[str], None]] = None):

    def _wrap(fn):
        def wrapped(state):
            result = fn(state)
            if progress_callback and "status" in result:
                progress_callback(result["status"])
            return result
        return wrapped

    graph = StateGraph(ResearchState)

    graph.add_node("search", _wrap(search_agent))
    graph.add_node("factcheck", lambda s: asyncio.run(parallel_fact_check(s)))
    graph.add_node("summarize", _wrap(summarizer_agent))
    graph.add_node("report", _wrap(report_agent))

    graph.set_entry_point("search")
    graph.add_edge("search", "factcheck")
    graph.add_edge("factcheck", "summarize")
    graph.add_edge("summarize", "report")
    graph.add_edge("report", END)

    return graph.compile()


# ── CLI Support ──

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
        "status": "Starting..."
    }

    return pipeline.invoke(initial)
