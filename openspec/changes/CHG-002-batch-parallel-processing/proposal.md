# CHG-002 — Batch Parallel Processing

## 1. Proposal Summary
- **Change ID**: 002
- **Title**: Batch Parallel Processing (`--parallel N`)
- **Status**: IMPLEMENTED (pending baseline review/archive)
- **Author**: Antigravity & User
- **Target Release**: v0.3.0

## 2. Problem Statement
在處理大量文件（特別是數十至數百份 PDF 或 Office 檔案）時，單執行緒循序處理耗時過長。然而，若無節制地啟動平行處理，本機 OCR 模型（如 Docling LayoutLM/EasyOCR/MinerU）會占用巨量記憶體（RAM/VRAM），可能導致系統 OOM 崩潰。此外，若批次中某一個損壞文件引發例外，不應中斷其餘健康文件的轉換。

## 3. Scope & Requirements
1. **平行度控制 (`--parallel N` / `-p N`)**：
   - 預設值：`1`（循序執行，記憶體最安全）。
   - 硬上限：`4` workers；CLI 與 pipeline 都拒絕超限值，不自動夾限，也不支援環境變數繞過。
2. **容錯隔離 (Fault Isolation)**：
   - 批次任務中若單一文件處理失敗，記錄其錯誤摘要並繼續處理其餘文件，整體命令回傳退出碼 `0`（或有 warning 狀態），絕不可中斷。
3. **路徑與檔名衝突防護**：
   - 保留來源資料夾之相對層級。
   - 保留來源相對目錄；同目錄同 stem 的不同輸入以來源副檔名區分。仍碰撞時附加來源路徑的穩定摘要，避免靜默覆蓋。
4. **進度回報**：
   - 終端機表格匯總各檔案之執行狀態（`OK`, `OK (warnings)`, `FAILED`）。

## 4. Acceptance Criteria
- `--parallel` 預設為 1；`1..4` 可用，0 與大於 4 的值明確拒絕。
- `process_batch` 對每個輸入隔離錯誤，且結果順序與輸入順序一致。
- 目錄輸入保留相對子目錄；相同輸出 stem 的輸入產生不同目標名稱且不互相覆蓋。
- 不新增 runtime dependency；worker 上限不能由隱式設定擴大。
