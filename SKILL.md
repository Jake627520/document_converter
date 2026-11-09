---
name: document-converter
description: Convert local documents such as PDF, DOCX, PPTX, XLSX, EPUB, HTML, images and text into Markdown, HTML, JSON, or plain text. Prefer local/offline processing. Use Docling as the primary engine and optionally fall back to Marker or MinerU for difficult PDFs/OCR, or to macOS's built-in OCR (apple-vision) for scans and photos.
---

# Document Converter Skill

Use this skill when the user asks to convert one or more documents between source formats and Markdown/HTML/JSON/text.

## Goals
- Keep document processing local by default.
- Preserve headings, reading order, tables, formulas, lists, images and captions where the parser supports them.
- Support single files and directories.
- Let the user select one or more outputs: md, html, json, txt.
- Do not upload documents to a remote service unless the user explicitly requests a remote/API mode.
- Prefer `docling` for general document conversion.
- Use `marker` or local `mineru` when explicitly requested or when Docling fails and the corresponding backend is installed.
- Use `docling-office` for Word, PowerPoint and Excel where only Docling's model-free readers are installed, and `apple-vision` on macOS for scans and photos when no model-based OCR can run.

## Commands
```bash
document-converter INPUT --to md
document-converter INPUT --to html
document-converter INPUT --to md html json
document-converter INPUT --output ./out --images referenced
document-converter ./docs --to md html --output ./out
document-converter INPUT --engine auto
document-converter INPUT --engine docling
document-converter INPUT --engine marker
document-converter INPUT --engine mineru
document-converter INPUT --engine docling-office   # .docx .pptx .xlsx, no model
document-converter INPUT --engine apple-vision     # macOS built-in OCR, scans and photos
```

## Engine policy
1. `auto`: Docling first.
2. If Docling fails and Marker is installed, retry with Marker for PDF/image inputs.
3. If still unavailable/failing and local MinerU is installed, retry with MinerU.
4. For a scanned PDF or an image on macOS, then try `apple-vision`; for `.docx` `.pptx` `.xlsx`, `docling-office`.
5. Never silently use a cloud API.
6. Report which engine was used, and that recognized text should be checked when OCR ran.

## Output policy
- `md`: UTF-8 Markdown.
- `html`: complete HTML document.
- `json`: normalized Docling JSON when available.
- `txt`: Markdown-derived plain text.
- `--images referenced` writes assets beside the output and references them from MD/HTML.
- `--images embedded` embeds image data when the backend supports it.
- `--images none` uses parser defaults/placeholders.

## Safety/privacy
Local files stay local unless the user explicitly selects a remote engine. Do not send document contents to third-party services.
