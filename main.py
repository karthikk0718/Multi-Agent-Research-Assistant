#!/usr/bin/env python3
# main.py  —  CLI entry point for the research pipeline

import sys
from agents.pipeline import run_cli
from utils.report_saver import save_markdown, save_pdf
from utils.memory import ResearchMemory

def main():
    memory = ResearchMemory()

    print("\n🔬 Multi-Agent Research Assistant (CLI)")
    print("=" * 50)
    print("Type 'quit' to exit.\n")

    while True:
        query = input("📌 Research query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not query:
            continue

        print()
        memory_context = memory.get_context()
        result = run_cli(query, memory_context=memory_context)

        # Save to memory for follow-ups
        memory.add_interaction(query, result["summary"])

        # Save files
        md_path  = save_markdown(query, result["final_report"], result["fact_check"])
        pdf_path = save_pdf(query, result["final_report"], result["fact_check"])

        print("\n" + "=" * 60)
        print("📋 FINAL REPORT")
        print("=" * 60)
        print(result["final_report"])
        print()
        print(f"💾 Saved → {md_path}")
        print(f"💾 Saved → {pdf_path}")
        print()

if __name__ == "__main__":
    main()
