# utils/graph_generator.py
 
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
 
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
 
 
def generate_performance_graph(performance_data: dict = None) -> str:
    """
    Generates a performance graph from topic-specific LLM-generated data.
    performance_data should contain:
        - title: str
        - x_label: str
        - y_label: str
        - x_values: list of numbers
        - y_values: list of numbers
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    # ── Fallback ──
    if not performance_data or not performance_data.get("x_values"):
        performance_data = {
            "title": "Performance vs Training Iterations",
            "x_label": "Iterations",
            "y_label": "Performance (%)",
            "x_values": [1, 2, 3, 4, 5, 6, 7, 8],
            "y_values": [55, 63, 70, 76, 82, 86, 89, 92],
        }
 
    x = performance_data.get("x_values", [])
    y = performance_data.get("y_values", [])
    title = performance_data.get("title", "Performance Graph")
    x_label = performance_data.get("x_label", "X")
    y_label = performance_data.get("y_label", "Y")
 
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#ffffff")
 
    ax.plot(x, y, marker="o", color="#4A90D9", linewidth=2.5,
            markersize=8, markerfacecolor="#E67E22", markeredgecolor="#ffffff",
            markeredgewidth=1.5, label=y_label, zorder=3)
 
    # Shaded area under curve
    ax.fill_between(x, y, alpha=0.12, color="#4A90D9")
 
    # Annotate each point
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi}", (xi, yi), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=8, color="#2c3e50")
 
    ax.set_xlabel(x_label, fontsize=10, color="#2c3e50")
    ax.set_ylabel(y_label, fontsize=10, color="#2c3e50")
    ax.set_title(title, fontsize=12, fontweight="bold", color="#2c3e50", pad=12)
    ax.grid(True, linestyle="--", alpha=0.5, color="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=9)
 
    filepath = os.path.join(OUTPUT_DIR, "performance_graph.png")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
 
    return filepath
 
 
def generate_ablation_graph(ablation_data: dict = None) -> str:
    """
    Generates an ablation study bar chart from topic-specific LLM-generated data.
    ablation_data should contain:
        - title: str
        - metric_name: str
        - variants: list of {"label": str, "score": float}
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    # ── Fallback ──
    if not ablation_data or not ablation_data.get("variants"):
        ablation_data = {
            "title": "Ablation Study",
            "metric_name": "Performance (%)",
            "variants": [
                {"label": "Full Model", "score": 91.5},
                {"label": "w/o Component A", "score": 78.0},
                {"label": "w/o Component B", "score": 82.3},
                {"label": "w/o Component C", "score": 74.1},
                {"label": "Baseline", "score": 65.0},
            ]
        }
 
    variants = ablation_data.get("variants", [])
    title = ablation_data.get("title", "Ablation Study")
    metric = ablation_data.get("metric_name", "Score")
 
    labels = [v["label"] for v in variants]
    scores = [v["score"] for v in variants]
 
    # Color: highest bar is green, others are blue shades
    max_score = max(scores)
    bar_colors = ["#2ECC71" if s == max_score else "#4A90D9" for s in scores]
 
    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#ffffff")
 
    bars = ax.bar(labels, scores, color=bar_colors, edgecolor="white",
                  linewidth=1.2, width=0.55, zorder=3)
 
    # Value labels on bars
    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{score:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#2c3e50")
 
    ax.set_ylabel(metric, fontsize=10, color="#2c3e50")
    ax.set_title(title, fontsize=12, fontweight="bold", color="#2c3e50", pad=12)
    ax.set_ylim(0, max(scores) * 1.18)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5, color="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
 
    # Wrap long labels
    wrapped = []
    for lbl in labels:
        if len(lbl) > 18:
            words = lbl.split()
            mid = len(words) // 2
            lbl = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        wrapped.append(lbl)
    ax.set_xticklabels(wrapped, fontsize=8.5, color="#2c3e50")
 
    filepath = os.path.join(OUTPUT_DIR, "ablation_graph.png")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
 
    return filepath