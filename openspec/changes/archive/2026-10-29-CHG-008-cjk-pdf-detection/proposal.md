# CHG-008: PDF CJK Text Detection and Scanned-PDF Warning

## Problem Statement
In previous versions of `document_converter.detector`, PDF text detection relied on a simple ASCII printable byte filter (`32 <= c <= 126 or c in (9, 10, 13)`) on parenthesized literal strings `\(([^)]+)\)` in `_inspect_builtin`. This caused severe issues:
1. Digital CJK documents (Traditional Chinese, Simplified Chinese, Japanese, Korean) using Type 0 composite fonts, CIDFont mappings, ToUnicode CMaps, or hexadecimal string operators (`<00010002> Tj`) were evaluated as containing 0 text characters, triggering false `scanned` classifications whenever images (like logos or headers) were present.
2. Even when parsed with `pypdf`, short CJK titles or single-sentence notices (10-24 characters) were classified as `hybrid` or `scanned` because the threshold `avg_chars >= 25` assumed Latin word character counts, failing to account for CJK semantic density where 1 CJK character is equivalent to ~2.5 Latin characters.
3. Empty files (0 bytes) or corrupted non-PDF files threw exceptions and fell back to `_classify(page_count=1, total_chars=0)`, diagnosing corrupt files as `scanned` with `is_scanned=True`.
4. Warnings across CLI and web pipelines lacked distinction between confirmed scanned documents vs inconclusive/unknown states.

## Proposed Changes
1. **CJK Density & Character Weighting**:
   - Introduce `_is_cjk` check covering CJK Unified Ideographs, Extension A/B, Hangul, Hiragana, Katakana, and fullwidth forms.
   - Calculate `effective_chars` weighting CJK characters with 2.5x density factor for classification thresholds.
2. **Built-in Stream Analyzer CMap & Hex String Decoding**:
   - Extract and parse `beginbfchar` mappings from ToUnicode CMaps in PDF streams.
   - Extract and decode hex strings `<...>` and UTF-16BE bytes within `BT...ET` blocks.
3. **Conservative Unknown Error State**:
   - Inspect file size and `%PDF-` magic header before attempting analysis.
   - Return `classification="unknown"`, `is_scanned=False`, and `has_text_layer=False` for 0-byte or corrupted inputs.
4. **Scanned Warning Differentiation & Multi-Language Support**:
   - In `pipeline.py`, emit `Scanned PDF detected` only when `profile.classification == "scanned"`. For `hybrid`, emit `Sparse text or mixed PDF detected`.
   - In `web_app.py`, update `_no_text_recovered` with conservative messaging for `unknown` classifications across `en`, `zh-TW`, and `zh-CN`.
