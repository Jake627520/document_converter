# Design Document: Standalone HTML Renderer

**Change ID**: 001  
**Status**: Proposed  
**Related Specs**: specs/003-output-formats.md  

---

## Architecture

```
┌─────────────────┐
│   writer.py     │
│  write_html()   │
└────────┬────────┘
         │
         ├─ use_renderer=True ──► renderer.render_html() ──► Semantic HTML
         │
         └─ use_renderer=False ─► Simple wrapper (legacy)
```

---

## Module Design: renderer.py

### 公開 API

```python
def render_html(markdown: str) -> str:
    """
    將 Markdown 轉換為語義化 HTML。

    Args:
        markdown: Markdown 格式字串

    Returns:
        完整的 HTML5 文件字串（包含 <!doctype html>）
    """
```

### 內部函式

```python
def _parse_heading(line: str) -> str | None:
    """解析標題：# H1 → <h1>H1</h1>"""

def _parse_paragraph(lines: list[str]) -> str:
    """解析段落：多行文字 → <p>...</p>"""

def _parse_list(lines: list[str], ordered: bool) -> str:
    """解析列表：- item → <ul><li>...</li></ul>"""

def _parse_table(lines: list[str]) -> str:
    """解析表格：| col1 | col2 | → <table>...</table>"""

def _parse_code_block(lines: list[str], language: str) -> str:
    """解析程式碼區塊：```python ... ``` → <pre><code>...</code></pre>"""

def _escape_html(text: str) -> str:
    """HTML 跳脫：使用 html.escape()"""
```

---

## Parsing Strategy

### 狀態機設計

```python
class ParserState(Enum):
    NORMAL = "normal"           # 一般段落
    HEADING = "heading"         # 標題
    LIST = "list"               # 列表
    TABLE = "table"             # 表格
    CODE_BLOCK = "code_block"   # 程式碼區塊
```

### 解析流程

1. **逐行讀取** Markdown 內容
2. **識別語法**（正則表達式匹配）
3. **狀態轉換**（進入/離開程式碼區塊、列表、表格）
4. **累積內容**（同類型內容合併）
5. **產生 HTML**（呼叫對應解析函式）

---

## HTML Escape Strategy

### 跳脫規則

| 情境 | 跳脫方式 |
|---|---|
| 一般文字（標題、段落） | `html.escape(text)` |
| 程式碼區塊 | `html.escape(code, quote=True)`（雙重跳脫） |
| 表格儲存格 | `html.escape(cell_text)` |
| 列表項目 | `html.escape(item_text)` |

### 實作範例

```python
import html

def _escape_html(text: str) -> str:
    return html.escape(text, quote=True)

# 程式碼區塊需雙重跳脫
def _parse_code_block(lines: list[str], language: str) -> str:
    code = "\n".join(lines)
    escaped_code = html.escape(code, quote=True)  # 雙重跳脫
    return f'<pre><code class="language-{language}">{escaped_code}</code></pre>'
```

---

## HTML Template

### 完整 HTML5 文件結構

```html
<!doctype html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* 基本 CSS（可選，未來擴充） */
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; }}
        pre {{ background: #f4f4f4; padding: 1rem; overflow-x: auto; }}
        code {{ font-family: monospace; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 0.5rem; }}
    </style>
</head>
<body>
{content}
</body>
</html>
```

---

## Testing Strategy (TDD)

### 測試案例清單

| 測試函式 | 測試內容 | 預期行為 |
|---|---|---|
| `test_render_heading()` | `# H1`, `## H2` | 產生 `<h1>`, `<h2>` |
| `test_render_paragraph()` | 多行純文字 | 產生 `<p>...</p>` |
| `test_render_unordered_list()` | `- item1`, `- item2` | 產生 `<ul><li>...</li></ul>` |
| `test_render_ordered_list()` | `1. item1`, `2. item2` | 產生 `<ol><li>...</li></ol>` |
| `test_render_code_inline()` | `` `code` `` | 產生 `<code>code</code>` |
| `test_render_code_block()` | `` ```python ... ``` `` | 產生 `<pre><code class="language-python">` |
| `test_render_table()` | `| col1 | col2 |` | 產生 `<table><tr><td>...</td></tr></table>` |
| `test_html_escape()` | `<script>alert(1)</script>` | 跳脫為 `&lt;script&gt;` |
| `test_code_escape()` | `` ```<div>test</div>``` `` | 雙重跳脫，不渲染為 HTML |
| `test_full_document()` | 混合多種語法 | 產生完整有效的 HTML5 |

### 測試 Fixture

```python
# tests/fixtures/expected/sample_text.html
<!doctype html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Converter Spec Test Sample</title>
    ...
</head>
<body>
<h1>Document Converter Spec Test Sample</h1>
</body>
</html>
```

---

## Compatibility Considerations

### 與 writer.py 相容

```python
# writer.py (既有簽章)
def write_html(content: str, output_path: Path) -> None:
    ...

# writer.py (新增參數)
def write_html(content: str, output_path: Path, use_renderer: bool = True) -> None:
    if use_renderer:
        html_content = render_html(content)
    else:
        html_content = f"<!doctype html><html><body>{content}</body></html>"
    output_path.write_text(html_content, encoding="utf-8")
```

### 與 CLI 相容

```python
# cli.py (既有指令)
document-converter file.pdf --to html

# cli.py (新增旗標，可選)
document-converter file.pdf --to html --legacy-html
```

---

## Performance Considerations

| 操作 | 時間複雜度 | 備註 |
|---|---|---|
| 逐行解析 | O(n) | n = 行數 |
| HTML 跳脫 | O(m) | m = 字元數 |
| 表格解析 | O(r × c) | r = 列數, c = 欄數 |
| 總體 | O(n + m) | 線性複雜度，可接受 |

---

## Future Extensions (Out of Scope)

- 數學公式渲染（MathJax/KaTeX）→ v0.4
- 語法高亮（Pygments）→ v0.4
- 自訂 CSS 主題 → v0.5
- 圖片路徑映射 → v0.5

---

## References

- [Python html.escape()](https://docs.python.org/3/library/html.html#html.escape)
- [CommonMark Spec](https://spec.commonmark.org/)
- [HTML5 Spec](https://html.spec.whatwg.org/)
