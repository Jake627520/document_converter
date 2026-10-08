---
spec_id: "005"
title: "PDF Text-Layer vs Scanned Auto-Detection Specification"
version: "0.2.0"
status: "APPROVED"
updated: "2026-10-08"
---

# 005 - PDF Text-Layer vs Scanned Auto-Detection Specification

## 1. Objective
Automatically detect whether an input PDF has an extractable digital text layer or consists primarily of scanned images, enabling the pipeline to select appropriate processing without wasted OCR compute.

## 2. Classification Heuristic
- **text_based**: Average characters per page >= 25.
- **scanned**: Total characters < 10 AND images present (or total characters == 0).
- **hybrid**: Between 10 and 25 characters, or partial pages with sparse text.

## 3. Graceful Multi-Layer Analysis
1. `pypdf` reader (if installed).
2. `pymupdf` / fitz (if installed).
3. Zero-dependency built-in PDF stream analyzer (parses `/Type /Page`, `stream` ... `endstream`, `BT` ... `ET`, and `/Subtype /Image`).
