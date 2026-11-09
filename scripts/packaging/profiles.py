"""Reviewed local release profiles for the macOS candidate build.

``text`` is the original audited candidate: Markdown and UTF-8 text only, with no
engine code frozen into the app. Its excluded and forbidden module lists are kept
exactly as they were reviewed, so a profile-aware build cannot weaken it.

``pdf`` additionally accepts PDFs that already carry a text layer, converted by
Docling's model-free reader, so the app contains no deep-learning runtime and
downloads no model weights. It drops only the entries that would block the
model-free engine, and keeps every other restriction.

``office-ocr`` additionally accepts Word, PowerPoint and Excel through Docling's
readers, and scanned PDFs and images through the OCR macOS ships (Apple's Vision
framework, reached through PyObjC). It still bundles no model and no
deep-learning runtime: the recognizer is part of the operating system.

All profiles share the launcher, the FastAPI app, the request limits and the
writer. They differ in what the build may freeze, which Python distributions are
pinned, and the source files recorded in the manifest.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SHARED_SOURCES = [
    "web_app.py",
    "web_security.py",
    "formats.py",
    "writer.py",
    "renderer.py",
    "models.py",
    "cleaner.py",
    "__init__.py",
]

UVICORN_HIDDEN = [
    "uvicorn.logging",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan.off",
]

# The reviewed text-only exclusion list, unchanged. The first fifteen entries are
# also rejected if they turn up in the frozen inventory.
TEXT_EXCLUDES = [
    "document_converter.pipeline",
    "document_converter.detector",
    "document_converter.engines",
    "document_converter.cli",
    "fitz",
    "pymupdf",
    "docling",
    "marker",
    "magic_pdf",
    "mineru",
    "torch",
    "pytest",
    "httpx",
    "pip",
    "setuptools",
    "tkinter",
    "uvloop",
    "httptools",
    "websockets",
    "watchfiles",
]

# Same list, minus the three entries the model-free PDF engine needs, plus the
# model runtimes that must stay out of this profile too.
PDF_EXCLUDES = [
    "document_converter.pipeline",
    "document_converter.detector",
    "document_converter.cli",
    "fitz",
    "pymupdf",
    "marker",
    "magic_pdf",
    "mineru",
    "torch",
    "torchvision",
    "transformers",
    "accelerate",
    "pytest",
    "httpx",
    "pip",
    "setuptools",
    "tkinter",
    "uvloop",
    "httptools",
    "websockets",
    "watchfiles",
]


@dataclass(frozen=True)
class Profile:
    """Everything the build and the audit need to know about one release."""

    name: str
    manifest_profile: str
    requirements_stem: str
    bundle_identifier: str
    candidate_name: str
    excludes: list[str]
    forbidden: list[str]
    forbidden_distributions: set[str]
    hidden_imports: list[str] = field(default_factory=list)
    collect_all: list[str] = field(default_factory=list)
    copy_metadata: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=lambda: list(SHARED_SOURCES))
    candidate_notice: str = ""


TEXT = Profile(
    name="text",
    manifest_profile="text-only",
    requirements_stem="requirements-macos-arm64",
    bundle_identifier="local.documentconverter.text",
    candidate_name="Document-Converter-macos-arm64-local-candidate",
    excludes=list(TEXT_EXCLUDES),
    forbidden=list(TEXT_EXCLUDES[:15]),
    forbidden_distributions={
        "pymupdf",
        "fitz",
        "docling",
        "docling-slim",
        "marker-pdf",
        "magic-pdf",
        "mineru",
        "torch",
        "pytest",
        "pytest-cov",
        "pip",
        "pip-audit",
        "pip-licenses",
        "httpx",
    },
    hidden_imports=list(UVICORN_HIDDEN),
    candidate_notice=(
        "Local test candidate only. Markdown and UTF-8 text to Markdown/HTML.\n"
        "Apple Silicon macOS only; no PDF/OCR/Office engines or models.\n"
        "No Developer ID signing or notarization; no distribution approval.\n"
        "Closing the browser does not stop the app; quit Document Converter in Activity Monitor.\n"
    ),
)

PDF = Profile(
    name="pdf",
    manifest_profile="pdf-text",
    requirements_stem="requirements-macos-arm64-pdf",
    bundle_identifier="local.documentconverter.pdftext",
    candidate_name="Document-Converter-macos-arm64-pdf-local-candidate",
    excludes=list(PDF_EXCLUDES),
    forbidden=list(PDF_EXCLUDES[:16]),
    forbidden_distributions={
        "pymupdf",
        "fitz",
        # The docling meta package depends on docling-slim[standard], which pulls
        # PyTorch; this profile pins the slim distribution with model-free extras.
        "docling",
        "docling-ibm-models",
        "marker-pdf",
        "magic-pdf",
        "mineru",
        "torch",
        "torchvision",
        "transformers",
        "accelerate",
        "pytest",
        "pytest-cov",
        "pip",
        "pip-audit",
        "pip-licenses",
        "httpx",
    },
    # Docling resolves backends and pipelines through entry points, so the frozen
    # app needs their distribution metadata as well as the module tree.
    hidden_imports=[
        *UVICORN_HIDDEN,
        "document_converter.engines.docling_native_engine",
        "docling.document_converter",
        "docling.datamodel.base_models",
        "docling.datamodel.pipeline_options",
        "docling.pipeline.native_pdf_pipeline",
        "docling.backend.docling_parse_v4_backend",
        "docling.backend.pypdfium2_backend",
    ],
    # Data files these packages read at runtime are not discovered by analysis:
    # latex2mathml's symbol table, jsonschema's registry, langcodes' tables.
    collect_all=[
        "docling",
        "docling_core",
        "docling_parse",
        "pypdfium2",
        "rtree",
        "latex2mathml",
        "jsonschema_specifications",
        "langcodes",
        "doclang",
    ],
    copy_metadata=["docling-slim", "docling-core", "docling-parse"],
    sources=[
        *SHARED_SOURCES,
        "engines/__init__.py",
        "engines/base.py",
        "engines/docling_engine.py",
        "engines/docling_native_engine.py",
    ],
    candidate_notice=(
        "Local test candidate only. Text-layer PDF, Markdown and UTF-8 text to Markdown/HTML.\n"
        "Apple Silicon macOS only. PDF text is read from the file as stored: no OCR, no heading\n"
        "levels, no table reconstruction. A scanned PDF has no text layer and converts to nothing.\n"
        "No Office or image formats, no model weights, no model downloads.\n"
        "No Developer ID signing or notarization; no distribution approval.\n"
        "Closing the browser does not stop the app; quit Document Converter in Activity Monitor.\n"
    ),
)

# PyObjC loads the bridges Vision depends on lazily, by name, so analysis
# cannot see them; every one of them is collected whole.
PYOBJC_PACKAGES = ["objc", "Foundation", "CoreFoundation", "AppKit", "Quartz", "CoreML", "Vision"]

OFFICE_OCR = Profile(
    name="office-ocr",
    manifest_profile="office-ocr",
    requirements_stem="requirements-macos-arm64-office-ocr",
    bundle_identifier="local.documentconverter.officeocr",
    candidate_name="Document-Converter-macos-arm64-office-ocr-local-candidate",
    # The pdf profile's lists unchanged: Office and macOS's OCR need no entry
    # removed, so every model runtime stays excluded and forbidden.
    excludes=list(PDF_EXCLUDES),
    forbidden=list(PDF_EXCLUDES[:16]),
    # OCR comes from the operating system; no OCR engine or model is pinned.
    forbidden_distributions=PDF.forbidden_distributions
    | {"ocrmac", "rapidocr", "onnxruntime", "easyocr", "opencv-python", "opencv-python-headless", "huggingface-hub"},
    hidden_imports=[
        *PDF.hidden_imports,
        "document_converter.engines.docling_office_engine",
        "document_converter.engines.apple_vision_engine",
        "docling.pipeline.simple_pipeline",
        "docling.backend.msword_backend",
        "docling.backend.mspowerpoint_backend",
        "docling.backend.msexcel_backend",
        *PYOBJC_PACKAGES,
    ],
    # python-docx and python-pptx read their default templates at runtime.
    collect_all=[*PDF.collect_all, "docx", "pptx", "openpyxl", *PYOBJC_PACKAGES],
    copy_metadata=list(PDF.copy_metadata),
    sources=[
        *PDF.sources,
        "engines/docling_office_engine.py",
        "engines/apple_vision_engine.py",
    ],
    candidate_notice=(
        "Local test candidate only. Word, PowerPoint and Excel (.docx .pptx .xlsx), PDF, images\n"
        "(.png .jpg .jpeg .webp), Markdown and UTF-8 text to Markdown/HTML/text.\n"
        "Apple Silicon macOS only. Scanned PDFs and images are read with the OCR built into macOS\n"
        "(Apple's Vision framework): paragraphs only, no heading levels or tables, and it can be wrong.\n"
        "No model weights, no model downloads, no deep-learning runtime.\n"
        "No Developer ID signing or notarization; no distribution approval.\n"
        "Closing the browser does not stop the app; quit Document Converter in Activity Monitor.\n"
    ),
)

PROFILES = {profile.name: profile for profile in (TEXT, PDF, OFFICE_OCR)}


def get(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError:
        raise SystemExit(f"Unknown release profile: {name}. Choose from {', '.join(sorted(PROFILES))}.") from None
