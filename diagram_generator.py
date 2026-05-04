# utils/diagram_generator.py
 
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
 
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
 
 
def generate_architecture_diagram(architecture_data: dict = None) -> str:
    """
    Generates an architecture diagram based on topic-specific data from the LLM.
    architecture_data should contain:
        - title: str
        - components: list of {"name": str, "description": str}
        - flow: list of [from_name, to_name]
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    # ── Fallback if no data ──
    if not architecture_data or not architecture_data.get("components"):
        architecture_data = {
            "title": "System Architecture",
            "components": [
                {"name": "Input Layer", "description": "Receives raw data"},
                {"name": "Processing Module", "description": "Core computation"},
                {"name": "Feature Extractor", "description": "Extracts key features"},
                {"name": "Decision Layer", "description": "Makes predictions"},
                {"name": "Output Layer", "description": "Produces results"},
            ],
            "flow": [
                ["Input Layer", "Processing Module"],
                ["Processing Module", "Feature Extractor"],
                ["Feature Extractor", "Decision Layer"],
                ["Decision Layer", "Output Layer"],
            ]
        }
 
    components = architecture_data.get("components", [])
    flow = architecture_data.get("flow", [])
    title = architecture_data.get("title", "System Architecture")
 
    n = len(components)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#f8f9fa")
    fig.patch.set_facecolor("#f8f9fa")
 
    # ── Position components in a horizontal flow ──
    positions = {}
    margin = 0.08
    spacing = (1.0 - 2 * margin) / max(n - 1, 1)
 
    colors = ["#4A90D9", "#E67E22", "#2ECC71", "#9B59B6", "#E74C3C",
              "#1ABC9C", "#F39C12", "#3498DB", "#E91E63", "#00BCD4"]
 
    for i, comp in enumerate(components):
        x = margin + i * spacing
        y = 0.52
        positions[comp["name"]] = (x, y)
 
        color = colors[i % len(colors)]
 
        # Box
        box = mpatches.FancyBboxPatch(
            (x - 0.07, y - 0.13), 0.14, 0.26,
            boxstyle="round,pad=0.01",
            linewidth=1.5,
            edgecolor=color,
            facecolor=color + "33",  # transparent fill
        )
        ax.add_patch(box)
 
        # Component name
        ax.text(x, y + 0.05, comp["name"], ha="center", va="center",
                fontsize=7.5, fontweight="bold", color="#2c3e50",
                wrap=True, multialignment="center")
 
        # Description
        desc = comp.get("description", "")
        if len(desc) > 30:
            desc = desc[:28] + "…"
        ax.text(x, y - 0.06, desc, ha="center", va="center",
                fontsize=6, color="#555555", style="italic",
                wrap=True, multialignment="center")
 
        # Step number circle
        circle = plt.Circle((x - 0.065, y + 0.1), 0.018, color=color, zorder=5)
        ax.add_patch(circle)
        ax.text(x - 0.065, y + 0.1, str(i + 1), ha="center", va="center",
                fontsize=6.5, fontweight="bold", color="white", zorder=6)
 
    # ── Draw arrows based on flow ──
    drawn = set()
    for edge in flow:
        if len(edge) == 2:
            src, dst = edge[0], edge[1]
            if src in positions and dst in positions and (src, dst) not in drawn:
                x1, y1 = positions[src]
                x2, y2 = positions[dst]
                ax.annotate(
                    "", xy=(x2 - 0.072, y2),
                    xytext=(x1 + 0.072, y1),
                    arrowprops=dict(
                        arrowstyle="->",
                        color="#2c3e50",
                        lw=1.5,
                        connectionstyle="arc3,rad=0.0"
                    )
                )
                drawn.add((src, dst))
 
    ax.set_title(title, fontsize=12, fontweight="bold", color="#2c3e50", pad=15)
 
    path = os.path.join(OUTPUT_DIR, "architecture.png")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
 
    return path
