from pathlib import Path
from .engines.base import EngineError
from .engines.docling_engine import DoclingEngine
from .engines.command_engine import MarkerEngine, MinerUEngine
from .models import ConversionResult, ImageMode

SUPPORTED = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".epub", ".md", ".markdown", ".txt",
    ".png", ".jpg", ".jpeg", ".webp", ".csv", ".rtf", ".odt", ".ods", ".odp"
}

def discover_inputs(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(
            p for p in source.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED
        )
    raise FileNotFoundError(source)

def choose_engine(name: str, path: Path):
    engines = {
        "docling": DoclingEngine(),
        "marker": MarkerEngine(),
        "mineru": MinerUEngine(),
    }
    if name != "auto":
        engine = engines[name]
        if not engine.can_handle(path):
            raise EngineError(f"{name} cannot handle {path.suffix}")
        return [engine]
    # General parser first; specialist fallbacks for difficult PDF/image cases.
    result = [engines["docling"]]
    if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        result += [engines["marker"], engines["mineru"]]
    return result

def convert_one(path: Path, engine_name: str, image_mode: ImageMode) -> ConversionResult:
    errors = []
    for engine in choose_engine(engine_name, path):
        try:
            return engine.convert(path, image_mode)
        except Exception as e:
            errors.append(f"{engine.name}: {e}")
    raise EngineError("All engines failed:\n" + "\n".join(errors))
