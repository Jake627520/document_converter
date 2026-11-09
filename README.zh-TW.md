# Document Converter 文件轉換工具

[English](README.md) | **繁體中文** | [简体中文](README.zh-CN.md)

本機優先的文件轉換工具：包含命令列工具、在你自己電腦上執行的瀏覽器工作台、
打包好的 macOS App，以及給 Codex 與 Claude 使用的 agent 技能（[`SKILL.md`](SKILL.md)）。
文件都在你的電腦上轉換，不會上傳到任何遠端服務。

這個專案怎麼做出來的，以及十個「看起來沒問題、查了才知道有問題」的缺陷：
見[案例研究](docs/case-study/README.zh-TW.md)。

---

## 1. 可以轉換什麼

**輸入格式。** 一個安裝能接受什麼，取決於它裝了哪些引擎。

| 輸入 | 從原始碼執行（已裝 Docling） | macOS App `text` 版 | macOS App `pdf` 版 | macOS App `office-ocr` 版 |
|---|---|---|---|---|
| Markdown `.md` `.markdown` | ✅ | ✅ | ✅ | ✅ |
| UTF-8 文字 `.txt` | ✅ | ✅ | ✅ | ✅ |
| **有文字層的** PDF | ✅ | ❌ | ✅ | ✅ |
| **掃描或拍照的** PDF | ✅ 需 OCR：Docling 的模型（第一次使用時下載），或在 Mac 上裝 `apple-vision` extra | ❌ | ❌ | ✅ macOS 內建 OCR |
| Office `.docx` `.pptx` `.xlsx` 及舊格式 | ✅（`.docx` `.pptx` `.xlsx` 只裝 `office` extra 也行，不需 PyTorch） | ❌ | ❌ | ✅ 僅 `.docx` `.pptx` `.xlsx` |
| `.html` `.htm` `.epub` `.csv` `.rtf` OpenDocument | ✅ | ❌ | ❌ | ❌ |
| 圖片 `.png` `.jpg` `.jpeg` `.webp` | ✅ 需 OCR，與掃描檔相同 | ❌ | ❌ | ✅ macOS 內建 OCR |

不支援的檔案會在轉換開始前就被拒絕，而且訊息會告訴你**哪些格式可以**。
例如在 `pdf` 版 App 上傳 Word 檔，你會看到：

> 這個版本不支援「.docx」檔案。可以轉換的格式：.markdown、.md、.pdf、.txt。

**文字檔必須是 UTF-8 編碼。** Big5、GBK 或 UTF-16 的檔案會被明確拒絕，
並告訴你先另存為 UTF-8 —— 它不會把檔案轉成亂碼：

> 「規格.txt」不是 UTF-8 編碼的文字檔（常見的是 Big5、GBK 或 UTF-16）。請先用文字編輯器另存為 UTF-8 再轉換。

**數量與大小限制。** 網頁與 macOS app 一次最多 5 個檔案，單一檔案與全部合計各不超過 24 MiB（約 25 MB），
整個請求上限 25 MiB（約 26 MB）。1 MiB 是 1,048,576 bytes，而 Finder 顯示的 1 MB 是
1,000,000 bytes，所以 Finder 顯示 25.1 MB 的檔案仍可上傳。CLI 沒有大小或檔案數量限制。

**絕不會給你空檔案。** 如果轉換抽不出任何文字 —— 沒有文字層的掃描檔、
整頁都是圖片、或檔案本身是空的 —— 系統會明確說明原因，
而不是讓你下載一個 0 bytes 的檔案。

**輸出格式。**

| 輸出 | 從原始碼執行（CLI 與瀏覽器） | macOS App `text` 版 | macOS App `pdf` 版 | macOS App `office-ocr` 版 |
|---|---|---|---|---|
| Markdown（`.md`） | ✅ | ✅ | ✅ | ✅ |
| HTML（`.html`） | ✅ | ✅ | ✅ | ✅ |
| 純文字（`.txt`） | ✅ | ✅ | ✅ | ✅ |
| Docling JSON（`.json`） | ✅ 檔案經 Docling 引擎解析時 | — | ✅ 僅限 PDF 輸入 | ✅ Office 檔與有文字層的 PDF |

Docling JSON 是引擎對文件結構的解析結果，所以只有經過引擎讀取的檔案才有。
Markdown 與文字檔是直接讀取的，而 `text` 版 App 完全不含引擎。

