# utils/report_saver.py
 
import os
import re
from datetime import datetime
 
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
 
from utils.diagram_generator import generate_architecture_diagram
from utils.graph_generator import generate_performance_graph, generate_ablation_graph
 
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
 
 
# ── UTILS ──
def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
 
def _safe_filename(query: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", (query or "research").lower())
    slug = re.sub(r"\s+", "_", slug).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"research_{slug[:40]}_{timestamp}"
 
 
def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = text.replace("<", "").replace(">", "")
    return text
 
 
# ── MARKDOWN SAVE ──
def save_markdown(query: str, report: str, fact_check: str) -> str:
    _ensure_output_dir()
 
    filename = _safe_filename(query) + ".md"
    filepath = os.path.join(OUTPUT_DIR, filename)
 
    content = f"""# Research Paper: {query}
 
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 
---
 
{report or ""}
 
---
 
## Fact Check
 
{fact_check or ""}
"""
 
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
 
    return filepath
 
 
# ── PDF SAVE ──
def save_pdf(
    query: str,
    report: str,
    fact_check: str,
    architecture_data: dict = None,
    ablation_data: dict = None,
    performance_data: dict = None,
) -> str:
    _ensure_output_dir()
 
    # ── Generate topic-specific visuals ──
    diagram_path = generate_architecture_diagram(architecture_data)
    perf_path = generate_performance_graph(performance_data)
    ablation_path = generate_ablation_graph(ablation_data)
 
    filename = _safe_filename(query) + ".pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
 
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.9 * inch,
        bottomMargin=1 * inch,
    )
 
    # ── STYLES ──
    title_style = ParagraphStyle(
        name="Title",
        fontName="Times-Bold",
        fontSize=22,
        alignment=1,
        spaceAfter=10,
        leading=28,
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        fontName="Times-Roman",
        fontSize=11,
        alignment=1,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        name="Heading",
        fontName="Times-Bold",
        fontSize=12,
        spaceBefore=16,
        spaceAfter=6,
        textColor=colors.HexColor("#1a237e"),
    )
    body_style = ParagraphStyle(
        name="Body",
        fontName="Times-Roman",
        fontSize=10,
        leading=16,
        spaceAfter=8,
        alignment=4,  # justified
    )
    caption_style = ParagraphStyle(
        name="Caption",
        fontName="Times-Roman",
        fontSize=9,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor("#555555"),
    )
    code_style = ParagraphStyle(
        name="Code",
        fontName="Courier",
        fontSize=8.5,
        leading=13,
        spaceAfter=6,
        leftIndent=20,
        backColor=colors.HexColor("#f5f5f5"),
    )
 
    elements = []
 
    # ── TITLE ──
    paper_title = query.title() if len(query) < 80 else query[:80].title() + "..."
    elements.append(Paragraph(paper_title, title_style))
    elements.append(Paragraph("A Multi-Agent AI Research Paper", subtitle_style))
    elements.append(Spacer(1, 6))
 
    # ── HORIZONTAL RULE (thin table) ──
    hr = Table([[""]],
               colWidths=[doc.width],
               style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#1a237e"))]))
    elements.append(hr)
    elements.append(Spacer(1, 8))
 
    # ── REPORT BODY ──
    # Parse the report text into sections with headings
    report_text = _clean(report or "")
    lines = report_text.split("\n")
 
    figure_counter = [0]  # mutable counter
 
    i = 0
    arch_inserted = False
    ablation_inserted = False
    perf_inserted = False
 
    while i < len(lines):
        line = lines[i].strip()
 
        if not line:
            i += 1
            continue
 
        # Detect section headings (numbered or ALL CAPS keywords)
        is_heading = (
            re.match(r"^\d+[\.\)]\s+[A-Z]", line) or
            re.match(r"^(Abstract|Keywords|Introduction|Related Work|Methodology|Algorithm|"
                     r"Mathematical|Architecture|Ablation|Performance|Results|Discussion|"
                     r"Conclusion|References)", line, re.IGNORECASE)
        )
 
        if is_heading:
            elements.append(Paragraph(line, heading_style))
 
            # ── Inject architecture diagram after Architecture section heading ──
            lower = line.lower()
            if "architecture" in lower and not arch_inserted and os.path.exists(diagram_path):
                figure_counter[0] += 1
                elements.append(Spacer(1, 6))
                elements.append(Image(diagram_path, width=440, height=210))
                arch_label = architecture_data.get("title", "System Architecture") if architecture_data else "System Architecture"
                elements.append(Paragraph(
                    f"Figure {figure_counter[0]}: {arch_label}", caption_style))
                arch_inserted = True
 
            # ── Inject ablation graph after Ablation section heading ──
            elif "ablation" in lower and not ablation_inserted:
                # Ablation table
                if ablation_data and ablation_data.get("variants"):
                    figure_counter[0] += 1
                    metric = ablation_data.get("metric_name", "Score (%)")
                    table_data = [[Paragraph("Model Variant", ParagraphStyle("th", fontName="Times-Bold", fontSize=9)),
                                   Paragraph(metric, ParagraphStyle("th", fontName="Times-Bold", fontSize=9))]]
                    for v in ablation_data["variants"]:
                        table_data.append([
                            Paragraph(str(v["label"]), ParagraphStyle("td", fontName="Times-Roman", fontSize=9)),
                            Paragraph(str(v["score"]), ParagraphStyle("td", fontName="Times-Roman", fontSize=9))
                        ])
                    tbl = Table(table_data, colWidths=[300, 140])
                    tbl.setStyle(TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#aaaaaa")),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaf6")),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(Spacer(1, 6))
                    elements.append(tbl)
                    ablation_label = ablation_data.get("title", "Ablation Study")
                    elements.append(Paragraph(
                        f"Table {figure_counter[0]}: {ablation_label}", caption_style))
 
                # Ablation bar chart
                if os.path.exists(ablation_path):
                    figure_counter[0] += 1
                    elements.append(Spacer(1, 4))
                    elements.append(Image(ablation_path, width=440, height=210))
                    elements.append(Paragraph(
                        f"Figure {figure_counter[0]}: Ablation Study — Impact of Each Component",
                        caption_style))
                ablation_inserted = True
 
            # ── Inject performance graph after Performance section heading ──
            elif "performance" in lower and not perf_inserted and os.path.exists(perf_path):
                figure_counter[0] += 1
                elements.append(Spacer(1, 6))
                elements.append(Image(perf_path, width=440, height=210))
                perf_label = performance_data.get("title", "Performance Graph") if performance_data else "Performance Graph"
                elements.append(Paragraph(
                    f"Figure {figure_counter[0]}: {perf_label}", caption_style))
                perf_inserted = True
 
        else:
            elements.append(Paragraph(line, body_style))
 
        i += 1
 
    # ── Insert any visuals not yet placed (fallback) ──
    if not arch_inserted and os.path.exists(diagram_path):
        figure_counter[0] += 1
        elements.append(Paragraph("Architecture Diagram", heading_style))
        elements.append(Image(diagram_path, width=440, height=210))
        arch_label = architecture_data.get("title", "System Architecture") if architecture_data else "System Architecture"
        elements.append(Paragraph(f"Figure {figure_counter[0]}: {arch_label}", caption_style))
 
    if not ablation_inserted and os.path.exists(ablation_path):
        figure_counter[0] += 1
        elements.append(Paragraph("Ablation Study", heading_style))
        elements.append(Image(ablation_path, width=440, height=210))
        elements.append(Paragraph(f"Figure {figure_counter[0]}: Ablation Study", caption_style))
 
    if not perf_inserted and os.path.exists(perf_path):
        figure_counter[0] += 1
        elements.append(Paragraph("Performance Graph", heading_style))
        elements.append(Image(perf_path, width=440, height=210))
        perf_label = performance_data.get("title", "Performance Graph") if performance_data else "Performance Graph"
        elements.append(Paragraph(f"Figure {figure_counter[0]}: {perf_label}", caption_style))
 
    # ── FACT CHECK SECTION ──
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Fact Check Notes", heading_style))
    elements.append(Paragraph(_clean(fact_check or "Not available"), body_style))
 
    # ── BUILD PDF ──
    doc.build(elements)
 
    return filepath