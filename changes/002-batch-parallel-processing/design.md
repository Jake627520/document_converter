# Design — CHG-002 Batch Parallel Processing

## 1. Architecture

```mermaid
flowchart TD
    CLI[CLI Argument: --parallel N] --> Validate[驗證 worker 數量: 1 <= N <= MAX_WORKERS]
    Validate --> Pipeline[pipeline.process_batch]
    Pipeline --> Pool[ThreadPoolExecutor: max_workers=N]
    
    subgraph Parallel Workers
        Pool --> W1[Worker 1: convert_one & write_result]
        Pool --> W2[Worker 2: convert_one & write_result]
        Pool --> WN[Worker N: convert_one & write_result]
    end

    W1 & W2 & WN --> Collector[結果收集與例外隔離]
    Collector --> Table[Rich Console 總覽表格輸出]
```

## 2. Technical Details

### 2.1 Worker 上限與安全邊界
- 定義 `DEFAULT_MAX_WORKERS = 4`。
- 若使用者輸入 `parallel <= 0`，拋出參數錯誤。
- 若使用者輸入 `parallel > 8`，終端輸出警示並限縮或要求確認，避免本機 VRAM/RAM 耗盡。

### 2.2 例外處理規範
- 每個工作單元（Task）包裝於獨立 `try-except` 區塊。
- 失敗結果回傳 `BatchItemResult(success=False, error=str(e), path=path)`。
- 所有任務完成（`as_completed`）後統一匯總。

### 2.3 輸出衝突防範
- 偵測輸出目錄中是否已有同名產物，若為同批次內多個副檔名輸入轉換至相同 stem，在命名時注入來源副檔名後綴（例如 `doc_docx.md`）。
