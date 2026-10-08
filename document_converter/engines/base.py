from pathlib import Path
from ..models import ConversionResult, ImageMode

class EngineError(RuntimeError):
    pass

class Engine:
    name = "base"

    def can_handle(self, path: Path) -> bool:
        return True

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        raise NotImplementedError
