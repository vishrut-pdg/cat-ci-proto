from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


NAVY = colors.HexColor("#0B2F50")
BLUE = colors.HexColor("#0968D2")
YELLOW = colors.HexColor("#FFCD11")
SLATE = colors.HexColor("#536A82")
LIGHT = colors.HexColor("#EEF3F8")


def _money(value) -> str:
    amount = float(value or 0)
    if abs(amount) >= 1_000_000:
        return f"USD {amount / 1_000_000:.1f}M"
    if abs(amount) >= 1_000:
        return f"USD {amount / 1_000:.1f}K"
    return f"USD {amount:,.0f}"


def _clean(value: str) -> str:
    return value.translate(str.maketrans({"\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}))


def _page(canvas, document):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 18 * mm, A4[0], 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(YELLOW)
    canvas.rect(16 * mm, A4[1] - 13 * mm, 17 * mm, 2 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(16 * mm, A4[1] - 10 * mm, "CAT COST INTELLIGENCE")
    canvas.setFillColor(colors.HexColor("#718097"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(16 * mm, 10 * mm, "Executive Guidance - confidential demo")
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_executive_report_pdf(context: dict, narrative: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm,
        topMargin=27 * mm, bottomMargin=17 * mm,
        title=f"Executive Cost Intelligence Report {context['period']}",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], textColor=NAVY, fontSize=23, leading=28, spaceAfter=5)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=SLATE, fontSize=9, leading=13, spaceAfter=14)
    heading = ParagraphStyle("Heading", parent=styles["Heading2"], textColor=NAVY, fontSize=14, leading=18, spaceBefore=10, spaceAfter=7)
    body = ParagraphStyle("Body", parent=styles["BodyText"], textColor=colors.HexColor("#314967"), fontSize=9, leading=14, spaceAfter=6)
    small = ParagraphStyle("Small", parent=body, fontSize=7.5, leading=10)
    right = ParagraphStyle("Right", parent=small, alignment=TA_RIGHT)

    summary = context["summary"]
    story = [
        Paragraph(
            f"{escape(context['top_products'][0]['product_name'])} cost intelligence report"
            if context.get("product_id") and context.get("top_products")
            else "Executive cost intelligence report",
            title,
        ),
        Paragraph(
            f"{escape(context['period'])} | "
            f"{escape(context.get('product_id') or context['scope']).title()} scope | "
            f"Data as of {context['as_of_date']}", subtitle,
        ),
    ]
    metric_data = [[
        Paragraph("<b>Validated opportunity</b>", small),
        Paragraph("<b>Current opportunities</b>", small),
        Paragraph("<b>Top product</b>", small),
        Paragraph("<b>Top plant</b>", small),
    ], [
        Paragraph(f"<b>{_money(summary['total_potential_savings'])}</b>", body),
        Paragraph(f"<b>{summary['opportunity_count']}</b>", body),
        Paragraph(escape(summary["top_product"]["name"] if summary["top_product"] else "Not available"), body),
        Paragraph(escape(summary["top_plant"]["name"] if summary["top_plant"] else "Not available"), body),
    ]]
    metrics = Table(metric_data, colWidths=[44 * mm] * 4, rowHeights=[10 * mm, 15 * mm])
    metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#D7E2ED")),
        ("INNERGRID", (0, 0), (-1, -1), .5, colors.HexColor("#D7E2ED")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([metrics, Spacer(1, 8 * mm), Paragraph("AI-grounded executive narrative", heading)])
    for line in _clean(narrative).splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("##"):
            story.append(Paragraph(escape(clean.lstrip("# ")), heading))
        elif clean.startswith("- "):
            story.append(Paragraph(f"&bull; {escape(clean[2:])}", body))
        else:
            story.append(Paragraph(escape(clean.replace("**", "")), body))

    story.extend([PageBreak(), Paragraph("Portfolio priorities", title), Paragraph("Backend-ranked measures; AI does not calculate these values.", subtitle)])
    priority_rows = [["Dimension", "Leader", "Potential savings", "Variance"]]
    for label, key in (("Plant", "top_plant"), ("Product", "top_product"), ("Category", "top_category"), ("Component", "top_component")):
        item = summary.get(key)
        priority_rows.append([label, item["name"] if item else "Not available", _money(item["potential_savings"] if item else 0), f"{float(item['variance_percent']):.1f}%" if item else "-"])
    priorities = Table(priority_rows, colWidths=[31 * mm, 70 * mm, 43 * mm, 32 * mm], repeatRows=1)
    priorities.setStyle(_table_style())
    story.extend([priorities, Spacer(1, 8 * mm), Paragraph("Recommended quick wins", heading)])
    win_rows = [["Rank", "Opportunity", "Savings", "Confidence", "Why now"]]
    for item in context["quick_wins"][:5]:
        win_rows.append([str(item["rank"]), Paragraph(escape(item["title"]), small), _money(item["potential_savings"]), f"{float(item['confidence']) * 100:.0f}%", Paragraph(escape(item["why_now"]), small)])
    wins = Table(win_rows, colWidths=[13 * mm, 51 * mm, 29 * mm, 25 * mm, 58 * mm], repeatRows=1)
    wins.setStyle(_table_style())
    story.extend([wins, Spacer(1, 8 * mm), Paragraph("Leading products", heading)])
    product_rows = [["Product", "Opportunity", "Variance", "Plants"]]
    for item in context["top_products"][:6]:
        product_rows.append([Paragraph(escape(item["product_name"]), small), _money(item["potential_savings"]), f"{float(item['variance_percent']):.1f}%", f"{item['lowest_cost_plant']} / {item['highest_cost_plant']}"])
    products = Table(product_rows, colWidths=[61 * mm, 35 * mm, 25 * mm, 55 * mm], repeatRows=1)
    products.setStyle(_table_style())
    story.append(products)
    document.build(story, onFirstPage=_page, onLaterPages=_page)
    return buffer.getvalue()


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#314967")),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D7E2ED")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])
