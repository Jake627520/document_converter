"""A page of text drawn with an installed font, for the tests that run real OCR.

Drawing it at test time needs no fixture files, and checks what a user would
get: a photo or a scanned page read back as text.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Fonts with Chinese glyphs: those macOS installs with the system, then the
# WenQuanYi font the Linux CI job installs.
FONTS = (
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
)

ENGLISH = "Quarterly revenue grew"
CHINESE = "營收成長百分之十二"


def font(size):
    for candidate in FONTS:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    raise AssertionError(f"none of these fonts is installed: {FONTS}")


def page(width=1700, height=2200):
    """A white page with one English and one Chinese paragraph, well apart."""
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((150, 200), ENGLISH, fill="black", font=font(72))
    draw.text((150, 600), CHINESE, fill="black", font=font(72))
    return image


def squeezed(text):
    return "".join((text or "").split())
