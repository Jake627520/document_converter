# CHG-008 Design: PDF CJK Text Detection & Scanned PDF Warnings

## Architecture & Detection Pipeline

```
PDF File Input
      │
      ▼
Early Validation (exists, size > 0, %PDF- header)
      ├── Fail ──► PdfProfile(classification="unknown", is_scanned=False, has_text_layer=False)
      │
      ▼
Library Inspection (pypdf -> pymupdf -> _inspect_builtin)
      │
      ├── Extract Text / Parse Hex Streams & CMaps
      ├── Calculate total_chars & effective_chars (CJK weight = 2.5x)
      │
      ▼
Classification (_classify)
      ├── avg_effective >= 25 ──────────► text_based (has_text_layer=True, is_scanned=False)
      ├── effective_chars < 10 & has_images ──► scanned (has_text_layer=False, is_scanned=True)
      ├── effective_chars < 10 & no_images ──► unknown (has_text_layer=False, is_scanned=False)
      ├── 10 <= effective_chars < 25 & has_images ──► hybrid (has_text_layer=True, is_scanned=True)
      └── 10 <= effective_chars < 25 & no_images ──► text_based (has_text_layer=True, is_scanned=False)
```

## Key Technical Decisions

1. **Local-First Zero External Weights**:
   - Uses standard Python `zlib`, `re`, and existing `pypdf` without adding any new external dependencies or heavy model downloads.
2. **CJK Character Range**:
   - `0x4E00..0x9FFF`: CJK Unified Ideographs
   - `0x3400..0x4DBF`: CJK Extension A
   - `0x20000..0x2A6DF`: CJK Extension B
   - `0xF900..0xFAFF`: CJK Compatibility Ideographs
   - `0x3040..0x309F`: Hiragana
   - `0x30A0..0x30FF`: Katakana
   - `0xAC00..0xD7AF`: Hangul Syllables
   - `0x1100..0x11FF`: Hangul Jamo
   - `0xFF00..0xFFEF`: Halfwidth/Fullwidth forms
3. **Sparse Text & OCR Artifact Defense**:
   - If a scanned document contains an image and a stray character (e.g. `1` or a stray period with `effective_chars < 10`), it is classified as `scanned`, not `text_based`.
4. **Warning Hierarchy & Conservative Diagnosis**:
   - Scanned warnings are only emitted when `classification == "scanned"`.
   - Hybrid files receive a sparse/mixed content warning.
   - Unparseable or empty files receive an inconclusive/unknown warning, preventing false statements that a corrupted file is a scanned document.
