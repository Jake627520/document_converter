# PDF 轉檔驗證報告（2026-10-10）

## 一句話結論

PDF **可以**轉成 Markdown / HTML / JSON / 純文字，而且不需要安裝 PyTorch；但要用
Docling 的「不跑模型」管線，這條路目前**沒有**接到 `document-converter` 指令上，
所以直接打 `document-converter convert xxx.pdf` 現在還是會失敗。另外你 Mac 上那個
App 本來就不收 PDF。

## 1. 這次實際跑出來的檔案

| 來源 PDF | 頁數 | 偵測結果 | 轉檔狀態 | Markdown 字數 | 耗時 |
|---|---|---|---|---|---|
| `headlamp_spec_zh.pdf`（中文車燈規格書，含表格、2 頁） | 2 | text_based | SUCCESS | 811 | 0.17s |
| `tv_panel_memo_en.pdf`（英文電視面板備忘） | 1 | text_based | SUCCESS | 317 | 0.04s |
| `scanned_inspection_sheet.pdf`（掃描版，沒有文字層） | 1 | scanned | SUCCESS（但內容是空的） | 14 | 0.06s |

輸出資料夾（每個檔案都有 `.md` / `.html` / `.json` / `.txt` 四種）：

- `verification/2026-10-10-pdf/results-clean/` — 正式輸出，等同 CLI 的 `--clean`
- `verification/2026-10-10-pdf/results-raw/` — 不做 clean 的同一份，用來對照 clean 砍掉了什麼
- `verification/2026-10-10-pdf/results-project-renderer/` — 改用本專案 `renderer.py` 產生的 HTML
- `verification/2026-10-10-pdf/reports/` — 指令輸出、測試結果、JSON 執行摘要

來源 PDF 放在 `verification/2026-10-10-pdf/samples/`，但**沒有進 git**：repo 的
`.gitignore` 有一條 `*.pdf`（避免誤傳真實文件）。要重建這三個樣本：

```bash
python -I verification/2026-10-10-pdf/make_sample_pdfs.py
```

中文、表格文字、雙語混排都正確轉出來了，HTML 是可直接開的單檔，JSON 有 33 個
text item。掃描版那份只得到 `<!-- image -->`，因為它沒有文字層，而這條管線不做
OCR（文字辨識）。

## 2. 為什麼不用 PyTorch 也能轉

用白話講：Docling 平常轉 PDF 會「先用 AI 看圖認版面」，所以要裝 PyTorch（約 2–4 GB）
再從 huggingface.co 下載模型權重。但 Docling 另外有一條 `NativePdfPipeline`，意思是
「直接把 PDF 裡本來就有的文字字元抓出來」，完全不跑 AI 模型。

- 好處：安裝小、很快（每頁不到 0.1 秒）、不需要連網下載模型、純本機。
- 代價：沒有標題階層、沒有 Markdown 表格、沒有閱讀順序重排、沒有 OCR。表格會變成
  一格一行的純文字（見 `results-clean/headlamp_spec_zh.md`）。

這次用的就是這條路，腳本是 `verification/2026-10-10-pdf/convert_pdfs_native.py`。
它仍然呼叫本專案的 `writer.py`、`renderer.py`、`cleaner.py`，所以輸出序列化是真的
走專案程式碼。

### 轉你自己的 PDF

```bash
python -m venv .venv && source .venv/bin/activate
pip install docling-slim typer rich fastapi uvicorn python-multipart pypdf \
            pypdfium2 docling-core docling-parse doclang lxml pandas pyyaml \
            tabulate latex2mathml marko beautifulsoup4 defusedxml rtree scipy \
            numpy pillow filetype langcodes pluggy pydantic-settings
pip install -e . --no-deps
python verification/2026-10-10-pdf/convert_pdfs_native.py \
    --input ~/Documents/我的PDF資料夾 --output ~/Desktop/converted
```

`--input` 也可以直接給單一檔案。

## 3. 這次發現的 3 個問題

### (1) `--clean` 會把獨立一行的數字整行刪掉（會掉資料）

