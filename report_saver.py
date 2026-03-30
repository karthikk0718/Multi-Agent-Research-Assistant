# utils/report_saver.py
# Saves final research reports to .md and .pdf files

import os
import re
from datetime import datetime
from fpdf import FPDF

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _safe_filename(query: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", query.lower())
    slug = re.sub(r"\s+", "_", slug).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"research_{slug[:40]}_{timestamp}"


# ── MARKDOWN SAVE ──

def save_markdown(query: str, report: str, fact_check: str) -> str:
    _ensure_output_dir()
    filename = _safe_filename(query) + ".md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    content = f"""# 🔬 Research Report

**Query:** {query}  
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{report}

---

## ✅ Fact-Check Notes

{fact_check}
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


# ── PDF CLASS ──

class _UTF8PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Multi-Agent Research Assistant", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# ── CLEAN TEXT ──

def _clean(text: str) -> str:
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)

    replacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--",
        "\u2022": "*", "\u2026": "...",
        "━": "-"
    }

    for orig, rep in replacements.items():
        text = text.replace(orig, rep)

    text = text.replace("\n\n\n", "\n\n")  # extra safety
    text = text.encode("latin-1", errors="ignore").decode("latin-1")

    return text


# ── PDF SAVE ──

def save_pdf(query: str, report: str, fact_check: str) -> str:
    _ensure_output_dir()
    filename = _safe_filename(query) + ".pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    pdf = _UTF8PDF()
    pdf.add_page()

    # ✅ FIX: margins
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # ── Title ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Research Report", ln=True)

    pdf.ln(4)

    # ── Query & Date ──
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)

    pdf.set_x(10)
    pdf.multi_cell(190, 6, _clean(f"Query: {query}"))

    pdf.set_x(10)
    pdf.multi_cell(190, 6, _clean(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))

    pdf.ln(5)

    # Divider
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── Report Section ──
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)

    for line in _clean(report).split("\n"):
        if line.strip():
            pdf.set_x(10)
            pdf.multi_cell(190, 6, line.strip())
        pdf.ln(1)

    pdf.ln(4)

    # Divider
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # ── Fact Check Section ──
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Fact-Check Notes", ln=True)

    pdf.set_font("Helvetica", "", 10)

    for line in _clean(fact_check).split("\n"):
        if line.strip():
            pdf.set_x(10)
            pdf.multi_cell(190, 6, line.strip())
        pdf.ln(1)

    pdf.output(filepath)

    return filepath