# Development Roadmap

## Current implemented changes

- **CHG-001 — Standalone offline HTML renderer**: implemented in `document_converter/renderer.py` and integrated with the writer. Its OpenSpec change remains in the change history pending review/archive workflow.
- **CHG-002 — Batch parallel processing**: implemented with a default of one worker, a hard limit of four, per-file fault isolation, relative-directory preservation, and collision-safe output names. Its OpenSpec change remains in the change history pending review/archive workflow.
- **PDF text/scanned detection**: already implemented in `document_converter/detector.py` and integrated into engine selection in `document_converter/pipeline.py`. Do not create a new OCR-detection implementation change unless a specific missing behavior is identified.

## Active development

- **CHG-003 — Watch mode**: in development under `openspec/changes/CHG-003-watch-mode/`. Uses standard-library polling, stable-file fingerprints, output-subtree exclusion, and existing batch fault isolation. Local-first; no runtime dependency or model is added.

CHG-003 is approved for implementation in this development session; it has not yet been committed or released.
