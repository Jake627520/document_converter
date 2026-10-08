# Spec Diff: HTML Renderer Change

**Change ID**: 001  
**Related Specs**: specs/003-output-formats.md  

---

## Current State (specs/003-output-formats.md v0.2)

目前 HTML 輸出規格（第 3.2 節）：

```markdown
### 3.2 HTML Output

HTML 輸出應為有效的 HTML5 文件，包含：
- `<!doctype html>` 宣告
- `<html>`, `<head>`, `<body>` 標籤
- 基本 meta 標籤（charset, viewport）

目前實作：將 Markdown 內容直接包裹在 HTML 標籤中，未進行語義化轉換。
```

**缺口**：
1. 未定義 Markdown → HTML 的轉換規則（標題、列表、表格、程式碼）
2. 未定義 HTML 跳脫行為
3. 未定義離線使用原則

---

## Proposed Changes (specs/003-output-formats.md v0.3)

### 新增章節：3.2.1 HTML Renderer

```markdown
### 3.2.1 HTML Renderer

獨立渲染器 `document_converter.renderer.render_html()` 負責將 Markdown 轉換為語義化 HTML。

#### 支援的 Markdown 語法

| Markdown | HTML | 備註 |
|---|---|---|
| `# H1` ~ `###### H6` | `<h1>H1</h1>` ~ `<h6>H6</h6>` | 標題層級對應 |
| 純文字段落 | `<p>...</p>` | 連續非空行視為段落 |
| `- item` / `* item` | `<ul><li>item</li></ul>` | 無序列表 |
| `1. item` | `<ol><li>item</li></ol>` | 有序列表 |
| `\`code\`` | `<code>code</code>` | 行內程式碼 |
| `\\`\\`python ... \\`\\`` | `<pre><code class="language-python">...</code></pre>` | 程式碼區塊 |
| `| col1 | col2 |` | `<table><tr><td>...</td></tr></table>` | 表格（簡化版，無合併儲存格） |

#### HTML 跳脫規則

- 所有 HTML 特殊字元（`<`, `>`, `&`, `"`, `'`）必須使用 `html.escape()` 跳脫
- 程式碼區塊內容需雙重跳脫（防止注入）
- 標題、段落內容需跳脫

#### 離線使用原則

- 不依賴外部 CDN（MathJax/KaTeX 暫不實作）
- 未來若支援數學公式，提供內嵌選項或本地靜態資源
- 所有 CSS 應內嵌於 `<style>` 標籤或本地檔案

#### 與 writer.py 相容性

- `writer.write_html()` 維持既有簽章
- 增加 `use_renderer: bool = True` 參數（預設啟用新渲染器）
- 向後相容：呼叫 `write_html(content, use_renderer=False)` 可使用舊版簡單包裝
```

### 修改章節：3.2 HTML Output

將現有描述修改為：

```markdown
### 3.2 HTML Output

HTML 輸出應為有效的 HTML5 文件，由 `writer.write_html()` 產生，包含：
- `<!doctype html>` 宣告
- `<html>`, `<head>`, `<body>` 標籤
- 基本 meta 標籤（charset, viewport）
- 語義化內容（由 renderer.render_html() 轉換）

預設啟用獨立渲染器；可透過 `--legacy-html` 旗標使用舊版簡單包裝。
```

---

## Impact Analysis

| Module | Change | Risk |
|---|---|---|
| `specs/003-output-formats.md` | 增加 3.2.1 節，修改 3.2 節 | Low（純文件更新） |
| `document_converter/writer.py` | 接入 renderer，增加 `use_renderer` 參數 | Medium（需測試相容性） |
| `document_converter/renderer.py` | 新增模組 | Low（獨立模組，無依賴） |
| `tests/test_renderer.py` | 新增測試檔案 | Low（獨立測試） |
| `tests/test_writer.py` | 增加 HTML 測試案例 | Low（擴充既有測試） |
| `document_converter/cli.py` | 增加 `--legacy-html` 旗標（可選） | Low（向後相容） |

---

## Spec Version Bump

- `specs/003-output-formats.md`: v0.2 → v0.3
- `CHANGELOG.md`: 增加 v0.3 章節

---

## Acceptance Criteria for Spec Update

- [ ] `specs/003-output-formats.md` 包含 3.2.1 HTML Renderer 完整規格
- [ ] `specs/003-output-formats.md` 版本號更新為 v0.3
- [ ] `CHANGELOG.md` 記錄 v0.3 變更
- [ ] `make specs` 驗證通過
