# macOS 候選包（文字版／PDF 版）

本專案有兩個已審查的發行設定檔（profile）：

| profile | 接受的輸入 | 打包內容 | 約略大小 |
|---|---|---|---|
| `text`（原本的版本） | `.md`、`.markdown`、`.txt` | 不含任何文件引擎或模型 | 數十 MB |
| `pdf`（新增） | 上述再加上**有文字層的 `.pdf`** | 另含 Docling 不跑模型的 PDF 讀取器 | 數百 MB |

`pdf` profile 的 PDF 轉檔只抽取 PDF 內既有的文字：**沒有 OCR、不重建標題階層與表格**，
掃描檔會明確回報「沒有文字層」而不是給你一個空檔案。它不含 PyTorch，也不下載模型。
Office 與圖片格式兩個 profile 都不接受。

```sh
# 文字版（預設，與原本相同）
BUILD_PYTHON="$HOME/.local/bin/python3.12" sh scripts/packaging/bootstrap_macos.sh \
    --output-dir build/private-release/candidate-text

# PDF 版
RELEASE_PROFILE=pdf BUILD_PYTHON="$HOME/.local/bin/python3.12" sh scripts/packaging/bootstrap_macos.sh \
    --output-dir build/private-release/candidate-pdf
```

`RELEASE_PROFILE=pdf` 會建立獨立的 `build/private-release/venv-pdf`，並從
`scripts/packaging/requirements-macos-arm64-pdf.lock` 安裝 60 個 hash 鎖定的 wheel。
該 lock 由 PyPI metadata 針對 CPython 3.12 / macOS arm64 產生；若 `uv pip sync` 回報
hash 不符，請在 Mac 上重新產生（指令寫在 lock 檔開頭）。

建置後的驗收：

```sh
build/private-release/venv-pdf/bin/python -I -m unittest discover -s tests -p test_release_packaging.py -v
"build/private-release/candidate-pdf/Document-Converter-macos-arm64-pdf-local-candidate/Document Converter.app/Contents/MacOS/Document Converter" --diagnostics
```

`--diagnostics` 應顯示 `"profile": "pdf-text"`、`inputs` 含 `.pdf`、`forbidden_loaded` 為空。

**尚未在 Mac 上驗證。** PDF profile 的程式與打包設定已在 Linux 上以等效的 PyInstaller
凍結建置驗證過（凍結後可轉中文與英文文字層 PDF、掃描檔回報 422、Markdown 正常、docx 被擋、
多檔輸出 ZIP），但 macOS arm64 的 `.app`、codesign、Finder 雙擊與 ZIP 產出都還沒跑過。

---

# macOS 文字版候選包

本流程建立 Apple Silicon（arm64）的本機測試 `.app` 與 ZIP。沿用 `web_app.py` 的 FastAPI UI、請求限制與 writer；發行入口固定使用文字版，只接受 UTF-8 `.md`、`.markdown`、`.txt`，輸出 Markdown 或 HTML。不提供 PDF、OCR、Office、圖片或模型下載。

## 建置

固定平台為 CPython 3.12.13、python-build-standalone build 20260623、aarch64-apple-darwin。已在 macOS 26.6.2 檢查。使用其他 Python build 會被拒絕，須重新取得對應原始 notices、更新 provenance 並驗收。只驗證本機平台；Intel、Windows、其他 macOS 版本及跨機安裝尚未驗證。

先確認根 `LICENSE`、`THIRD_PARTY_NOTICES.md` 與 `docs/LICENSE_AUDIT.md`、`docs/PRIVATE_DISTRIBUTION.md` 已完成。缺任何文件直接停止；權利人與使用範圍應由使用者確認。

```sh
BUILD_PYTHON="$HOME/.local/bin/python3.12" sh scripts/packaging/bootstrap_macos.sh
```

bootstrap 只重建 `build/private-release/venv`，不使用現有 `.venv`。`uv pip sync` 從官方 PyPI 安裝 hash lock 內列出的 binary wheels，禁止 system site-packages。21 項依賴分為 FastAPI／Uvicorn／multipart 的 runtime 套件與 PyInstaller 的 build tools；未安裝 dev/test、Docling、PyMuPDF、Marker、MinerU 或模型。

不需再下載依賴時，可在該隔離環境執行：

```sh
build/private-release/venv/bin/python -I scripts/packaging/build_macos.py --output-dir build/private-release/candidate-2
```

每次用新的輸出目錄；已有候選包會保留並拒絕覆蓋。版本與依賴固定，可重複執行相同流程；未宣稱 ZIP 位元組完全重現，codesign、ZIP timestamps 等仍可能不同。

## 產物與授權證據

輸出目錄包括 `.app`、包裹 `.app` 的 ZIP、ZIP SHA-256、`BUILD_MANIFEST.json` 與 `FROZEN_INVENTORY.json`。法律目錄同時放在外層 `legal/` 與 `.app/Contents/Resources/legal/`：

