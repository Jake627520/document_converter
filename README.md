# Document Converter Skill

A local-first document conversion CLI and Codex/agent Skill.

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

## 4. Usage

```bash
document-converter paper.pdf --to md
document-converter paper.pdf --to html
document-converter paper.pdf --to md html --images referenced
document-converter ./documents --to md html --output ./converted
```

Inspect engines:

```bash
document-converter --list-engines
```

Force an engine:

```bash
document-converter paper.pdf --engine docling --to md html
document-converter paper.pdf --engine marker --to md
document-converter paper.pdf --engine mineru --to md
```

## 5. Architecture & Design

The converter uses a normalized conversion result internally. This keeps input parsing separate from rendering and makes it possible to add EPUB/DOCX/PDF parsers or future renderers without changing the CLI.

Docling is the primary backend because its current CLI/API supports a unified document representation and native Markdown/HTML output. Marker and MinerU are optional specialist fallbacks and are strictly isolated behind adapters.

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