## 2. macOS App

只支援 Apple Silicon（M 系列晶片）的 Mac。共有三個已審查的設定檔：

| 設定檔 | 接受的檔案 | 內含 |
|---|---|---|
| `text` | UTF-8 編碼的 `.md`、`.markdown`、`.txt` | 不含任何文件引擎與模型 |
| `pdf` | 上述格式，再加上**已有文字層的 PDF** | Docling 不需模型的 PDF 讀取器 —— 沒有 OCR、沒有 AI 模型、沒有 PyTorch，也不會下載任何東西 |
| `office-ocr` | 上述格式，再加上 Word、PowerPoint、Excel（`.docx`、`.pptx`、`.xlsx`）、**掃描的 PDF** 與圖片（`.png`、`.jpg`、`.jpeg`、`.webp`） | `pdf` 版的內容，加上 Docling 的 Office 讀取器與 PyObjC（用來呼叫 macOS 內建的文字辨識）—— 沒有 OCR 引擎、沒有 AI 模型、沒有 PyTorch，也不會下載任何東西 |

`pdf` 版只抽取 PDF 裡原本就有的文字，不會重建標題階層或表格。掃描的 PDF 沒有文字層，
App 會明確告訴你，而不是給你一個空白檔案。`text` 與 `pdf` 版都不接受 Office 文件與圖片。

`office-ocr` 版會先讀 PDF 的文字層；只有圖片的 PDF 與圖片檔，交給 macOS 內建的文字辨識
（Apple 的 Vision 框架，也就是「照片」App 能選取圖中文字的那套辨識器）。辨識結果只有段落，
不還原標題階層與表格，網頁也會提醒你核對。同一份 PDF 若有文字頁也有掃描頁，只會讀文字層，掃描頁不會被辨識。Word、PowerPoint、Excel 會保留標題、清單與表格。
舊版 `.doc`、`.ppt`、`.xls` 不接受。

### 開啟 App

- **你自己建置的 App**：直接雙擊就能開啟。macOS 只會攔下從網路上取得的檔案。
- **別人傳給你的 App**（下載、AirDrop 或透過通訊軟體傳送）：第一次開啟會被擋下，
  因為候選包只有 ad-hoc 簽章，沒有 Developer ID 簽章，也沒有經過 Apple 公證。
  從 macOS 15 開始，「按右鍵 › 打開」已經無法繞過這個阻擋。請先嘗試開啟 App 一次，
  再到**系統設定 › 隱私權與安全性**，在「安全性」區塊找到這個 App，
  按下**仍要打開**並輸入管理者密碼。

請不要為了繞過這一步而關閉 Gatekeeper。

### 使用方式

1. 雙擊 `Document Converter.app`。它會啟動本機服務，並用預設瀏覽器開啟
   `http://127.0.0.1:<port>`。
2. 拖入或選取最多 **5 個**檔案。單一檔案與全部選取的檔案合計，各不得超過 **24 MiB（約 25 MB）**。
3. 選擇輸出格式，按下**開始轉換**。一份文件會下載成單一檔案，多份文件會下載成 ZIP。
   下載的檔案會以原始文件的名稱命名，中文檔名也可以。
4. 上傳的檔案會以系統產生的名稱暫存在系統暫存資料夾，每次轉換完成後就會刪除。
5. 關閉瀏覽器不會停止 App。要結束它，請開啟**活動監視器**，找到 `Document Converter` 並結束。

執行 App 不需要安裝 Python、Node.js、Docker 或 VS Code。

### 驗證狀態