- 自有授權與發行政策文件；第三方權利由原始條款控制。
- `THIRD_PARTY_INVENTORY.json`：exact installed distribution name/version、runtime/build-tool role、metadata/RECORD SHA-256、授權原文路徑與 SHA-256。
- `third-party/<package>/`：wheel 所附原始 LICENSE/COPYING/NOTICE，保留巢狀路徑，含 build tool notices。依檔名（含 `LICENCE` 英式拼法）與 PEP 639 標準位置 `<dist-info>/licenses/` 兩種方式辨識；後者的檔名由上游決定而非慣例，例如 pypdfium2 以 `LICENSES/BSD-3-Clause.txt`、`BUILD_LICENSES/freetype.txt` 攜帶 PDFium 內含元件的授權。任一 wheel 完全未附授權即中止建置。
- 升級任何 pinned 版本後，先執行 `python3 scripts/packaging/audit_notices.py --profile pdf`（或 `--profile text`）。它不需安裝即可依 lock 的 hash 取得對應 wheel 並套用建置本身的判定規則，可在非 macOS 機器上先行確認，避免在 Mac 上才發現上游移除授權檔。
- `third-party/python-runtime/`：同版本官方完整 artifact 的原始 `PYTHON.json`、native notices、CPython installed LICENSE、取得來源與 artifact hash。
- `requirements-macos-arm64.txt` 與 hash lock；實際 frozen module／binary source inventory。

官方 Python metadata 是完整 Python build 的參考資料，並不代表每個 extension 都被打包。`FROZEN_INVENTORY.json` 決定實際攜帶內容。metadata 未提供的個別 native dependency 版本不能從 license identifier 推定；使用官方 artifact provenance 與 binary hashes追溯。macOS 系統 framework／libz 使用作業系統版本，不複製為應用程式私有 library。

PyInstaller 官方說明允許在符合依賴授權的前提下使用例外條款封裝商用程式。此例外只處理 PyInstaller，不取代依賴或自有程式的權利確認。查看[官方授權說明](https://pyinstaller.org/en/stable/license.html)；實際版本的 wheel `COPYING.txt` 會隨清單保留。[官方 macOS 建置說明](https://pyinstaller.org/en/stable/usage.html#macos-specific-options)也說明未提供 signing identity 時採 ad-hoc signing。

## 驗證與操作

### 一般使用者：啟動本機候選包

候選 ZIP 位於建置它的那台 Mac 的專案資料夾內，以 `text` 版為例：

`build/private-release/candidate-text/Document-Converter-macos-arm64-local-candidate.zip`

`pdf` 版則是 `build/private-release/candidate-pdf/Document-Converter-macos-arm64-pdf-local-candidate.zip`。

此 ZIP 是本機建置產物，不在 GitHub 原始碼倉庫內。於 Finder 雙擊 ZIP
解壓縮，再雙擊解壓資料夾中的 **Document Converter.app**。App 啟動後會選用
可用的本機連接埠，並在預設瀏覽器開啟轉換介面。選取 UTF-8 `.md`、
`.markdown` 或 `.txt`，選擇 Markdown 或 HTML，按「開始轉換」。單一輸出
下載為檔案，多個輸出下載為 ZIP；下載通常位於瀏覽器的 Downloads 資料夾。

上傳內容與轉換輸出使用每次請求專屬的系統暫存資料夾；請求完成後即清除。
瀏覽器已下載的輸出檔會保留在 Downloads。關閉瀏覽器不會停止 App；請在
「活動監視器」搜尋並退出 **Document Converter**，以停止本機服務。

此候選包只有 ad-hoc 簽章，沒有 Developer ID 簽章或 Apple notarization。
macOS 首次開啟時可能顯示安全性警告。請勿為了開啟它而停用 Gatekeeper；
依照你所在組織核准的 App 審查流程處理。候選包僅供 Apple Silicon 使用。

驗證紀錄：候選包 frozen release integration 有 10 項測試通過；專案整套測試
有 111 項通過，覆蓋率 83.56%。這些測試不代表 Finder 雙擊、其他 Mac 安裝或
Windows 支援已驗證。Windows 尚無安裝包且未測試；README 的 Windows venv
指令只說明原始碼環境設定。

### 維護者驗證指令

```sh
build/private-release/venv/bin/python -I -m unittest discover -s tests -p test_release_packaging.py -v
"build/private-release/candidate/Document-Converter-macos-arm64-local-candidate/Document Converter.app/Contents/MacOS/Document Converter" --diagnostics
"build/private-release/candidate/Document-Converter-macos-arm64-local-candidate/Document Converter.app/Contents/MacOS/Document Converter" --no-browser --port 18767
```

HTTP smoke 使用新的 loopback port，驗證首頁、Markdown round trip、HTML、UTF-8 TXT、PDF 拒絕、非法 UTF-8 與 Host／Origin 安全邊界。`--diagnostics` 報告 frozen 狀態與 import paths，拒絕已載入的 forbidden engines。正常開啟 `.app` 會選可用 loopback port 並開啟預設瀏覽器。關閉頁面不會停止背景程式；在「活動監視器」退出 Document Converter，或從 CLI 啟動時按 Ctrl-C。測試使用 `--no-browser`；Finder 雙擊與 GUI 啟動仍未驗證。

乾淨機器的安裝驗收不需要第二台 Mac：`docs-release/macos-vm-verification.md` 是用免費的 macOS 虛擬機
（Apple 授權允許同一台 Apple Silicon Mac 同時執行 2 台）走完「同事收到 App」全程的 SOP，
含刻意貼上隔離標籤以觸發 Gatekeeper、以及在沒有 Python 的客體系統確認 `.app` 自我完整。
它驗收「漏帶東西」與 Gatekeeper 流程，不驗收不同晶片世代與不同 macOS 大版本的差異。

候選包固定標記 `distribution_ready: false`，沒有 Developer ID 簽章或 notarization。此流程不 commit、push、發布、修改 GitHub visibility，也不代表第三方或產品的完整法律核准。正式交付仍需確認自有權利／接受者、native inventory、獨立驗收、簽章／notarization 與目標電腦的實際安裝。不得以關閉 Gatekeeper 取代安裝驗收。