`document_converter/cleaner.py:44-45` 只要看到一行是 1–4 位數字就刪掉，原意是去掉
頁碼，但表格裡的數值也會被當頁碼砍掉。證據：

```
$ diff results-raw/headlamp_spec_zh.md results-clean/headlamp_spec_zh.md
37,38d36
< 84          <- 規格表「LED 顆數 84」的 84 不見了
```

對 PM 來說這個最嚴重：規格表的數字（數量、尺寸、年份）可能無聲消失。

### (2) 新 clone 下來跑 `python -m pytest` 不會全過

`.gitignore:48` 的 `*.pdf` 把測試用的 `tests/fixtures/sample_text.pdf` 一起擋掉了，
所以那個檔從來沒進 repo。乾淨 clone 的結果是 **4 failed / 100 passed / 7 skipped**
（`reports/pytest.txt`）：

- 缺 fixture 造成 3 項失敗：`test_inspect_fixture`、
  `test_inspect_directory_shows_distinguishable_relative_paths`、
  `test_watch_rejects_file_source`
- 第 4 項 `test_detect_text_based_pdf` 是下面 (3) 造成的

把 fixture 補回來後是 1 failed / 103 passed（`reports/pytest-with-fixture.txt`）。
先前紀錄的「111 項通過」應該是你本機剛好有這個沒被追蹤的檔案才成立。

### (3) PDF 偵測結果會隨「有沒有裝 pypdf」而改變

`detector.py` 優先用 `pypdf`，沒有才用自己寫的分析器。但 `pypdf` **不在**
`pyproject.toml` 的依賴裡，所以照 README 裝完的環境其實是用內建分析器 ——
而內建分析器把這三份 PDF 全部判成 `scanned`、字數 0（`reports/cli-inspect.txt` 有
兩種環境的對照表）。

原因：內建分析器的 regex 要求 `endstream` 前面一定有換行，而且只會 zlib 解壓；
遇到 ASCII85Decode 之類的編碼就讀不到字。誤判成 scanned 之後，`pipeline.py` 會改
用 OCR 優先的引擎順序，還會加一句警告 `OCR processing applied` —— 但其實沒有做 OCR。

## 4. 沒有驗到的部分（請當成未知，不要當成可用）

- **你 Mac 上的 App 不支援 PDF。** 發行入口寫死只收 `.md`/`.markdown`/`.txt`
  （`web_app.py:32-33`、`114`），PDF 會被擋掉。這不是 bug，是當初的設計。
- **Docling 標準管線（有版面 AI 的那條）這次沒驗。** 一是你要我跳過 torch，二是這台
  雲端機的網路政策擋掉 huggingface.co（CONNECT 403），模型權重下載不下來。若要驗這條，
  需要在環境設定的 Network access 把 `huggingface.co` 加進 Allowed domains（標題列的
  cloud environment 選單 → Edit），步驟見
  https://code.claude.com/docs/en/cloud-environments#network-access
- **OCR 完全沒驗。** 掃描檔要靠 OCR，本次管線不含 OCR，所以掃描 PDF 等於轉不出內容。
- **候選包測試 7 項全 skip**（`reports/pytest.txt`），因為 `.app` 只存在你的 Mac 上。
- Finder 雙擊啟動、跨 Mac 安裝、Windows 相容性 — 仍未驗證。
- 本次在 Linux / CPython 3.13 驗證，不是 macOS arm64 / 3.12。

## 5. 重現方式

```bash
# 1. 重建樣本 PDF（需要 reportlab、pillow）
python -I verification/2026-10-10-pdf/make_sample_pdfs.py

# 2. 轉檔（三組輸出）
python verification/2026-10-10-pdf/convert_pdfs_native.py \
    --raw-output verification/2026-10-10-pdf/results-raw \
    --project-html-output verification/2026-10-10-pdf/results-project-renderer

# 3. AGENTS.md 要求的驗收
python -m pytest
document-converter --help
document-converter --list-engines   # 實際子指令是 `document-converter list-engines`
```

備註：`AGENTS.md` 寫的 `document-converter --list-engines` 不存在，CLI 註冊的是子指令
`document-converter list-engines`（`cli.py:134`）。
