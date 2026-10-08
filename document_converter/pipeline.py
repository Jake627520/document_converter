from pathlib import Path
from .engines.base import EngineError
from .engines.docling_engine import DoclingEngine
from .engines.command_engine import MarkerEngine, MinerUEngine
from .models import ConversionResult, ImageMode
from .detector import inspect_pdf, PdfProfile

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

def choose_engine(name: str, path: Path, profile: PdfProfile | None = None):
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

    # Auto engine selection strategy
    is_pdf = path.suffix.lower() == ".pdf"
    is_image = path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}

    if is_pdf and profile and profile.is_scanned:
        # Scanned PDF without text layer: prioritize engines with dedicated OCR/VLM capabilities
        # Docling first (has internal OCR), then fallbacks
        return [engines["docling"], engines["mineru"], engines["marker"]]
    elif is_pdf or is_image:
        # Standard text-based PDF or image
        return [engines["docling"], engines["marker"], engines["mineru"]]
    else:
        # General documents (Office, HTML, text)
        return [engines["docling"]]

def convert_one(path: Path, engine_name: str, image_mode: ImageMode) -> ConversionResult:
    profile: PdfProfile | None = None
    if path.suffix.lower() == ".pdf":
        try:
            profile = inspect_pdf(path)
        except Exception:
            profile = None

    errors = []
    for engine in choose_engine(engine_name, path, profile=profile):
        try:
            result = engine.convert(path, image_mode)
            if profile:
                result.metadata["pdf_profile"] = profile
                if profile.is_scanned:
                    result.warnings.append(
                        f"Scanned PDF detected ({profile.page_count} pages, {profile.total_chars} text chars). OCR processing applied."
                    )
            return result
        except Exception as e:
            errors.append(f"{engine.name}: {e}")
    raise EngineError("All engines failed:\n" + "\n".join(errors))
