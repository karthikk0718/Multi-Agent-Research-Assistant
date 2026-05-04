#!/usr/bin/env python3
# main.py — CLI entry point for the research pipeline
 
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
        try:
            query = input("📌 Research topic: ").strip()
 
            if query.lower() in ("quit", "exit", "q"):
                print("👋 Goodbye!")
                break
 
            if not query:
                print("⚠️ Please enter a valid topic.\n")
                continue
 
            print("\n⏳ Processing...\n")
 
            memory_context = memory.get_context()
            result = run_cli(query, memory_context=memory_context)
 
            memory.add_interaction(query, result.get("summary", ""))
 
            # Save files with topic-specific visual data
            md_path = save_markdown(query, result["final_report"], result["fact_check"])
            pdf_path = save_pdf(
                query,
                result["final_report"],
                result["fact_check"],
                architecture_data=result.get("architecture_data"),
                ablation_data=result.get("ablation_data"),
                performance_data=result.get("performance_data"),
            )
 
            print("\n" + "=" * 60)
            print("📋 FINAL REPORT")
            print("=" * 60)
            print(result.get("final_report", "No report generated."))
 
            print("\n📌 KEY POINTS:")
            print(result.get("key_points", "Not available"))
 
            print("\n📊 CONFIDENCE:")
            print(result.get("confidence", "Unknown"))
 
            print("\n💾 FILES SAVED:")
            print(f"📄 Markdown → {md_path}")
            print(f"📕 PDF      → {pdf_path}")
            print("=" * 60 + "\n")
 
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
 
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("👉 Check your API keys or internet connection.\n")
 
 
if __name__ == "__main__":
    main()