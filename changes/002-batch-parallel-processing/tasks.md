# Tasks — CHG-002 Batch Parallel Processing

- [x] **Phase 1: TDD RED (失敗測試先行)**
  - [x] 建立 `tests/test_batch_parallel.py`
  - [x] 測試項目 1: 多檔案平行轉換正確產出各目標格式
  - [x] 測試項目 2: 容錯測試（單一檔案損毀拋出錯誤時，其餘檔案仍成功完成）
  - [x] 測試項目 3: 平行 worker 數量約束與邊界驗證
  - [x] 執行測試確認 FAIL (RED)
- [x] **Phase 2: TDD GREEN (實作平行處理管道)**
  - [x] 在 `document_converter/pipeline.py` 實作 `process_batch`
  - [x] 在 `document_converter/cli.py` 整合 `--parallel` 參數
  - [x] 執行測試確認全部 PASS (GREEN)
- [x] **Phase 3: 驗證與同步**
  - [x] 執行 `make lint && make test` (51 項測試全數通過)
  - [x] 提交 commit 並同步至遠端 Private repo
