---
spec_id: "002"
title: "Engine Adapter Architecture Specification"
version: "0.2.0"
status: "APPROVED"
updated: "2026-10-08"
---

# 002 - Engine Adapter Architecture Specification

## 1. Overview
Parser engines are isolated behind a unified abstract interface (`document_converter.engines.base.Engine`). This prevents external package changes, CLI deprecations, or license restrictions from leaking into the core application.

## 2. Interface Definition
```python
class Engine:
    name: str

    def can_handle(self, path: Path) -> bool:
        """Return True if this engine can process the given file type."""
        ...

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        """Parse input and return unified ConversionResult or raise EngineError."""
        ...
```

## 3. Registered Adapters
1. **DoclingEngine (`docling`)**:
   - Primary default engine.
   - Licensed under MIT.
   - Python native integration via `docling.document_converter.DocumentConverter`.
2. **MarkerEngine (`marker`)**:
   - Optional PDF specialist fallback.
   - Licensed under GPL-3.0 (must be isolated).
   - CLI subprocess execution via `marker_single` / `marker`.
3. **MinerUEngine (`mineru`)**:
   - Optional PDF & OCR specialist fallback.
   - Subprocess execution via `mineru` / `mineru-kit`.
   - Never redistributes model weights.
