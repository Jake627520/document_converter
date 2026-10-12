# macOS arm64 `pdf` release candidate: first real build

Run by the project owner on their own Apple Silicon Mac. Everything below is
that machine's output, not a reproduction: this repository's CI and the agent
environment are Linux, and the candidate needs macOS arm64, the pinned
python-build-standalone runtime, `codesign` and `ditto`.

- Date: 2026-10-12
- Branch: `claude/elegant-bohr-zi2ef5`
- Host: macOS 27.0.1, arm64
- Build Python: CPython 3.12.13 (`~/.local/bin/python3.12`)
- PyInstaller 6.22.3, contrib hooks 2026.8

## Build

```
RELEASE_PROFILE=pdf BUILD_PYTHON="$HOME/.local/bin/python3.12" \
  sh scripts/packaging/bootstrap_macos.sh --output-dir build/private-release/candidate-pdf
```

60 packages installed from `requirements-macos-arm64-pdf.lock`. Result:

```json
{
  "profile": "pdf-text",
  "app": ".../candidate-pdf/Document-Converter-macos-arm64-pdf-local-candidate/Document Converter.app",
  "zip": ".../candidate-pdf/Document-Converter-macos-arm64-pdf-local-candidate.zip",
  "zip_sha256": "16a0f2be376c605ff6a6fee7dd04e42499042f7ba0ee5c219344299b261a18b6",
  "distribution_ready": false
}
```

### Build warnings, all expected

| Warning | Why it is expected |
| --- | --- |
| `docling.service_client` needs `httpx` | Docling's remote-service client. This project is local-first, so the absence of `httpx` is the intended outcome, not a gap. |
| `docling_core.transforms.chunker` needs `tree_sitter` | Document chunking for retrieval pipelines; unused here. |
| `scipy.special._cdflib` not found | Stale entry in scipy's own PyInstaller hook; the module no longer exists upstream. |
| `jinja2` not found | A templating engine. HTML output comes from this project's own renderer. |
| `user32`, `msvcrt` not found | Windows libraries, absent on macOS by definition. |

## Frozen application

```
"…/Document Converter.app/Contents/MacOS/Document Converter" --diagnostics
```

```json
{
  "profile": "pdf-text",
  "inputs": [".markdown", ".md", ".pdf", ".txt"],
  "frozen": true,
  "python": "3.12.13 (main, Jun 23 2026, 15:44:24) [Clang 22.1.3 ]",
  "forbidden_loaded": []
}
```

`forbidden_loaded` empty: no deep-learning runtime, no optional engine, no CLI
or pipeline module is loaded in the frozen app. `sys.path` holds only the three
bundle entries, with no external site-packages.

## Release runtime tests

```
build/private-release/venv-pdf/bin/python -I -m unittest discover -s tests -p test_release_packaging.py -v
Ran 7 tests in 2.970s — OK
```

Both profiles' runtime behaviour, including a real text-layer PDF converting, a
scanned PDF reported rather than returned empty, and the reviewed `text`
profile still rejecting PDFs.

## Third-party notices

The point of this round. Before the fix in this branch the build stopped with
`No original license/notice in installed wheel: latex2mathml`, and would have
collected 103 notice files while silently dropping 21.

```
find legal/third-party/pypdfium2 -type f | wc -l
      18
find legal/third-party/tqdm legal/third-party/latex2mathml -type f
legal/third-party/tqdm/tqdm-4.70.1.dist-info/licenses/LICENCE
legal/third-party/latex2mathml/latex2mathml-3.80.0.dist-info/licenses/LICENSE
```

`legal/THIRD_PARTY_INVENTORY.json`: profile `pdf-text`, 60 packages,
**124 notice files**. The 21 recovered match the Linux audit of the same
pinned wheels exactly (`scripts/packaging/audit_notices.py --profile pdf`).

## Still not verified

- Finder double-click launch, and the Gatekeeper prompt a first launch shows.
- Installing the ZIP on a second Mac.
- Developer ID signing and notarization. The candidate is ad-hoc signed and
  marked `distribution_ready: false`.
- Docling's model-based pipeline, OCR for scanned pages, and Windows. These are
  outside this profile's scope, not merely untested.
