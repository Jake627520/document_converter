from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

OutputFormat = Literal["md", "html", "json", "txt"]
ImageMode = Literal["none", "referenced", "embedded"]

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
