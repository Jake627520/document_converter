# Change Proposal: Standalone HTML Renderer

**Change ID**: 001  
**Status**: Proposed  
**Author**: Jake Chiu  
**Date**: 2026-10-08  
**Related Specs**: specs/003-output-formats.md  

---

## Problem Statement

目前 `writer.py` 的 HTML 輸出僅為簡單包裝（將 Markdown 內容包裹在 `<html><body>...</body></html>` 中），缺乏：

1. **語義化標籤**：標題應為 `<h1>`-`<h6>`，列表應為 `<ul>/<ol>`，表格應為 `<table>`
2. **HTML 跳脫**：特殊字元（`<`, `>`, `&`）未正確跳脫，可能導致 XSS 或渲染錯誤
3. **離線相容**：未來若支援數學公式，需確保不依賴外部 CDN
4. **可測試性**：缺乏針對 HTML 輸出品質的獨立測試

這導致 HTML 輸出品質不穩定，無法用於正式網頁發布或離線檢視。

---

## Proposed Solution

建立獨立的 `document_converter/renderer.py` 模組，負責：

1. **Markdown → HTML 轉換**：
   - 標題：`# H1` → `<h1>H1</h1>`
   - 段落：純文字段落 → `<p>...</p>`
   - 列表：`- item` → `<ul><li>item</li></ul>`
   - 表格：`| col1 | col2 |` → `<table><tr><td>...</td></tr></table>`
   - 程式碼：` ```python ... ``` ` → `<pre><code class="language-python">...</code></pre>`

2. **HTML 跳脫**：
   - 使用 `html.escape()` 處理特殊字元
   - 程式碼區塊內容需雙重跳脫（防止注入）

3. **離線優先**：
   - 不依賴外部 CDN（MathJax/KaTeX 暫不實作）
   - 未來若支援數學公式，提供內嵌選項或本地靜態資源

4. **與現有 writer.py 相容**：
   - 不破壞既有 API（`write_html()` 簽章不變）
   - 可選擇性啟用新渲染器（`--use-renderer` 旗標，未來預設啟用）

---

## Acceptance Criteria

- [ ] 建立 `document_converter/renderer.py`，包含 `render_html(markdown: str) -> str` 函式
- [ ] 建立 `tests/test_renderer.py`，覆蓋標題、段落、列表、表格、程式碼、HTML 跳脫
- [ ] 所有測試通過（`pytest tests/test_renderer.py`）
- [ ] 更新 `specs/003-output-formats.md`，增加 HTML renderer 規格
- [ ] 更新 `writer.py`，接入新渲染器（向後相容）
- [ ] 執行 `make test` 全套測試通過
- [ ] 執行 `make lint` 無警告

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 破壞現有 writer.py API | High | 維持既有簽章，增加 `use_renderer=True` 參數 |
| 表格解析複雜度高 | Medium | 先支援簡化表格（無合併儲存格），進階功能留待 v0.5 |
| 數學公式處理未定 | Low | 明確標註「暫不支援」，留待 v0.4 Change |
| HTML 跳脫遺漏 | Medium | TDD 優先寫失敗測試，強制覆蓋邊界案例 |

---

## Timeline Estimate

| Phase | Estimated Time |
|---|---|
| Change Proposal & Design | 30 min |
| TDD: 寫失敗測試 | 1-2h |
| 實作 renderer.py | 2-3h |
| 整合 writer.py | 1h |
| 測試與除錯 | 1-2h |
| 更新 Specs & 封存 | 30 min |
| **Total** | **6-9h** |

---

## Decision Record

**Decision**: 採用輕量級自實作渲染器，而非引入 `markdown` 或 `mistune` 套件。

**Rationale**:
1. 減少依賴（符合 minimal-dependency 原則）
2. 完全控制 HTML 輸出品質（無黑盒子）
3. 避免引入額外授權風險（`markdown` 套件為 BSD，但依賴越多風險越高）
4. 教育價值：實作過程可深入理解 Markdown → HTML 轉換邏輯

**Alternatives Considered**:
- `markdown` 套件：功能完整，但依賴增加、自訂性低
- `mistune` 套件：輕量，但仍為外部依賴
- `mistletoe` 套件：符合 CommonMark，但學習曲線陡峭

**Conclusion**: 自實作輕量渲染器，專注於核心功能（標題、表格、程式碼、跳脫），進階功能留待未來。

---

## References

- [OpenSpec Getting Started](https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md)
- [specs/003-output-formats.md](../specs/003-output-formats.md)
- [document_converter/writer.py](../document_converter/writer.py)
- [tests/test_writer.py](../tests/test_writer.py)
