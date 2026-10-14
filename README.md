# Document Converter

**English** | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md)

A local-first document converter: a command-line tool, a browser workbench that
runs on your own computer, a packaged macOS app, and an agent skill
([`SKILL.md`](SKILL.md)) for Codex and Claude. Documents are converted on your
machine; nothing is uploaded to a remote service.

How it was built, and the ten defects that looked fine until they were checked:
the [case study](docs/case-study/README.md), also in [繁體中文](docs/case-study/README.zh-TW.md) and [简体中文](docs/case-study/README.zh-CN.md).

---

## 1. What it converts

**Inputs.** What a given install accepts depends on which engines it has.

| Input | From source, Docling installed | macOS app, `text` profile | macOS app, `pdf` profile |
|---|---|---|---|
| Markdown `.md` `.markdown` | ✅ | ✅ | ✅ |
| UTF-8 text `.txt` | ✅ | ✅ | ✅ |
| PDF **with a text layer** | ✅ | ❌ | ✅ |
| PDF that is a **scan or photo** | ⚠️ needs an OCR engine installed separately | ❌ | ❌ |
| Office `.docx` `.pptx` `.xlsx` and older | ✅ | ❌ | ❌ |
| `.html` `.htm` `.epub` `.csv` `.rtf` OpenDocument | ✅ | ❌ | ❌ |
| Images `.png` `.jpg` `.jpeg` `.webp` | ⚠️ needs Docling's model pipeline (PyTorch) | ❌ | ❌ |

A file the install does not accept is refused before any conversion starts, and
the message names the formats that would work — for example, from the `pdf`
app: 這個版本不支援「.docx」檔案。可以轉換的格式：.markdown、.md、.pdf、.txt。

**A text file must be UTF-8.** A Big5, GBK or UTF-16 file is refused with a
message saying so and asking you to re-save it as UTF-8; it is not converted
into mojibake.

**Limits.** Up to 5 files per conversion, each up to 24 MiB (about 25 MB as Finder
counts it), 25 MiB (about 26 MB) per request. A MiB is 1,048,576 bytes; the MB
Finder shows is 1,000,000, so a file Finder lists as 25.1 MB is still accepted.

**Nothing is ever returned empty.** If a conversion recovers no text — a scan
with no text layer, a page that is one picture, an empty file — the answer says
that and why, rather than downloading a 0-byte file.

**Outputs.**

| Output | From source (CLI and browser) | macOS app, `text` profile | macOS app, `pdf` profile |
|---|---|---|---|
| Markdown (`.md`) | ✅ | ✅ | ✅ |
| HTML (`.html`) | ✅ | ✅ | ✅ |
| Plain text (`.txt`) | ✅ | ✅ | ✅ |
| Docling JSON (`.json`) | ✅ when a Docling engine parsed the file | — | ✅ PDF input only |

Docling JSON is the engine's own structural parse of a document, so it exists
only where an engine read the file. Markdown and text files are read directly,
and the `text` app runs no engine at all.

## 2. macOS app

It runs on Apple Silicon (M-series) Macs only. Two reviewed profiles exist:

| Profile | Accepts | Bundles |
|---|---|---|
| `text` | UTF-8 `.md`, `.markdown`, `.txt` | No document engine and no model |
| `pdf` | The above, plus **PDFs that already contain a text layer** | Docling's model-free PDF reader — no OCR, no AI model, no PyTorch, nothing downloaded |

The `pdf` profile extracts the text a PDF already holds. It does not rebuild
heading levels or tables, and a scanned PDF has no text layer: the app says so
instead of returning an empty file. Office documents and images are not
accepted by either profile.

### Opening the app

- **An app you built yourself** opens with a double-click: macOS only gates
  files that arrived from the internet.
- **An app you received** — downloaded, sent by AirDrop or through a chat app —
  is blocked on first launch, because the candidate is only ad-hoc signed, with
  no Developer ID signature or Apple notarization. From macOS 15 onward,
  Control-click › Open no longer gets past this. Try to open the app once, then
  go to **System Settings › Privacy & Security**, find the app under
  *Security*, choose **Open Anyway** and enter an administrator password.

Do not disable Gatekeeper to get around this.

### Using it

1. Double-click `Document Converter.app`. It starts a local service and opens
   your default browser at `http://127.0.0.1:<port>`.
2. Drop in or select up to **5** files. Each file, and the selection as a whole,
   may be up to **24 MiB (about 25 MB)**.
