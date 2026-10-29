import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

OutputFormat = Literal["md", "html", "json", "txt"]
ImageMode = Literal["none", "referenced", "embedded"]

# An engine marks a picture it could not read as an HTML comment, so a page of
# those is not recovered text, however many bytes it occupies.
_PLACEHOLDER = re.compile(r"<!--.*?-->", re.DOTALL)

@dataclass
class ConversionResult:
    source: Path
    engine: str
    markdown: str | None = None
    html: str | None = None
    json_text: str | None = None
    text: str | None = None
    assets: dict[str, bytes] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def has_recovered_text(self) -> bool:
        """Did this conversion recover any text at all?

        Asked of the result rather than of an engine, because every engine can
        return a document with nothing in it - a scan with no text layer, a
        page that is one picture, an empty input - and the caller's duty is the
        same each time: say so, rather than hand over an empty file.
        """
        return bool(_PLACEHOLDER.sub("", self.markdown or "").strip())


def no_text_recovered_message(result: ConversionResult) -> str:
    """Explain why no output file was written (CLI / shared policy)."""
    source = getattr(result, "source", None)
    name = getattr(source, "name", str(source)) if source else "file"
    engine = getattr(result, "engine", None) or "unknown"
    # text_direct / plain text inputs: empty or whitespace only
    if engine == "text_direct":
        return (
            f"{name}: no text recovered. The file is empty or contains only whitespace. "
            "No output file was written."
        )
    return (
        f"{name}: no text recovered (engine: {engine}). "
        "The file may be a scan or photo with no text layer, image-only pages, or empty. "
        "No output file was written. A scanned PDF needs an OCR-capable engine; this project ships none. "
        "Marker or MinerU can be installed separately, under their own terms; "
        "`document-converter list-engines` shows what is installed."
    )
