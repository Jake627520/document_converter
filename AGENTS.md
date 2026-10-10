# Coding-agent instructions

## Project rules
- Keep document conversion local-first.
- Do not add remote document-upload APIs unless explicitly requested.
- Keep parser engines behind `document_converter/engines/`.
- Keep output serialization in `writer.py`.
- Add a regression test for every parser or renderer behavior change.
- Prefer current upstream APIs and avoid pinning exact patch versions unless a reproducibility bug requires it.

## Validation
Run:
```bash
python -m pytest
document-converter --help
document-converter list-engines
```
