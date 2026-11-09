"""Input formats independent of optional conversion engines."""
SUPPORTED = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
    ".html", ".htm", ".epub", ".md", ".markdown", ".txt",
    ".png", ".jpg", ".jpeg", ".webp", ".csv", ".rtf", ".odt", ".ods", ".odp"
}

TEXT_SUPPORTED = frozenset({".md", ".markdown", ".txt"})

# Release profile that adds PDF through the model-free reader: text-layer PDFs
# only, with no OCR, no Office formats and no model weights.
PDF_TEXT_SUPPORTED = frozenset(TEXT_SUPPORTED | {".pdf"})

OFFICE_SUFFIXES = frozenset({".docx", ".pptx", ".xlsx"})
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})

# Release profile that adds Word, PowerPoint and Excel through Docling's readers
# and reads scanned PDFs and images with the OCR macOS ships. Still no model.
OFFICE_OCR_SUPPORTED = frozenset(PDF_TEXT_SUPPORTED | OFFICE_SUFFIXES | IMAGE_SUFFIXES)
