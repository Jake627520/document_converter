# Tasks — CHG-002 Batch Parallel Processing

- [x] **Phase 1: TDD RED (失敗測試先行)**
  - [x] 建立 `tests/test_batch_parallel.py`
  - [x] 測試項目 1: 多檔案平行轉換正確產出各目標格式
  - [x] 測試項目 2: 容錯測試（單一檔案損毀拋出錯誤時，其餘檔案仍成功完成）
- [x] 測試預設 worker 數為 1，硬上限 4，並拒絕 0 與 5
- [x] 測試巢狀相對路徑保留及同 stem 輸入不覆寫
- [x] 測試 source_root 未提供時大小寫不同的目的路徑不碰撞
  - [x] 執行測試確認 FAIL (RED)
- [x] **Phase 2: TDD GREEN (實作平行處理管道)**
- [x] 在 `document_converter/pipeline.py` 實作 `process_batch`、硬上限與 deterministic 輸出名稱
- [x] 在 `document_converter/writer.py` 支援共用輸出 stem
  - [x] 在 `document_converter/cli.py` 整合 `--parallel` 參數
  - [x] 執行測試確認全部 PASS (GREEN)
- [x] **Phase 3: 驗證與同步**
- [x] 執行 `make lint`、`make test` 與 `git diff --check`
- [x] OpenSpec change 與基線規格驗證通過
- [x] Commit / push：已於 `b758692` 提交
