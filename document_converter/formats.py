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
