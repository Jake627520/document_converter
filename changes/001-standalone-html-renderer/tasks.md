# Task Breakdown: HTML Renderer

**Change ID**: 001  
**Status**: COMPLETED ✅  

---

## Phase 1: Setup & TDD (COMPLETED)

### Task 1.1: 建立測試檔案
- [x] 建立 `tests/test_renderer.py`
- [x] 匯入必要模組
- [x] 建立測試 Fixture 路徑（`tests/fixtures/expected/`）

### Task 1.2: 寫失敗測試
- [x] `test_render_heading_h1()` & `test_render_heading_h2_h3()`: 標題解析
- [x] `test_render_paragraph()`: 段落解析
- [x] `test_render_unordered_list()`: 無序列表
- [x] `test_render_ordered_list()`: 有序列表
- [x] `test_render_code_inline()`: 行內程式碼
- [x] `test_render_code_block_python()`: 程式碼區塊
- [x] `test_render_table_simple()`: 表格
- [x] `test_html_escape_script()`: HTML 跳脫
- [x] `test_full_document_structure()`: 完整文件

### Task 1.3: 建立測試 Fixture
- [x] 建立 `tests/fixtures/expected/sample_text.html`
- [x] 建立 `tests/fixtures/sample_text.md`

---

## Phase 2: Implementation (COMPLETED)

### Task 2.1: 實作 renderer.py 基礎架構
- [x] 建立 `document_converter/renderer.py`
- [x] 實作 `_escape_html()` 函式
- [x] 實作 `render_html()` 主函式

### Task 2.2: 實作語法解析器
- [x] 標題解析（`h1` ~ `h6`）
- [x] 段落解析（`<p>`）
- [x] 列表解析（`<ul>`, `<ol>`）
- [x] 表格解析（`<table>`, `<thead>`, `<tbody>`）
- [x] 程式碼區塊解析（`<pre><code>`，跳脫 XSS）

### Task 2.3: 實作 HTML 模板
- [x] 建立 HTML5 完整文件模板
- [x] 內嵌深淺色現代 CSS
- [x] 支援 safe title 與 100% 離線無 CDN 保證

---

## Phase 3: Integration & Testing (COMPLETED)

### Task 3.1: 整合至 writer.py
- [x] 更新 `writer.py` 呼叫 `render_html()`
- [x] 向後相容既有輸出

### Task 3.2: 執行驗證
- [x] `make test`: 全部 49 項測試通過
