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
- `third-party/<package>/`：wheel 所附原始 LICENSE/COPYING/NOTICE，保留巢狀路徑，含 build tool notices。
- `third-party/python-runtime/`：同版本官方完整 artifact 的原始 `PYTHON.json`、native notices、CPython installed LICENSE、取得來源與 artifact hash。
- `requirements-macos-arm64.txt` 與 hash lock；實際 frozen module／binary source inventory。

官方 Python metadata 是完整 Python build 的參考資料，並不代表每個 extension 都被打包。`FROZEN_INVENTORY.json` 決定實際攜帶內容。metadata 未提供的個別 native dependency 版本不能從 license identifier 推定；使用官方 artifact provenance 與 binary hashes追溯。macOS 系統 framework／libz 使用作業系統版本，不複製為應用程式私有 library。

PyInstaller 官方說明允許在符合依賴授權的前提下使用例外條款封裝商用程式。此例外只處理 PyInstaller，不取代依賴或自有程式的權利確認。查看[官方授權說明](https://pyinstaller.org/en/stable/license.html)；實際版本的 wheel `COPYING.txt` 會隨清單保留。[官方 macOS 建置說明](https://pyinstaller.org/en/stable/usage.html#macos-specific-options)也說明未提供 signing identity 時採 ad-hoc signing。

## 驗證與操作

### 一般使用者：啟動本機候選包

目前這台 Mac 的候選 ZIP 位於：

`/Users/jakechiu/Documents/Projects/document_converter/build/private-release/candidate-3/Document-Converter-macos-arm64-local-candidate.zip`

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

候選包固定標記 `distribution_ready: false`，沒有 Developer ID 簽章或 notarization。此流程不 commit、push、發布、修改 GitHub visibility，也不代表第三方或產品的完整法律核准。正式交付仍需確認自有權利／接受者、native inventory、獨立驗收、簽章／notarization 與目標電腦的實際安裝。不得以關閉 Gatekeeper 取代安裝驗收。
