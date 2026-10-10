"""Generate the synthetic sample PDFs used for conversion verification.

The PDFs themselves are not committed (the repository .gitignore excludes
``*.pdf`` so real documents cannot be added by accident); run this script to
recreate them byte-for-byte inputs for ``convert_pdfs_native.py``::

    python -I verification/2026-10-10-pdf/make_sample_pdfs.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

OUT = Path(__file__).resolve().parent / "samples"
OUT.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
base = getSampleStyleSheet()
cjk_h1 = ParagraphStyle("cjk_h1", parent=base["Heading1"], fontName="MSung-Light", fontSize=18, leading=24)
cjk_h2 = ParagraphStyle("cjk_h2", parent=base["Heading2"], fontName="MSung-Light", fontSize=14, leading=20)
cjk_body = ParagraphStyle("cjk_body", parent=base["BodyText"], fontName="MSung-Light", fontSize=11, leading=17)


def build_report(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=A4, title="Headlamp Module Spec",
                            author="Product Management", leftMargin=20 * mm, rightMargin=20 * mm)
    flow = [
        Paragraph("車燈模組規格報告 Headlamp Module Spec", cjk_h1),
        Paragraph("1. 專案背景 Background", cjk_h2),
        Paragraph("本文件說明 ADB 矩陣式頭燈模組的量產規格，供 PM 與供應商審閱。"
                  "This document describes the production spec of the ADB matrix headlamp module.", cjk_body),
        Spacer(1, 6 * mm),
        Paragraph("2. 關鍵規格 Key specifications", cjk_h2),
    ]
    data = [
        ["項目 Item", "規格 Spec", "備註 Note"],
        ["光通量 Luminous flux", "1200 lm", "25 degC"],
        ["色溫 Color temperature", "5500 K", "+/- 300 K"],
        ["工作電壓 Voltage", "9 - 16 V", "12 V nominal"],
        ["LED 顆數 LED count", "84", "matrix ADB"],
        ["防水等級 Ingress", "IP6K9K", "ISO 20653"],
    ]
    table = Table(data, colWidths=[55 * mm, 55 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "MSung-Light"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f1")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flow += [table, Spacer(1, 6 * mm)]
    flow += [
        Paragraph("3. 驗證項目 Validation items", cjk_h2),
        Paragraph("3.1 配光測試：依 ECE R149 於暗室量測。Photometry per ECE R149.", cjk_body),
        Paragraph("3.2 熱衝擊：-40 degC 至 85 degC，循環 100 次。Thermal shock, 100 cycles.", cjk_body),
        Paragraph("3.3 振動測試：隨機振動 10 - 2000 Hz。Random vibration 10 - 2000 Hz.", cjk_body),
        PageBreak(),
        Paragraph("4. 時程 Schedule", cjk_h1),
        Paragraph("DV 完成 2026 Q1；PV 完成 2026 Q2；SOP 2026 Q3。"
                  "DV done 2026 Q1, PV done 2026 Q2, SOP 2026 Q3.", cjk_body),
        Paragraph("5. 風險 Risks", cjk_h2),
        Paragraph("供應鏈 LED binning 交期風險；散熱鰭片模具開發風險。"
                  "LED binning lead time risk and heat sink tooling risk.", cjk_body),
    ]
    doc.build(flow)


def build_ascii_memo(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=A4, title="TV Panel Weekly Memo")
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("TV Panel Weekly Memo", styles["Title"]),
        Paragraph("Week 41 - Panel sourcing update", styles["Heading2"]),
        Paragraph("Open-cell prices for 55-inch panels stayed flat week over week. "
                  "Supplier B offered a 2% discount for Q4 volume above 120k units.", styles["BodyText"]),
        Paragraph("Action items", styles["Heading2"]),
        Paragraph("1. Confirm Q4 forecast with demand planning by Friday.", styles["BodyText"]),
        Paragraph("2. Request updated quality data for the new backlight vendor.", styles["BodyText"]),
    ]
    doc.build(flow)


def build_scanned(path: Path) -> None:
    """Image-only PDF: no text layer, mimics a scanned paper document."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1240, 1754), "white")
    draw = ImageDraw.Draw(img)
    font_path = None
    for candidate in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(candidate).exists():
            font_path = candidate
            break
    title_font = ImageFont.truetype(font_path, 54) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
    draw.text((90, 110), "SCANNED INSPECTION SHEET", font=title_font, fill="black")
    lines = [
        "Line: Headlamp assembly L2",
        "Date: 2026-10-09   Shift: A",
        "Sampled units: 50",
        "Defects found: 1 (lens scratch)",
        "Inspector signature: ____________",
    ]
    y = 240
    for line in lines:
        draw.text((90, y), line, font=body_font, fill="black")
        y += 70
    draw.rectangle([80, 90, 1160, y + 40], outline="black", width=3)
    img.save(path, "PDF", resolution=150.0)


build_report(OUT / "headlamp_spec_zh.pdf")
build_ascii_memo(OUT / "tv_panel_memo_en.pdf")
build_scanned(OUT / "scanned_inspection_sheet.pdf")
for p in sorted(OUT.iterdir()):
    print(p.name, p.stat().st_size, "bytes")
