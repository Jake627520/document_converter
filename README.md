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
# Marker (Note: GPL-3.0 License restrictions)
pip install ".[marker]"

# MinerU (Note: AGPL-3.0 and Non-commercial model weights)
# Follow MinerU official guidelines to install the CLI on your system PATH
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

- **Local-First & Zero Network Leakage**: 本專案所有轉換作業預設完全於本機環境執行。未經使用者明確指定與授權，**絕不向任何第三方雲端 AI API、外部 LLM 或遠端伺服器傳送文件內容**。
- **No Document Content in Logs**: CLI 與各解析引擎之日誌輸出**僅記錄處理狀態、檔案路徑與錯誤診斷**，絕不將原始文件內容、解析全文或 OCR 提取結果傾印（dump）至系統日誌。
- **Secret & Sensitive Data Guard**: `.gitignore` 預設嚴密排除所有輸出目錄 (`converted/`, `outputs/`)、輸入目錄、暫存資產、憑證 (`.env*`, `*.pem`, `*.key`) 與模型快取。
- **Repository Policy**: 本專案在開發與測試階段**維持 Private 狀態**。在公開發布前必須完成完整的 Secret Scan 與 License Audit。

---

## 8. Third-Party Licenses

詳細第三方套件與模型授權審查請參閱：
- [THIRD_PARTY_NOTICES.md](file:///Users/jakechiu/Documents/Projects/document_converter/THIRD_PARTY_NOTICES.md)
- [docs/LICENSE_AUDIT.md](file:///Users/jakechiu/Documents/Projects/document_converter/docs/LICENSE_AUDIT.md)
