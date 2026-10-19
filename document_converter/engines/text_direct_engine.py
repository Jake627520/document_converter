"""Direct UTF-8 reader for Markdown and plain text — no external engine required."""

from pathlib import Path

from .base import Engine, EngineError
from ..models import ConversionResult, ImageMode
from ..writer import plain_text_of

_TEXT_SUFFIXES = {".md", ".markdown", ".txt"}

# Matches the README promise: refuse Big5 / GBK / UTF-16 rather than mojibake.
_UTF8_REFUSAL = (
    "{name} is not valid UTF-8. Re-save the file as UTF-8 and try again. "
    "Big5, GBK and UTF-16 are not accepted."
)


class TextDirectEngine(Engine):
    name = "text_direct"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _TEXT_SUFFIXES

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        if not self.can_handle(path):
            raise EngineError(f"{self.name} cannot handle {path.suffix}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise EngineError(_UTF8_REFUSAL.format(name=path.name)) from exc
        except OSError as exc:
            raise EngineError(f"Cannot read {path.name}: {exc}") from exc

        return ConversionResult(
            source=path,
            engine=self.name,
            markdown=content,
            text=plain_text_of(content, path.suffix),
        )