| | |
|---|---|
| ✅ 已在 Apple Silicon Mac 上驗證（2026-10-12／13） | `pdf` 候選包已完成建置、ad-hoc 簽章與壓縮；能像一般 App 一樣開啟並轉換真實文件；凍結後的執行環境回報沒有載入任何禁止的模組；內含 124 個第三方授權聲明檔 |
| ✅ 已重新建置並檢查（2026-11-08，macOS 27.2） | `pdf` 候選包由 `ccd843d` 建置，內含 Pillow 13.0.0，具備純文字、Docling JSON 輸出與下載檔名功能；9 項 release 測試通過；`--diagnostics` 顯示 `pdf-text`、沒有載入禁用模組；`pip-audit` 在固定版本中找不到已知漏洞；凍結後的 App 在不開瀏覽器的模式下，把中文檔名的文字層 PDF 轉成純文字與 JSON 並沿用原檔名、兩個檔案以 ZIP 回傳、拒絕 `.docx`、對掃描檔說明原因。尚未經 Finder 開啟 |
| ⏳ 尚未建置 | `office-ocr` 候選包。CI 在 Apple Silicon runner 上安裝它鎖定的 macOS 套件，以未凍結的方式執行，並用真正的 Vision 讀回一張含英文與繁體中文的圖片；凍結成 App 需要固定的 Python build，要在擁有者的 Mac 上做 |
| ⏳ 尚未驗證 | 安裝到第二台 Mac —— [`docs-release/macos-vm-verification.md`](docs-release/macos-vm-verification.md) 說明如何用免費的 macOS 虛擬機驗證 |
| ➖ 不打算做 | Developer ID 簽章與 Apple 公證 —— 擁有者於 2026-10-29 決定維持 ad-hoc 簽章，因為 App 不上架 App Store，收件者也很少（[ROADMAP](docs/ROADMAP.md)）；收件者依上方步驟開啟一次即可，每個候選包仍標記為 `distribution_ready: false` |
| ❌ 不提供 | Windows App —— 沒有安裝包；在 Windows 上從原始碼執行，見下方說明 |

### 自行建置

```sh
RELEASE_PROFILE=pdf BUILD_PYTHON="$HOME/.local/bin/python3.12" \
  sh scripts/packaging/bootstrap_macos.sh --output-dir build/private-release/candidate-pdf
```

改成 `RELEASE_PROFILE=office-ocr`（並換一個輸出目錄）就是建置 `office-ocr` 版；拿掉 `RELEASE_PROFILE` 就是建置 `text` 版。完整的建置與驗收流程請見
[`docs-release/macos.md`](docs-release/macos.md)。

## 3. 從原始碼執行（開發者）

支援 Python 3.11 到 3.14；CI 測試 3.11 與 3.12。

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

