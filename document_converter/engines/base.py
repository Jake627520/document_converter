from collections.abc import Sequence
from pathlib import Path
from ..models import ConversionResult, ImageMode

class EngineError(RuntimeError):
    def __init__(self, message: str = "", failures: Sequence[BaseException] = ()):
        super().__init__(message)
        # The exceptions behind an aggregate failure, kept as raised so a caller
        # can ask why each engine failed instead of parsing the message.
        self.failures = tuple(failures)

class Engine:
    name = "base"

    def can_handle(self, path: Path) -> bool:
        return True

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        raise NotImplementedError