3. Choose an output format and select **Convert**. One file downloads on its
   own; several download as a ZIP. Each download is named after the document it
   came from, Chinese file names included.
4. Uploads are held in the system's temporary folder under generated names and
   removed after every conversion.
5. Closing the browser does not stop the app. To quit it, open
   **Activity Monitor**, find `Document Converter` and quit it.

You do not need Python, Node.js, Docker or VS Code to run the app.

### Status

| | |
|---|---|
| ✅ Verified on an Apple Silicon Mac (2026-10-12/13) | `pdf` candidate built, signed ad-hoc and zipped; opened like any app and converted a real document; its frozen runtime reported no forbidden module; it carried 124 third-party notice files |
| ℹ️ Rebuild to update | That candidate predates the plain text and Docling JSON outputs and the download names; a candidate built from this version has them |
| ⏳ Not yet verified | Installing on a second Mac — [`docs-release/macos-vm-verification.md`](docs-release/macos-vm-verification.md) covers it with a free macOS virtual machine |
| ❌ Not done | Developer ID signing and Apple notarization; every candidate is marked `distribution_ready: false` |
| ❌ Not available | Windows — there is no installer and no platform testing |

### Building it

```sh
RELEASE_PROFILE=pdf BUILD_PYTHON="$HOME/.local/bin/python3.12" \
  sh scripts/packaging/bootstrap_macos.sh --output-dir build/private-release/candidate-pdf
```

Leave out `RELEASE_PROFILE=pdf` for the `text` profile. The full build and
acceptance procedure is in [`docs-release/macos.md`](docs-release/macos.md).

## 3. From source (developers)

Python 3.11 to 3.14 is supported; CI tests 3.11 and 3.12.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .
```

The Windows command sets up the source tree only; it does not mean Windows has
been tested.

### Browser workbench

```bash
pip install -e ".[web]"
document-converter web             # http://127.0.0.1:8765 ; --port 8766 for another port
```

The server binds to loopback only. The same limits as the app apply: up to five
files, 24 MiB (about 25 MB) each and in total, 25 MiB (about 26 MB) per request. It uses the CLI's `auto`
engine selection, so it uses whichever engines are installed — Marker and
MinerU included — but it never installs one.

### Command line

```bash
document-converter convert paper.pdf --to md
document-converter convert paper.pdf --to md --to html --to json --to txt
document-converter convert ./documents --to md --output ./converted
document-converter list-engines
```

Choose an engine explicitly:

```bash
document-converter convert paper.pdf --engine docling --to md
document-converter convert paper.pdf --engine docling-native --to md   # no PyTorch, no model download
document-converter convert paper.pdf --engine marker --to md
document-converter convert paper.pdf --engine mineru --to md
```

Remove Markdown noise:

```bash
document-converter convert paper.pdf --to md --clean
document-converter convert paper.pdf --to md --clean --strip-page-numbers
```

`--clean` removes labelled page markers such as `Page 3 of 12`, `4 / 20` and
`- 5 -`. It keeps lines holding only digits, because engines put table cells and
other values on their own line; add `--strip-page-numbers` only when a
document's page numbers survive as bare numerals and you accept losing
standalone numbers with them.

### PDF without PyTorch (`docling-native`)

Docling's default PDF pipeline runs layout and table models: it needs PyTorch, a
multi-gigabyte install, and downloads model weights on first use.
`docling-native` uses Docling's model-free `NativePdfPipeline` instead:

```bash
pip install "docling-slim[convert-core,format-pdf]" typer rich pypdf
pip install -e . --no-deps
```

That install is about 0.4 GB. It converts PDF only, rebuilds no structure, runs
no OCR, and records that limitation as a warning on every conversion. `auto`
tries it last, so model-based engines are preferred wherever they are
installed.

### Optional engines

```bash
pip install ".[marker]"   # check the package and model license terms first
# MinerU: install its CLI separately, after reading docs/LICENSE_AUDIT.md
```

## 4. How it works

Every engine produces one normalized conversion result, and the writer turns it
into the requested outputs. Parsing stays separate from rendering, so an input
format or an output can be added without touching the CLI. Engines sit behind
adapters in `document_converter/engines/`; output serialization lives in
`writer.py`.

### What it is built on

This project writes the interfaces, the engine selection, the scanned-PDF
detection, the Markdown cleaner, the renderer and the packaging. The conversion
itself is done by these:

| Part | Component | License | Bundled in the macOS app? |
|---|---|---|---|
| PDF reading, no model | **Docling** `docling-slim`, `docling-core`, `docling-parse` | MIT | ✅ `pdf` profile |
| PDF parsing underneath it | **pypdfium2** and Google's **PDFium** | BSD-3-Clause / Apache-2.0 | ✅ `pdf` profile |
| Browser interface | **FastAPI**, **Starlette**, **Uvicorn** | MIT / BSD | ✅ both |
| Command line | **Typer**, **Rich** | MIT | ✅ both |
| Scanned-PDF detection | **pypdf**, or a built-in stream reader when it is absent | BSD-3-Clause | ✅ both |
| Packaging into an app | **PyInstaller** | GPL-2.0-or-later **with its Bootloader exception** | ✅ bootloader only |
| PDF with layout and table models | Docling's model pipeline, needing **PyTorch** and downloaded weights | MIT code, model terms separate | ❌ |
| Alternative PDF/OCR engines | **Marker**, **MinerU** | Apache-2.0 code; separate model and additional terms | ❌ |

**OCR: this project ships none.** No OCR engine or vendor is included in either
macOS profile, and a scan is reported as having no text layer rather than
guessed at. OCR exists only if you install Marker or MinerU yourself, under
their own terms — see [`docs/LICENSE_AUDIT.md`](docs/LICENSE_AUDIT.md), which
records what was checked and when.

### Fork it and run your own

The repository is public so that it can be read and run. It is not open source
(section 8): forking to read, study or run it is fine, and republishing or
selling the project's own software is not.

```bash
# 1. Fork on GitHub, then clone your fork
git clone https://github.com/<your-account>/documnet_converter.git
cd documnet_converter

