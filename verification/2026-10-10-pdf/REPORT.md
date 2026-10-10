# PDF 轉檔驗證報告（2026-10-10）

## 一句話結論

PDF 可以用正式指令轉成 Markdown / HTML / JSON / 純文字，而且不需要安裝 PyTorch：

```bash
document-converter convert ~/Documents/我的PDF --engine docling-native --to md --to html
```

驗證過程中查出的 3 個問題都已修掉（細節在第 4 節）。你 Mac 上那個候選 App 仍然
不收 PDF —— 那是發行入口的設計，不在這次修正範圍。

## 1. 這次實際轉出來的檔案

| 來源 PDF | 頁數 | 偵測結果 | 轉檔狀態 | 備註 |
|---|---|---|---|---|
| `headlamp_spec_zh.pdf`（中文車燈規格書，含表格、2 頁） | 2 | text_based | OK | 中文、表格數值、雙語混排都正確 |
| `tv_panel_memo_en.pdf`（英文電視面板備忘） | 1 | text_based | OK | — |
| `scanned_inspection_sheet.pdf`（掃描版，沒有文字層） | 1 | scanned | OK（內容是空的） | 會警告「沒有跑 OCR」 |

輸出資料夾（每個檔案都有 `.md` / `.html` / `.json` / `.txt` 四種）：

- `results-clean/` — **主要成果**，由正式 CLI 加 `--clean` 產生
- `results-raw/` — 同一批但不加 `--clean`
- `results-project-renderer/` — 改用本專案 `renderer.py` 產生的 HTML
- `reports/` — 指令輸出、pytest 紀錄、JSON 執行摘要

來源 PDF 在 `samples/`，但**沒有進 git**：repo 的 `.gitignore` 有一條 `*.pdf`
（避免誤傳真實文件）。重建這三個樣本：

```bash
python -I verification/2026-10-10-pdf/make_sample_pdfs.py
```

## 2. 為什麼不用 PyTorch 也能轉

白話講：Docling 平常轉 PDF 會「先用 AI 看圖認版面」，所以要裝 PyTorch（約 2–4 GB）
再從 huggingface.co 下載模型。但 Docling 另外有一條 `NativePdfPipeline`，意思是
「直接把 PDF 裡本來就有的文字撈出來」，完全不跑 AI 模型。這次把它包成新引擎
`docling-native`（`document_converter/engines/docling_native_engine.py`）。

- 好處：安裝小（`pip install docling-slim` 就夠）、很快（每頁不到 0.1 秒）、不需連網
  下載模型、純本機。
- 代價：沒有標題階層、沒有 Markdown 表格、沒有閱讀順序重排、沒有 OCR。表格會變成
  一格一行的純文字（見 `results-clean/headlamp_spec_zh.md`）。每次轉檔都會印出這段
  警告，不會讓人誤以為是完整結構。
- `--engine auto` 把它排在最後：有裝模型版就優先用模型版，沒裝才用它，所以 PDF 不會
  再整批失敗。

### 在你的 Mac 上轉自己的 PDF

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
pip install -e .                      # 完整版（含 PyTorch，之後兩條路都能走）

# 或只要不用 torch 的精簡版（實測約 0.4 GB，已驗證可轉檔）：
# pip install "docling-slim[convert-core,format-pdf]" typer rich pypdf
# pip install -e . --no-deps

document-converter convert ~/Documents/我的PDF資料夾 \
    --engine docling-native --to md --to html -o ~/Desktop/converted --clean