如果 `python -m venv` 失敗，表示這個 Python 缺少 venv 模組。在 Debian 或 Ubuntu 上，
用 `sudo apt install python3-venv` 安裝後再執行一次。或改用
[uv](https://docs.astral.sh/uv/) 建立環境，它不需要這個模組；之後把下面的 `pip`
換成 `uv pip`：

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e .
```

不要用 `pip install --user`：較新的 Linux 發行版會在虛擬環境外拒絕它（PEP 668），
而且它會把這個專案的套件混進你的使用者目錄。

依需求選擇安裝層級：

- **最小安裝**（僅 UTF-8 Markdown / 純文字 + CLI + PDF inspect 偵測）：
  ```bash
  pip install -e .
  ```
  未安裝 Docling 時，`.md` 與 `.txt` 仍可正常轉換；PDF/Office 會在 `list-engines` 顯示 `not detected`，在執行 `convert` 時給出引擎不可用錯誤，而不是安裝失敗。

- **常用安裝**（含 Docling，可轉換 PDF/Office 等格式）：
  ```bash
  pip install -e ".[docling]"
  ```

- **瀏覽器工作台**：
  ```bash
  pip install -e ".[web]"
  # 或連同 Docling：
  pip install -e ".[docling,web]"
  ```

- **完整安裝**（Docling + 瀏覽器工作台）：
  ```bash
  pip install -e ".[full]"
  ```

- **不需 PyTorch 的 Office 轉換**（透過 Docling 的讀取器轉 `.docx`、`.pptx`、`.xlsx`，約 0.4 GB，不用模型）：
  ```bash
  pip install -e ".[office]"
  ```

- **Mac 上不用下載任何東西的 OCR**（用 macOS 內建的文字辨識讀掃描 PDF 與照片）：
  ```bash
  pip install -e ".[apple-vision]"
  ```

Windows 上的原始碼安裝已在 CI 驗證：CI 在 `windows-latest`（Python 3.12）安裝 web extra，整套測試通過。Markdown 與純文字的轉換，以及瀏覽器工作台，都能在 Windows 上使用。另一個 job 加裝 `docling` extra，測試全數通過、沒有任何 skip，所以有文字層的 PDF 也能在 Windows 上轉換。CI 不下載 Docling 模型，所以模型流程（版面、表格、OCR）尚未在 Windows 上驗證。

在 Windows 上，`docling-native` 不會把頁面畫成圖片：Docling 的頁面渲染器在 Windows 上，背景執行緒結束時會弄壞記憶體（[docling-parse #357](https://github.com/docling-project/docling-parse/issues/357)），造成轉換隨機當機。文字、Markdown 與 HTML 的結果不變，只是 Docling JSON 裡沒有每一頁的縮圖。Docling 的模型流程需要這些頁面圖片，所以仍會渲染，在 docling-parse 修好之前仍有這個風險。

### 瀏覽器工作台

```bash
document-converter web             # http://127.0.0.1:8765 ; --port 8766 for another port
```

伺服器只綁定本機回環位址（loopback）。限制與 App 相同：最多五個檔案、單檔與合計
各 24 MiB（約 25 MB）、單次請求 25 MiB（約 26 MB）。它使用與 CLI 相同的 `auto` 引擎選擇，所以會用到已安裝的
任何引擎（包括 Marker 與 MinerU），但不會替你安裝任何引擎。

### 命令列

```bash
document-converter convert paper.pdf --to md
document-converter convert paper.pdf --to md --to html --to json --to txt
document-converter convert ./documents --to md --output ./converted
document-converter list-engines
```

指定引擎：

```bash
document-converter convert paper.pdf --engine docling --to md
document-converter convert paper.pdf --engine docling-native --to md   # no PyTorch, no model download
document-converter convert report.docx --engine docling-office --to md  # Word/PowerPoint/Excel，不用模型
document-converter convert scan.pdf --engine apple-vision --to md       # macOS 內建 OCR
document-converter convert paper.pdf --engine marker --to md
document-converter convert paper.pdf --engine mineru --to md
```

清除 Markdown 雜訊：

```bash
document-converter convert paper.pdf --to md --clean
document-converter convert paper.pdf --to md --clean --strip-page-numbers
```

`--clean` 會移除有標示的頁碼，例如 `Page 3 of 12`、`4 / 20` 與 `- 5 -`。
只有數字的那一行會保留，因為引擎常把表格儲存格和其他數值單獨放一行；
只有在文件的頁碼以單獨數字殘留、而且你接受連帶刪掉單獨數值時，才加上 `--strip-page-numbers`。

### 平行批次轉換

```bash
document-converter convert ./documents --to md --output ./converted --parallel 4
```

- 預設 1 個 worker，安全上限為 4。
- 適合一次轉換**多個檔案**（目錄或批次輸入）。
- **單一大型 PDF** 通常加速有限：時間主要花在轉換引擎；行程內引擎還受 Python GIL 限制。
- 單一檔案失敗不會中止整批其餘檔案。

### 不需 PyTorch 的 PDF 轉換（`docling-native`）

Docling 預設的 PDF 流程會執行版面與表格模型：需要安裝好幾 GB 的 PyTorch，
並在第一次使用時下載模型權重。`docling-native` 改用 Docling 不需模型的 `NativePdfPipeline`：

```bash
pip install "docling-slim[convert-core,format-pdf]" typer rich pypdf
pip install -e . --no-deps
```

這樣安裝約 0.4 GB。它只轉換 PDF，不重建文件結構、不做 OCR，每次轉換都會以警告記錄這項限制。
`auto` 會把它排在最後，所以有安裝模型版引擎時會優先使用模型版。

### 不需 PyTorch 的 Office 轉換（`docling-office`）

Word、PowerPoint、Excel 檔案完全不需要模型：Docling 用 python-docx、python-pptx 與
openpyxl 讀取，保留標題、清單與表格。`docling-office` 把 Docling 限定在這三種格式，
所以絕不會走到需要模型權重的流程。用 `pip install -e ".[office]"` 安裝；沒有裝完整版
Docling 時，`auto` 會用它。文件裡的圖片仍保留為圖片，不會讀出圖中的文字。

### OCR（文字辨識）

掃描檔和照片裡沒有可以直接取出的文字，必須「辨識」出來。支援兩種方式，`auto` 會用已安裝的那一種：

| | Docling 的模型 | `apple-vision` |
|---|---|---|
| 安裝 | `pip install -e ".[docling]"` | `pip install -e ".[apple-vision]"` |
| 可用平台 | macOS、Linux、Windows | 只有 macOS |
| 需要下載 | 第一次使用時下載版面模型（Hugging Face）與 OCR 模型（RapidOCR） | 不用：辨識器是 macOS 內建的 |
| 輸出 | 標題、表格與閱讀順序 | 只有段落 |
| 語言 | RapidOCR 的中英文模型 | 繁體中文、簡體中文、英文 |

`apple-vision` 使用 Apple 的 Vision 框架，也就是「照片」App 能選取圖中文字的那套辨識器。
它把 PDF 每一頁以 300 dpi 轉成圖片後辨識，再依行與行之間的距離組回段落。
每次轉換都會附上警告，提醒文字是辨識出來的、使用前請核對。CI 兩種都驗證：
一頁畫上英文與繁體中文的頁面，分別由 Linux 上的 Docling 模型與 Apple Silicon Mac 上的 Vision 讀回。

### 選用引擎

```bash
pip install ".[marker]"   # check the package and model license terms first
pip install ".[mineru]"   # MinerU 4.x; read docs/LICENSE_AUDIT.md first
```

`mineru` 選用套件會安裝 MinerU 4.x，它會帶進 PyTorch，並從 Hugging Face 或
ModelScope 下載模型檔（`mineru-models-download`）。本專案只執行 `mineru-kit parse`，
在你的電腦上轉換，從不使用 MinerU 的遠端服務選項。MinerU 的另一個指令 `mineru`
會為 mineru.net 收集使用數據：第一次執行時會詢問，預設為「是」；
執行 `mineru telemetry disable` 可以關閉。

## 4. 運作原理

每個引擎都產生同一種標準化的轉換結果，再由 writer 轉成你要的輸出格式。
解析與輸出彼此分離，所以新增輸入或輸出格式時不必修改 CLI。
引擎都透過 `document_converter/engines/` 裡的轉接層（adapter）接入；輸出序列化集中在 `writer.py`。

### 用到哪些技術

本專案自己寫的是：操作介面、引擎選擇邏輯、掃描檔偵測、Markdown 清理器、
HTML 轉譯器，以及打包流程。**實際的文件解析由下列元件完成**：

| 用途 | 元件 | 授權 | 是否打包進 macOS App |
|---|---|---|---|
| PDF 讀取（不跑模型） | **Docling** `docling-slim`、`docling-core`、`docling-parse` | MIT | ✅ `pdf`、`office-ocr` 版 |
| Docling 底層的 PDF 解析 | **pypdfium2** 與 Google 的 **PDFium** | BSD-3-Clause / Apache-2.0 | ✅ `pdf`、`office-ocr` 版 |
| 瀏覽器介面 | **FastAPI**、**Starlette**、**Uvicorn** | MIT / BSD | ✅ 三版 |
| 命令列介面 | **Typer**、**Rich** | MIT | — App 沒有命令列 |
| 掃描檔偵測 | **pypdf**，沒有時改用內建的串流分析器 | BSD-3-Clause | — App 直接讀文字層 |
| 打包成 App | **PyInstaller** | GPL-2.0-or-later，**附 Bootloader 例外條款** | ✅ 僅啟動器 |
| 含版面與表格模型的 PDF 流程 | Docling 的模型流程，需 **PyTorch** 並下載模型權重 | 程式碼 MIT，模型條款另計 | ❌ |
| Office 讀取（不跑模型） | 透過 Docling 使用 **python-docx**、**python-pptx**、**openpyxl** | MIT | ✅ `office-ocr` 版 |
| Docling 模型流程中的 OCR | **RapidOCR** 與 PaddleOCR 模型，由 **ONNX Runtime** 執行 | Apache-2.0 / MIT | ❌ |
| macOS 上的 OCR | Apple 的 **Vision** 框架，透過 **PyObjC** 呼叫 | macOS 內建 / MIT | ✅ `office-ocr` 版含 PyObjC；Vision 是 macOS 內建的 |
| 其他 PDF／OCR 引擎 | **Marker**、**MinerU** | 程式碼 Apache-2.0；模型與附加條款另計 | ❌ |

**OCR：本專案沒有附帶任何 OCR。** 所有 macOS 版本都不含任何 OCR 引擎或模型。
`text` 與 `pdf` 版會把掃描檔明確回報為「沒有文字層」，而不是硬猜內容；
`office-ocr` 版透過 PyObjC 使用 macOS 本來就有的辨識器。
從原始碼安裝時，OCR 來自 Docling 的模型流程、`apple-vision`（使用 macOS 本來就有的辨識器），
或你自己安裝的 Marker、MinerU（受它們自己的條款約束）——
查證紀錄見 [`docs/LICENSE_AUDIT.md`](docs/LICENSE_AUDIT.md)。

### Fork 自己跑：SOP

這個倉庫公開是為了讓人閱讀與執行。它**不是開源**（見第 8 節）：
fork 來閱讀、研究、執行都沒問題，但不得重新發布或販售本專案自有的軟體。

```bash
# 1. 在 GitHub 上 fork，然後 clone 你的 fork
git clone https://github.com/<你的帳號>/document_converter.git
cd document_converter

# 2. Python 3.11 到 3.14
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip

# 3. 只要 Markdown 與文字：不含引擎，安裝量最小
pip install -e ".[web]"

# 4. 加上 PDF 但不要 PyTorch：約 0.4 GB，不下載任何模型
pip install "docling-slim[convert-core,format-pdf]"

#    或改成含版面與表格模型的 PDF：數 GB，會下載模型權重
#    pip install docling

# 5. 確認實際裝到什麼，再啟動瀏覽器介面
document-converter list-engines
document-converter web
```

`list-engines` 會印出**這個安裝實際擁有的引擎**，所以第 5 步告訴你的是真實情況，
而不是文件上的理想情況。

要跑本專案對自己做的那套檢查：

```bash
pip install -e ".[dev,web]"
python -m pytest
document-converter --help
document-converter list-engines
python3 scripts/packaging/audit_notices.py --profile pdf   # 需要網路
```

打包 macOS App 需要 Apple Silicon Mac，流程見
[`docs-release/macos.md`](docs-release/macos.md)。

## 5. 你的文件

> [!IMPORTANT]
> 1. 轉換任何文件（PDF、Office 文件、圖片或掃描檔）之前，請確認你有權處理該文件，
>    必要時也有權散布。
> 2. 請勿將客戶機密資料、真實商業文件、個人資料或未經授權的受著作權保護文件提交到本 repository。
> 3. 自動化測試只使用自行合成、屬於公眾領域或不含敏感資訊的文件。

## 6. 安全與隱私

- **本機優先。** 文件由本機安裝的引擎處理。並非每一種引擎、套件與模型下載器的組合
  都經過網路行為稽核；處理敏感檔案前，請先確認你選用的引擎。
- **上傳檔案。** 以系統產生的名稱暫存，每次請求結束後刪除，轉換失敗也一樣。
- **日誌。** CLI 會回報處理狀態與錯誤。第三方引擎可能會自行記錄日誌。
- **敏感檔案。** `.gitignore` 已涵蓋常見的輸出檔、憑證、暫存素材與模型快取，
  但它不會移除已經被追蹤的檔案；每次 commit 前請先檢查 `git status`。

## 7. 支援

這是個人專案，公開是為了讓人閱讀與使用。它以現狀提供，**不承諾支援、不承諾回答問題、
不承諾修復問題，也不承諾持續維護**。Issue 與 pull request 可能不會得到回覆。
處理重要文件前請先檢查輸出結果：各引擎的限制在上面都有說明，每次轉換也都會記錄成警告。

## 8. 授權

**本專案。** Copyright (c) 2026 Jake Chiu，採用[專有使用授權](LICENSE)：
允許個人使用及公司內部使用（包含內部商業用途）；不得轉售或散布本專案自有的軟體。
這不是開源授權，**本倉庫公開也不會使它變成開源**：在這裡讀得到原始碼，
並不因此取得 `LICENSE` 沒有授予的任何權利。

**第三方元件**各自保有原本的授權，本專案的任何內容都不限制原作者授予的權利。
請見 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 與
[`docs/LICENSE_AUDIT.md`](docs/LICENSE_AUDIT.md)。每個安裝包的 `legal/` 資料夾
都附有所有元件的授權與聲明原文。

macOS App 的 `pdf` 版包含部分基於 FreeType Team 及 Independent JPEG Group 成果的軟體。

> 本頁為翻譯，僅供參考。授權條款以英文 [`LICENSE`](LICENSE) 為準；
> 第三方授權以 `THIRD_PARTY_NOTICES.md`、`docs/` 內文件及各元件授權原文為準。
