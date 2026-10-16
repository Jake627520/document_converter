# UAT: conversion output and every rejection path

Date: 2026-10-13. Run in this repository's development environment (Linux,
CPython 3.13, Docling installed without PyTorch), against both reviewed release
profiles configured in-process.

Reproduce with:

```sh
pip install -e ".[dev,web]" reportlab
python -I verification/2026-10-13-uat/make_samples.py   # writes samples/, gitignored
python -I verification/2026-10-13-uat/uat.py
```

## Part 1: do converted documents come out right?

Seven documents, each aimed at a defect this project has fixed. `make_samples.py`
generates them, so the inputs are synthetic and no real document is involved.
The `.md` outputs are committed beside this report.

| Sample | Aimed at | Result |
| --- | --- | --- |
| `01-spec-table-zh.pdf` | The cleaner deleting table values | ✅ Every value kept: `84`, `5500 K`, `12`, `35 W`, `6`, `50000 hr`, `1`, and a bare `84` on its own line |
| | HTML entities in Markdown | ✅ `A & B`, `公差 < 300 K`, `P > 30 W` all literal |
| | Chinese text | ✅ Intact throughout |
| `02-long-paragraphs-zh.pdf` | Reading-order recovery | ⚠️ Each PDF line becomes its own paragraph — a documented limit of the model-free reader, recorded as a warning on every conversion, not a regression |
| `03-multipage-pagenumbers.pdf` | Page markers vs. real values | ✅ `17`, `34`, `51` kept; `Page 1 of 3`, `- 1 -`, `1` present and removed only with `--clean` |
| `06-image-with-caption.pdf` | A picture with some text | ✅ The caption converts; the unreadable picture becomes `<!-- image -->` |
| `07-entities-and-quotes.pdf` | The entity fix, fully | ✅ `&`, `<`, `>`, `"ready"`, `<div>`, `C:\Users\x` all literal |
| `04-drawing-no-text.png` | An image with no text | See part 2 |
| `05-image-only-no-text.pdf` | A scan with no text layer | See part 2 |

One apparent defect was traced and dismissed: `01`'s output reads `R&D;` with a
stray semicolon. Reading the PDF with `pypdf`, independently of this project,
shows `R&D;` is in the PDF itself — reportlab mangled a bare `&` while building
the sample. The converter reproduced the document faithfully.

## Part 2: what a user sees when something is wrong

Four defects were found by this UAT and fixed in the same change.

| Case | Before | After |
| --- | --- | --- |
| Image-only PDF, full install | **200 and a 97-byte file holding `<!-- image -->`** | 422, naming the cause and that OCR is needed |
| Empty `.md` | **200 and a 0-byte download** | 422: 這個檔案沒有抽出任何文字。檔案可能是空的，或只有空白。 |
| Unsupported input | `Unsupported input type` — English, on a Chinese page, naming nothing | 這個版本不支援「.docx」檔案。可以轉換的格式：.markdown、.md、.pdf、.txt。 |
| No file selected | FastAPI's own `[{'type': 'missing', 'loc': ['body', 'files'] …}]` | 400: 請先選擇 1 到 5 個檔案。 |

Other messages were translated to match the page: the size and count limits, the
output-format list, the cross-origin and busy responses, and the conversion
failure. A non-UTF-8 text file now gets its own message naming Big5, GBK and
UTF-16 and asking for a re-save, instead of a Python codec error.

`uat-after.txt` holds the full matrix as it stands after the fixes: 14 cases ×
2 profiles. Every message is Traditional Chinese, matching the interface.
It was regenerated on 2026-10-15, after the size limits came to be stated in
both units (`24 MiB（約 25 MB）`); no other line changed.

### How images are handled, by path

| Upload | `text` app | `pdf` app | Full install from source |
| --- | --- | --- | --- |
| `.png` image file | 400, unsupported | 400, unsupported | 422 — Docling's image pipeline needs PyTorch, which is absent here |
| PDF that is one picture | 400, unsupported (no PDF at all) | 422, no text layer, no OCR in this release | 422, no text recovered, naming the engine |
| PDF with a caption and a picture | 400, unsupported | 200, caption converted | 200, caption converted |

**No OCR is shipped.** Neither profile contains an OCR engine, and a scan is
reported rather than guessed at.

## Not covered here

The macOS `.app` itself: this run exercises the same code in-process, not a
frozen bundle. `tests/test_release_packaging.py` covers the frozen launcher, and
`docs-release/macos-vm-verification.md` covers a clean machine. Docling's
model-based pipeline and OCR engines are not installed in this environment and
are outside both release profiles.
