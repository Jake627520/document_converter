---
spec_id: "003"
title: "Output Formats & Serialization Specification"
version: "0.2.0"
status: "APPROVED"
updated: "2026-10-08"
---

# 003 - Output Formats & Serialization Specification

## 1. Overview
Output serialization is strictly encapsulated in `document_converter.writer.py`.

## 2. Supported Formats
- **Markdown (`.md`)**:
  - Encoded in UTF-8.
  - Supports `--clean` post-processing to strip redundant blank lines and page number noise while strictly protecting fenced code blocks and math blocks.
  - Supports `--preserve-layout` to retain raw page breaks.
- **HTML (`.html`)**:
  - Full HTML5 document with `<meta charset="utf-8">` and document title.
  - Generated directly by engine when available, or rendered via markdown parser fallback.
- **JSON (`.json`)**:
  - Normalized structured document representation (Docling dict export).
- **Text (`.txt`)**:
  - Markdown-derived clean plain text with headings and code fences flattened.

## 3. Assets Handling
When images are referenced (`--images referenced`), binaries are extracted to `<stem>_assets/` and relative links in Markdown/HTML point to this folder.