```

`--engine docling-native` 可以換成 `--engine auto`：在沒有 PyTorch 的環境，模型版引擎
載入失敗後會自動落到 `docling-native`，所以 PDF 不會整批失敗（實測紀錄見
`reports/slim-install-no-torch.txt`）。單一檔案或整個資料夾都可以當輸入。

## 3. 驗收指令

```bash
python -m pytest          # 122 passed, 7 skipped（覆蓋率 87.67%）
document-converter --help
document-converter list-engines
```

測試在「有裝 pypdf」與「pypdf 被擋掉（走內建分析器）」兩種環境都是 122 passed
（`reports/pytest.txt`）。7 項 skip 是候選包整合測試，`.app` 只存在你的 Mac 上。

## 4. 驗證中查出的 3 個問題與修正

### (1) `--clean` 會把獨立一行的數字整行刪掉（會掉資料）→ 已修

原本 `cleaner.py` 只要看到一行是 1–4 位數字就刪掉，原意是去掉頁碼，但表格數值也被
當頁碼砍掉：規格表「LED 顆數 84」的 `84` 會消失。

修正：預設**保留**只有數字的行；`Page 3 of 12`、`4 / 20`、`- 5 -` 這種有標籤的頁碼
照舊刪除。要回到舊的積極行為，加 `--clean --strip-page-numbers`
（對照見 `reports/clean-vs-strip-page-numbers.txt`）。

### (2) 新 clone 跑 `python -m pytest` 不會全過 → 已修

`.gitignore` 的 `*.pdf` 把測試用的 `tests/fixtures/sample_text.pdf` 一起擋掉，那個檔
從來沒進 repo，所以乾淨 clone 會有 3 項失敗。先前「111 項通過」是本機剛好有這個
未追蹤檔案才成立。

修正：新增 `tests/pdf_samples.py`，用程式產生**結構合法**的小 PDF（正確的
cross-reference offset、字型資源、真的內容串流），測試在暫存目錄自己建輸入，不再依賴
任何 commit 不進去的二進位檔。`.gitignore` 的防護規則保持原樣。

### (3) PDF 偵測結果會隨環境改變，而且內建分析器會誤判 → 已修

`detector.py` 優先用 `pypdf`，但 `pypdf` 不在依賴清單裡；照 README 裝完其實是用內建
分析器，而它把這三份 PDF 全判成 `scanned`、字數 0。原因有兩個：regex 要求
`endstream` 前面一定有換行，而且只會 zlib 解壓，遇到 ASCII85Decode 就讀不到字。

修正：
- `pypdf` 列入正式依賴，偵測結果不再看環境。
- 內建分析器容許 `endstream` 前沒有換行，並支援 ASCII85（含 ASCII85 包 Flate）。現在
  兩種環境對三份樣本的分類完全一致（`reports/cli-inspect.txt`）。
- 順手修掉誤導的警告：原本掃描 PDF 一律印「OCR processing applied」，但其實沒做 OCR。
  現在改成指名引擎並提醒檢查輸出。

另外 `AGENTS.md` 寫的 `document-converter --list-engines` 不存在，已改成子指令
`list-engines`（`cli.py:134`）。

規格文件（`openspec/specs/`）同步更新：engine-adapter 新增「不需模型權重也能轉 PDF」、
output-formats 新增「清理不得刪掉內容」、pdf-detection 新增「內建分析器要能讀常見編碼」、
cli-interface 新增引擎名稱與 `--strip-page-numbers`。

## 5. 仍未驗證的部分（請當成未知，不要當成可用）

- **你 Mac 上的 App 不支援 PDF。** 發行入口寫死只收 `.md`/`.markdown`/`.txt`
  （`web_app.py:32-33`、`114`），PDF 會被擋掉。這次沒有改發行入口。
- **Docling 標準管線（有版面 AI 的那條）沒驗。** 一是你要我跳過 torch，二是這台雲端機
  的網路政策擋掉 huggingface.co（CONNECT 403），模型權重下載不下來。若要驗，需在環境
  設定的 Network access 把 `huggingface.co` 加進 Allowed domains（標題列的 cloud
  environment 選單 → Edit），步驟見
  https://code.claude.com/docs/en/cloud-environments#network-access
- **OCR 完全沒驗**，掃描 PDF 目前等於轉不出內容。
- **候選包測試 7 項全 skip**，`.app` 只存在你的 Mac 上。
- Finder 雙擊啟動、跨 Mac 安裝、Windows 相容性 — 仍未驗證。
- 本次在 Linux / CPython 3.13 驗證，不是 macOS arm64 / 3.12。

## 6. 重現方式

```bash
# 1. 重建樣本 PDF（需要 reportlab、pillow）
python -I verification/2026-10-10-pdf/make_sample_pdfs.py

# 2. 正式 CLI 轉檔
document-converter convert verification/2026-10-10-pdf/samples \
    --to md --to html --to json --to txt \
    -o verification/2026-10-10-pdf/results-clean --clean --engine docling-native

# 3. 專案自家 renderer 的 HTML 對照
python verification/2026-10-10-pdf/convert_pdfs_native.py \
    --project-html-output verification/2026-10-10-pdf/results-project-renderer

# 4. 驗收
python -m pytest
```
