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
  - When an engine provides native HTML, the writer preserves it unchanged.
  - When native HTML is absent and Markdown is available, a built-in parser generates a complete HTML5 document with UTF-8 metadata, escaped document title, and embedded CSS.
  - The fallback has no additional runtime dependency, does not call a network service, and emits no external CSS, JavaScript, or font references.
  - Supported fallback Markdown constructs: headings, paragraphs, ordered/unordered lists, tables, fenced code, inline code, bold, and italic. Empty Markdown still produces a complete HTML document.
  - Source text and title are escaped; raw HTML is not executed. Code-fence language classes accept only `[A-Za-z0-9_+-]+`.
  - LaTeX is not rendered; formula markers remain escaped text.
- **JSON (`.json`)**:
  - Normalized structured document representation (Docling dict export).
- **Text (`.txt`)**:
  - Markdown-derived clean plain text with headings and code fences flattened.

## 3. Assets Handling
When images are referenced (`--images referenced`), binaries are extracted to `<stem>_assets/` and relative links in Markdown/HTML point to this folder.
