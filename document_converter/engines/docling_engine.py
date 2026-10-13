import json
import re
from pathlib import Path
from .base import Engine, EngineError
from ..models import ConversionResult, ImageMode

# Docling's Markdown serializer HTML-escapes the document's own text, so a
# document reading "Inbound & Outbound" is exported as "Inbound &amp; Outbound".
# Markdown is not HTML and the plain-text output certainly is not, and the
# document model itself holds the unescaped text - the JSON export proves it -
# so the entities are undone here, at the one place both Docling adapters
# serialize through. The HTML export is left exactly as Docling produced it:
# there the entities belong, and re-escaping an already escaped document would
# be the same mistake in the other direction.
#
# This is the precise inverse of html.escape, applied in one pass, so it undoes
# exactly one level: a document whose own text is "&amp;" is exported by Docling
# as "&amp;amp;" and still reads "&amp;" afterwards.
_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#x27;": "'", "&#39;": "'"}
_ENTITY = re.compile("|".join(map(re.escape, _ENTITIES)))


def unescape_markdown(md: str) -> str:
    """Undo one level of the HTML escaping Docling's Markdown serializer adds."""
    return _ENTITY.sub(lambda match: _ENTITIES[match.group(0)], md or "")

class DoclingEngine(Engine):
    name = "docling"

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        try:
            from docling.document_converter import DocumentConverter
        except Exception as e:
            raise EngineError(f"Docling is not installed: {e}") from e

        try:
            converter = DocumentConverter()
            result = converter.convert(str(path))
            return build_result(result.document, path, self.name, image_mode)
        except Exception as e:
            raise EngineError(f"Docling failed for {path}: {e}") from e

def export_document(doc, image_mode: ImageMode):
    """Serialize a Docling document, using the current serializer API where available."""
    # Use the current Docling serializer API where available.
    if image_mode == "referenced" and hasattr(doc, "export_to_markdown_with_images"):
        md, md_files = doc.export_to_markdown_with_images("referenced", "assets")
        html = None
        assets = {}
        for name, data in md_files:
            assets[str(name)] = data
        if hasattr(doc, "export_to_html_with_images"):
            html, html_files = doc.export_to_html_with_images("referenced", "assets")
            for name, data in html_files:
                assets[str(name)] = data
    elif image_mode == "embedded" and hasattr(doc, "export_to_markdown_with_images"):
        md, _ = doc.export_to_markdown_with_images("embedded", "assets")
        html = doc.export_to_html() if hasattr(doc, "export_to_html") else None
        assets = {}
    else:
        md = doc.export_to_markdown()
        html = doc.export_to_html() if hasattr(doc, "export_to_html") else None
        assets = {}
    return unescape_markdown(md), html, assets

def build_result(doc, path: Path, engine_name: str, image_mode: ImageMode) -> ConversionResult:
    """Turn a Docling document into this project's normalized conversion result."""
    md, html, assets = export_document(doc, image_mode)
    json_text = json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2)
    return ConversionResult(
        source=path,
        engine=engine_name,
        markdown=md,
        html=html,
        json_text=json_text,
        text=_markdown_to_text(md),
        assets=assets,
    )

def _markdown_to_text(md: str) -> str:
    lines = []
    for line in md.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if s.startswith("```"):
            continue
        while s.startswith("#"):
            s = s[1:].lstrip()
        if s.startswith(("- ", "* ", "+ ")):
            s = s[2:]
        lines.append(s)
    return "\n".join(lines).strip() + "\n"
