# utils/memory.py
from typing import List, Dict

class ResearchMemory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    @property
    def has_history(self) -> bool:
        return len(self.history) > 0

    def add_interaction(self, query: str, summary: str):
        """Store a query + its research summary."""
        self.history.append({
            "query": query,
            "summary": summary
        })

    def get_context(self) -> str:
        """Return last 3 interactions as context."""
        if not self.history:
            return ""

        lines = ["=== Previous Research Context ==="]
        for i, item in enumerate(self.history[-3:], 1):
            lines.append(f"\n[Session {i}]")
            lines.append(f"Query:   {item['query']}")
            lines.append(f"Summary: {item['summary'][:300]}...")
        lines.append("=================================\n")

        return "\n".join(lines)

    def clear(self):
        """Clear memory."""
        self.history = []
