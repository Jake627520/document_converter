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

### PDF Without PyTorch (`docling-native`)

Docling's default PDF pipeline runs layout and table models: it needs PyTorch
(a multi-gigabyte install) and downloads model weights from huggingface.co on
first use. The `docling-native` engine uses Docling's model-free
`NativePdfPipeline` instead, which reads the text and bitmaps the PDF already
contains and runs no models, so it works offline from a much smaller install:

```bash
# instead of pip install -e . , which pulls docling and PyTorch
pip install "docling-slim[convert-core,format-pdf]" typer rich pypdf
pip install -e . --no-deps
```

That install is roughly 0.4 GB and contains no PyTorch. `--engine auto` also
works there: the model-based engines fail to load and the model-free reader
converts the file.

It converts PDF only, and it reconstructs no structure: no heading levels, no
Markdown tables, no reading-order recovery and no OCR, so a scanned page yields
no text. Every conversion records that limitation as a warning. `auto` keeps it
last, so model-based engines are preferred wherever they are installed.

```bash
document-converter convert paper.pdf --engine docling-native --to md --to html
```

### Optional Engines (Isolated)

```bash
# Marker (verify the exact package and model license terms before use)
pip install ".[marker]"

# MinerU (verify the exact package, model artifact, and deployment terms before use)
# Consult docs/LICENSE_AUDIT.md; install its CLI separately if appropriate.
```

### Private macOS Application Candidate (Two Profiles)

兩個已審查的發行設定檔：`text` 只收 `.md`/`.markdown`/`.txt`（原本的版本，不含任何引擎與
模型）；`pdf` 另外收**有文字層的 PDF**，用不需模型的讀取器轉換（沒有 OCR、不重建標題與表格、
不含 PyTorch、不下載模型，掃描檔會明確告知沒有文字層）。建置與驗收指令見
[macOS 建置與本機使用指南](docs-release/macos.md)。

### Private macOS Application Candidate

這是給一般使用者直接開啟的 macOS 候選 App。它只支援 Apple Silicon
（M 系列晶片）Mac，將 UTF-8 編碼的 `.md`、`.markdown`、`.txt` 文件轉成
Markdown 或 HTML。它不支援 PDF、Office 文件、圖片、OCR，也不包含模型。

#### 一般使用者：下載並啟動 App

目前的 ZIP 與 `.app` 都只存在建置它的這台 Mac，**沒有上傳到 GitHub**。
檔案位置如下：

- ZIP：`/Users/jakechiu/Documents/Projects/document_converter/build/private-release/candidate-3/Document-Converter-macos-arm64-local-candidate.zip`
- 解壓後的 App：`/Users/jakechiu/Documents/Projects/document_converter/build/private-release/candidate-3/Document-Converter-macos-arm64-local-candidate/Document Converter.app`

照下面步驟操作：

1. 在 Finder 按 `Command + Shift + G`，貼上上方 ZIP 路徑所在的資料夾：
   `/Users/jakechiu/Documents/Projects/document_converter/build/private-release/candidate-3/`，再按 Enter。
2. 在 Finder 雙擊 `Document-Converter-macos-arm64-local-candidate.zip` 解壓縮。
3. 打開解壓後的 `Document-Converter-macos-arm64-local-candidate` 資料夾，找到
   `Document Converter.app`。它的完整路徑如上方所列。
4. 雙擊 `Document Converter.app`。設計上 App 會啟動本機服務，並用預設瀏覽器開啟操作頁面；Finder 雙擊啟動尚未驗證。
5. 在網頁選取或拖入最多 **5 個** `.md`、`.markdown` 或 `.txt` 檔案。檔案必須是 UTF-8 編碼；單一檔案及全部選取檔案合計不得超過 **24 MiB**，整個上傳請求上限為 **25 MiB**。
6. 選擇輸出為 Markdown 或 HTML，按「開始轉換」。一份文件會下載成單一檔案，多份文件會下載成 ZIP。下載位置通常是瀏覽器的「下載項目」（Downloads）資料夾。
7. 上傳檔案和轉換中的輸出會放在系統暫存資料夾；每次轉換完成後會清除。瀏覽器下載的成品會保留在「下載項目」。關閉瀏覽器不會停止 App；要停止服務，請打開「活動監視器」，搜尋並退出 `Document Converter`。

**一般使用者不需要安裝 Node.js、Docker、VS Code、Python 或 pip。**只需要這份
App、一台 Apple Silicon Mac，以及可用的瀏覽器。VS Code 是編輯程式碼時可選用的
工具，不是執行 App 的必要條件。

此候選 App 只有 ad-hoc 簽章，沒有 Developer ID 簽章或 Apple 公證；macOS
首次開啟時可能顯示安全性提示。請勿停用 Gatekeeper；如遇提示，請依組織核准的
App 審查流程處理。此 App 只提供 Apple Silicon macOS；**Windows 沒有安裝包，
也尚未測試**。Finder 雙擊啟動、其他 Mac 安裝與首次安全提示處理均未驗證。

#### 開發者：從原始碼執行

以下是開發者流程，**一般使用者不需要執行**。從原始碼安裝需要 Python
（版本 `3.11` 至 `3.14`）與 pip；啟動瀏覽器介面還要安裝 web 依賴：

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[web]"
document-converter web
```

Windows 上述指令只說明原始碼環境的設定方式，不代表 Windows 已完成測試或有
安裝包。要重新打包 macOS App，請參閱[macOS 建置與本機使用指南](docs-release/macos.md)。
另可查看[私人發行要求](docs/PRIVATE_DISTRIBUTION.md)。目前候選包只供本機測試，
發行狀態仍為 `distribution_ready: false`。

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
document-converter convert paper.pdf --engine docling-native --to md   # no PyTorch, no model download
document-converter convert paper.pdf --engine marker --to md
document-converter convert paper.pdf --engine mineru --to md
```

Clean up Markdown noise:

```bash
document-converter convert paper.pdf --to md --clean
document-converter convert paper.pdf --to md --clean --strip-page-numbers
```

`--clean` removes labelled page markers such as `Page 3 of 12`, `4 / 20` and
`- 5 -`. It keeps a line that holds only digits, because engines emit table
cells and other document values on their own line; add `--strip-page-numbers`
when a document's page numbers survive as bare numerals and you accept that
standalone numeric values are removed with them.

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
