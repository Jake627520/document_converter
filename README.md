# Document Converter Skill

A local-first document conversion CLI, browser workbench, and Codex/agent Skill.

---

## 1. Supported Inputs

Docling handles a broad set of formats including PDF, DOCX, PPTX, XLSX, HTML, EPUB, images, Markdown and text. See the upstream support matrix for the installed Docling version.

## 2. Outputs

- Markdown (`.md`)
- HTML (`.html`)
- Docling JSON (`.json`)
- Plain text (`.txt`)

## 3. Installation

Recommended Python: 3.11 or 3.12.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

python -m pip install -U pip
pip install -e .
```

The Windows commands above are setup instructions for the Python source tree;
they do not indicate that Windows has a packaged application or has passed
platform testing. No Windows installer is currently available.

### Local Browser Workbench (Optional)

Install the web extra and start the local interface:

```bash
pip install -e ".[web]"
document-converter web
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). The server binds only to loopback; use `document-converter web --port 8766` to choose another local port. Drop or select up to five supported documents, choose Markdown or HTML, and download the result (multiple inputs are returned as a ZIP). Each file and the combined selection are limited to 24 MiB; the complete multipart request is capped at 25 MiB. The web feature uses the existing `auto` conversion pipeline and does not install or enable optional Marker/MinerU engines.

Uploads are held under generated temporary names and removed after each request, including conversion failures. The browser upload is handled by the local server. This does not guarantee zero network egress from the selected parser or model; review engine and model behavior before processing sensitive files.

The default local engine is Docling:

```bash
pip install docling
```

### Optional Engines (Isolated)

```bash
# Marker (verify the exact package and model license terms before use)
pip install ".[marker]"

# MinerU (verify the exact package, model artifact, and deployment terms before use)
# Consult docs/LICENSE_AUDIT.md; install its CLI separately if appropriate.
```

### Private macOS Application Candidate

The self-contained Apple Silicon candidate uses the same browser workbench and
accepts only UTF-8 Markdown (`.md`, `.markdown`) and text (`.txt`), with Markdown
or HTML output. It excludes PDF/Office/OCR engines and model weights.

#### Use the local macOS candidate

The current ZIP is available on this Mac at:

`/Users/jakechiu/Documents/Projects/document_converter/build/private-release/candidate-3/Document-Converter-macos-arm64-local-candidate.zip`

This build artifact is local and is not included in the GitHub repository. To
start it, double-click the ZIP in Finder to extract it, then double-click
`Document Converter.app` in the extracted folder. The app starts a local service
and opens the workbench in your default browser. Select `.md`, `.markdown`, or
UTF-8 `.txt` files, choose Markdown or HTML, then start conversion. A single
result downloads as a file; multiple results download as a ZIP. Downloads
usually appear in the browser's Downloads folder.

Uploads and generated files are held in a temporary directory while that
conversion request is processed and are removed when the request finishes. The
browser's downloaded copy remains in its Downloads folder. Closing the browser
does not stop the app; quit **Document Converter** in Activity Monitor to stop
the local service.

The candidate is ad-hoc signed and not notarized. macOS may show a first-launch
security warning. Do not disable Gatekeeper to open it; use your organization's
approved app review process. This candidate is for Apple Silicon Macs only.

The frozen release integration check recorded 10 tests passing. The full project
suite recorded 111 tests passing with 83.56% coverage. Neither result verifies
Finder double-click behavior, installation on another Mac, or Windows support.
There is no Windows installer, and Windows use has not been tested.

See the [macOS build and local-use guide](docs-release/macos.md) and
[private distribution requirements](docs/PRIVATE_DISTRIBUTION.md). The candidate
is for local testing: it has ad-hoc signing, not Developer ID signing or Apple
notarization, and its manifest retains `distribution_ready: false`.

## 4. Usage

```bash
document-converter convert paper.pdf --to md
document-converter convert paper.pdf --to html
document-converter convert paper.pdf --to md --to html --images referenced
document-converter convert ./documents --to md --to html --output ./converted
```

Inspect engines:

```bash
document-converter list-engines
```

Force an engine:

```bash
document-converter convert paper.pdf --engine docling --to md --to html
document-converter convert paper.pdf --engine marker --to md
document-converter convert paper.pdf --engine mineru --to md
```

## 5. Architecture & Design

The converter uses a normalized conversion result internally. This keeps input parsing separate from rendering and makes it possible to add EPUB/DOCX/PDF parsers or future renderers without changing the CLI.

Docling is the primary backend because its current CLI/API supports a unified document representation and native Markdown/HTML output. Marker and MinerU are optional specialist fallbacks accessed through adapters; their package and model licenses require separate review.

---

## 6. Document Copyright & Legal Compliance

> [!IMPORTANT]
> **文件著作權與處理權限聲明 (Copyright & Ownership Notice)**
> 
> 1. 使用者在透過本工具轉換任何文件（包含 PDF、Office 文件、圖片或掃描文件）前，**必須確保自身擁有該文件的合法著作權、授權或合法處理與散布權利**。
> 2. 本專案**嚴格禁止**將任何客戶機密資料、商業真實文件、個人隱私資料或未經授權之受版權保護文件提交至版本控制庫（Git Repository）。
> 3. 本專案之自動化測試僅使用自製合成、公眾領域（Public Domain）或無敏感資訊之測試文件。

---

## 7. Security & Privacy Baseline

- **Local-first design**: The CLI is designed to process documents with locally installed engines. Network access by an engine, package, or model downloader has not been audited for every configuration; verify the selected engine and its settings before processing sensitive documents.
- **Logging**: The project CLI reports processing status and errors. Third-party engines may produce their own logs; logging behavior has not been exhaustively verified across engines and versions.
- **Secret & Sensitive Data Guard**: `.gitignore` includes patterns for common outputs, credentials, temporary assets, and model caches. Review the ignore rules and `git status` before each commit; ignore rules do not remove files already tracked.
- **Repository visibility**: The intended development posture is private. Confirm actual visibility in GitHub settings. Private visibility does not replace license, privacy, or distribution review.

---

## 8. Third-Party Licenses

Third-party package and model review status:
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- [docs/LICENSE_AUDIT.md](docs/LICENSE_AUDIT.md)

## 9. Project License

Copyright (c) 2026 Jake Chiu. The project's own software uses the
[proprietary use license](LICENSE): personal and internal organizational use,
including internal commercial use, is permitted; resale and external
redistribution of the project's own software are restricted. This is not an MIT
license. Third-party components retain their respective licenses and statutory
rights remain unaffected. Read the full license before distributing a copy.