# 2. Python 3.11 to 3.14
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip

# 3. Markdown and text only, no engine, smallest install
pip install -e ".[web]"

# 4. Add PDF without PyTorch - about 0.4 GB, downloads no model
pip install "docling-slim[convert-core,format-pdf]"

#    or add PDF with layout and table models - multi-gigabyte, downloads weights
#    pip install docling

# 5. Check what it found, then start the browser interface
document-converter list-engines
document-converter web
```

`list-engines` prints which engines this install actually has, so step 5 tells
you what you really got rather than what the documentation hopes for.

To run the tests and the checks this project runs on itself:

```bash
pip install -e ".[dev,web]"
python -m pytest                       # 186 tests
document-converter --help
document-converter list-engines
python3 scripts/packaging/audit_notices.py --profile pdf   # needs network
```

Building the macOS app needs an Apple Silicon Mac; see
[`docs-release/macos.md`](docs-release/macos.md).

## 5. Your documents

> [!IMPORTANT]
> 1. Before converting any document — PDF, Office file, image or scan — make
>    sure you hold the right to process and, where relevant, distribute it.
> 2. Never commit client confidential material, real business documents,
>    personal data or unlicensed copyrighted documents to this repository.
> 3. The automated tests use only synthetic, public-domain or non-sensitive
>    documents.

## 6. Security and privacy

- **Local-first.** Documents are processed by locally installed engines.
  Network behaviour has not been audited for every engine, package and model
  downloader combination; check the engine you select before processing
  sensitive files.
- **Uploads.** Kept under generated temporary names and removed after each
  request, including failed ones.
- **Logging.** The CLI reports status and errors. Third-party engines may log on
  their own.
- **Sensitive files.** `.gitignore` covers common outputs, credentials,
  temporary assets and model caches. It does not remove files already tracked;
  check `git status` before every commit.

## 7. Support

This is a personal project, published so that it can be read and used. It
comes as it is, with no commitment to support, to answer questions, to fix a
problem or to keep it working. Issues and pull requests may go unanswered.
Before you process anything that matters, check the output: the limits each
engine has are described above and recorded as warnings on every conversion.

## 8. Licenses

**This project.** Copyright (c) 2026 Jake Chiu, under a
[proprietary use license](LICENSE): personal use and a company's internal use,
including internal commercial use, are permitted; resale and redistribution of
the project's own software are not. It is not an open-source license, and this
repository being public does not make it one: reading the source here grants no
right the `LICENSE` does not give. The `LICENSE` file is authoritative; this
paragraph only summarizes it.

**Third-party components** keep their own licenses, and nothing here restricts
the rights their authors grant. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
and [`docs/LICENSE_AUDIT.md`](docs/LICENSE_AUDIT.md). Each installer carries
every component's original license and notice texts in its `legal/` folder.

The `pdf` profile of the macOS app includes software based in part on the work
of the FreeType Team and of the Independent JPEG Group.
