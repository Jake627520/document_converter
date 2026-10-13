"""Build varied test documents, each aimed at a defect this project fixed."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)
from PIL import Image as PILImage, ImageDraw

OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
ss = getSampleStyleSheet()
zh = ParagraphStyle("zh", parent=ss["BodyText"], fontName="STSong-Light", fontSize=10, leading=15)
zh_h = ParagraphStyle("zhh", parent=ss["Heading1"], fontName="STSong-Light", fontSize=15, leading=20)

def build(name, story, **kw):
    path = OUT / name
    SimpleDocTemplate(str(path), pagesize=A4, title=name, **kw).build(story)
    print(f"  {name:34} {path.stat().st_size:>7} bytes")
    return path

# 1. Spec sheet: table values, bare numerals, ampersands, angle brackets.
rows = [["項目 Item", "規格 Spec", "數量 Qty", "備註"],
        ["LED 顆數", "84", "84", "A & B 供應商"],
        ["色溫", "5500 K", "12", "公差 < 300 K"],
        ["功率", "35 W", "6", "P > 30 W 需散熱"],
        ["壽命", "50000 hr", "1", "AEC-Q102 & IATF"]]
t = Table(rows, colWidths=[38*mm, 38*mm, 22*mm, 48*mm])
t.setStyle(TableStyle([("FONTNAME", (0,0), (-1,-1), "STSong-Light"),
                       ("FONTSIZE", (0,0), (-1,-1), 9),
                       ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
                       ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#eeeeee"))]))
build("01-spec-table-zh.pdf", [
    Paragraph("車燈模組規格 Headlamp Spec", zh_h), Spacer(1, 6*mm), t, Spacer(1, 6*mm),
    Paragraph("備註：本表數值為假資料，僅供轉檔驗證。R&D 與 QA 共同確認。", zh),
    Paragraph("84", zh),          # a bare numeral on its own line, like a table value
    Paragraph("Page 1 of 2", zh),  # a labelled page marker
])

# 2. Long wrapped paragraphs: the fragmentation the resume showed.
long_zh = ("本段刻意寫得很長，用來檢查轉檔後同一個段落是否被拆成許多行。"
           "物流資訊系統在巴西、泰國與阿根廷的導入，涵蓋需求訪談、差異分析、"
           "方案評估、使用者驗收測試、上線切換與上線後的問題追蹤，"
           "每個階段都需要與當地團隊、IT 與外部物流夥伴協同。") * 2
build("02-long-paragraphs-zh.pdf", [
    Paragraph("段落換行測試", zh_h), Spacer(1, 4*mm),
    Paragraph(long_zh, zh), Spacer(1, 4*mm), Paragraph(long_zh, zh),
])

# 3. Multi-page with page numbers in several shapes.
story = []
for page in range(1, 4):
    story += [Paragraph(f"第 {page} 章 Chapter {page}", zh_h), Spacer(1, 4*mm),
              Paragraph(f"本頁內容。數值 {page * 17} 必須保留。", zh), Spacer(1, 30*mm),
              Paragraph(f"Page {page} of 3", zh), Paragraph(f"- {page} -", zh),
              Paragraph(f"{page}", zh)]
    if page < 3:
        story.append(PageBreak())
build("03-multipage-pagenumbers.pdf", story)

# 4. An image with no text at all - the question asked.
img = PILImage.new("RGB", (900, 560), "white")
d = ImageDraw.Draw(img)
d.rectangle([60, 60, 840, 500], outline="black", width=4)
d.line([60, 280, 840, 280], fill="black", width=3)
d.ellipse([320, 120, 580, 240], outline="black", width=3)
for x in range(120, 800, 90):
    d.line([x, 320, x, 460], fill="black", width=2)
photo = OUT / "04-drawing-no-text.png"
img.save(photo)
print(f"  {photo.name:34} {photo.stat().st_size:>7} bytes  (PNG, no text)")

build("05-image-only-no-text.pdf", [Image(str(photo), width=165*mm, height=103*mm)])

# 6. Image plus a caption: some text, mostly picture.
build("06-image-with-caption.pdf", [
    Paragraph("圖 1：配光曲線示意", zh), Spacer(1, 3*mm),
    Image(str(photo), width=150*mm, height=94*mm), Spacer(1, 3*mm),
    Paragraph("資料來源：內部量測 & 模擬，誤差 < 5%。", zh),
])

# 7. Entities and punctuation that an HTML-escaping serializer mangles.
build("07-entities-and-quotes.pdf", [
    Paragraph("Entities &amp; punctuation", ss["Heading1"]), Spacer(1, 4*mm),
    Paragraph("Inbound &amp; Outbound, 5 &lt; 6, 7 &gt; 6, he said &quot;ready&quot;.", ss["BodyText"]),
    Paragraph("Tags like &lt;div&gt; and a path C:\\Users\\x must survive.", ss["BodyText"]),
])
print("\nsamples in", OUT)
