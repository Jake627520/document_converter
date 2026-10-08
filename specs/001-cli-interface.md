---
spec_id: "001"
title: "CLI Interface Specification"
version: "0.2.0"
status: "APPROVED"
updated: "2026-10-08"
---

# 001 - CLI Interface Specification

## 1. Overview
The `document-converter` CLI provides a local-first interface to convert documents between source formats (PDF, Office, HTML, Markdown, images) and target representations (Markdown, HTML, JSON, TXT).

## 2. Command Signature
```bash
document-converter convert [OPTIONS] SOURCE
document-converter inspect [OPTIONS] SOURCE
document-converter list-engines
```

## 3. Arguments & Options (`convert`)
- `SOURCE`: Path to a single input file or directory (recursively processed).
- `--to [md|html|json|txt]`: Desired output format(s). Can be specified multiple times. Default: `md`.
- `--output / -o PATH`: Target directory. Default: `./converted`.
- `--engine [auto|docling|marker|mineru]`: Engine selection. Default: `auto`.
- `--images [none|referenced|embedded]`: Image asset handling mode. Default: `none`.
- `--clean / --no-clean`: Clean markdown artifacts, extra newlines, and page noise. Default: `false`.
- `--preserve-layout`: Retain original page breaks, spacing, and delimiters. Default: `false`.

## 4. Subcommands
- `inspect`: Pre-scans PDF documents to report page count, character count, text-layer presence, and classification (`text_based` vs `scanned`).
- `list-engines`: Lists all registered engines, installation status, and installation commands.

## 5. Exit Codes & Error Handling
- `0`: All files processed successfully.
- `1`: Syntax error, unhandled exception, or missing arguments.
- `2`: Bad parameter (e.g. invalid format or unsupported engine).
