# CHG-008 Tasks

## 1. Safety & Baseline Audit
- [x] Run git status and diff stat; ensure Phase 1/1.1/1.2 changes are preserved.
- [x] Verify current commit `acb4e9b` on `main`.

## 2. Investigation & TDD Fixtures
- [x] Analyze `document_converter/detector.py` CJK detection flaws.
- [x] Create Type 0 CJK synthetic fixtures in `tests/pdf_samples.py` (TC, SC, JA, KO).
- [x] Add boundary fixtures: sparse text with image, empty PDF, corrupt PDF.
- [x] Add regression tests in `tests/test_detector.py` and confirm TDD RED failure mode.

## 3. Implementation
- [x] Implement CJK range check `_is_cjk` and density weighting in `_classify`.
- [x] Implement ToUnicode CMap parser `_parse_cmap` and hex string decoding in `_inspect_builtin`.
- [x] Implement early validation for empty and corrupt PDFs returning `classification="unknown"`.
- [x] Update `_inspect_with_pypdf` and `_inspect_with_fitz` with CJK weighting and empty file handling.
- [x] Update `pipeline.py` warning dispatch to check `classification == "scanned"`.
- [x] Update `web_app.py` `_no_text_recovered` with conservative messaging for `unknown` in `en`, `zh-TW`, and `zh-CN`.

## 4. Verification & OpenSpec
- [x] Run `tests/test_detector.py` and `tests/test_pipeline.py`.
- [x] Run full pytest excluding release packaging: `.venv/bin/python -m pytest --ignore=tests/test_release_packaging.py`.
- [x] Verify coverage >= 80% (achieved 86.77% across 207 tests).
- [x] Update `openspec/specs/pdf-detection/spec.md`.
- [x] Maintain security limitation note: CSP `unsafe-inline` and browser E2E test limitations documented.
