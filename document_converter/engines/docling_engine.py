import json
from pathlib import Path
from .base import Engine, EngineError
from ..models import ConversionResult, ImageMode

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
            doc = result.document

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

            json_text = json.dumps(doc.export_to_dict(), ensure_ascii=False, indent=2)
            text = _markdown_to_text(md)
            return ConversionResult(
                source=path,
                engine=self.name,
                markdown=md,
                html=html,
                json_text=json_text,
                text=text,
                assets=assets,
            )
        except Exception as e:
            raise EngineError(f"Docling failed for {path}: {e}") from e

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
