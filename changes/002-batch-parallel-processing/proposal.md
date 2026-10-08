# CHG-002 — Batch Parallel Processing

## 1. Proposal Summary
- **Change ID**: 002
- **Title**: Batch Parallel Processing (`--parallel N`)
- **Status**: IN_PROGRESS
- **Author**: Antigravity & User
- **Target Release**: v0.3.0

## 2. Problem Statement
在處理大量文件（特別是數十至數百份 PDF 或 Office 檔案）時，單執行緒循序處理耗時過長。然而，若無節制地啟動平行處理，本機 OCR 模型（如 Docling LayoutLM/EasyOCR/MinerU）會占用巨量記憶體（RAM/VRAM），可能導致系統 OOM 崩潰。此外，若批次中某一個損壞文件引發例外，不應中斷其餘健康文件的轉換。

## 3. Scope & Requirements
1. **平行度控制 (`--parallel N` / `-p N`)**：
   - 預設值：`1`（循序執行，記憶體最安全）。
   - 最大安全上限：預設限制上限為 `4` workers（可透過環境變數或參數擴充，但防範預設過載）。
2. **容錯隔離 (Fault Isolation)**：
   - 批次任務中若單一文件處理失敗，記錄其錯誤摘要並繼續處理其餘文件，整體命令回傳退出碼 `0`（或有 warning 狀態），絕不可中斷。
3. **路徑與檔名衝突防護**：
   - 保留來源資料夾之相對層級。
   - 若同目錄下存在同主檔名之不同輸入（例如 `report.pdf` 與 `report.docx` 同時輸出 `.md`），自動附加副檔名特徵避免無意覆蓋。
4. **進度回報**：
   - 終端機表格匯總各檔案之執行狀態（`OK`, `OK (warnings)`, `FAILED`）。
