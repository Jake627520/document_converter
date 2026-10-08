"""Supplementary HTML renderer regression tests for CHG-001."""

import unittest
from pathlib import Path
from document_converter.renderer import render_html


class TestHTMLRenderer(unittest.TestCase):
    """HTML 渲染器測試套件"""

    def test_render_heading_h1(self):
        """測試：一級標題 # H1 → <h1>H1</h1>"""
        md = "# Document Title"
        expected = "<h1>Document Title</h1>"
        result = render_html(md)
        self.assertIn(expected, result)

    def test_render_heading_h2_h3(self):
        """測試：多級標題 ## H2, ### H3"""
        md = """## Section 1
### Subsection 1.1"""
        result = render_html(md)
        self.assertIn("<h2>Section 1</h2>", result)
        self.assertIn("<h3>Subsection 1.1</h3>", result)

    def test_render_paragraph(self):
        """測試：純文字段落 → <p>...</p>"""
        md = "This is a paragraph.\nIt spans multiple lines."
        result = render_html(md)
        self.assertIn("<p>This is a paragraph.\nIt spans multiple lines.</p>", result)

    def test_render_unordered_list(self):
        """測試：無序列表 - item → <ul><li>item</li></ul>"""
        md = """- Item 1
- Item 2
- Item 3"""
        result = render_html(md)
        self.assertIn("<ul>", result)
        self.assertIn("<li>Item 1</li>", result)
        self.assertIn("<li>Item 2</li>", result)
        self.assertIn("<li>Item 3</li>", result)

    def test_render_ordered_list(self):
        """測試：有序列表 1. item → <ol><li>item</li></ol>"""
        md = """1. First item
2. Second item
3. Third item"""
        result = render_html(md)
        self.assertIn("<ol>", result)
        self.assertIn("<li>First item</li>", result)
        self.assertIn("<li>Second item</li>", result)

    def test_render_code_inline(self):
        """測試：行內程式碼 `code` → <code>code</code>"""
        md = "Use the `print()` function."
        result = render_html(md)
        self.assertIn("<code>print()</code>", result)

    def test_render_code_block_python(self):
        """測試：程式碼區塊 ```python ... ``` → <pre><code class="language-python">"""
        md = """```python
def hello():
    print("Hello, World!")
```"""
        result = render_html(md)
        self.assertIn('<pre><code class="language-python">', result)
        self.assertIn("def hello():", result)
        self.assertIn("</code></pre>", result)

    def test_render_code_block_escape(self):
        """測試：程式碼區塊中的 HTML 應被跳脫（防止注入）"""
        md = """```html
<div onclick="alert('XSS')">Malicious Code</div>
```"""
        result = render_html(md)
        # HTML 特殊字元應被跳脫
        self.assertIn("&lt;div", result)
        self.assertIn("&gt;", result)
        self.assertNotIn("<div onclick=", result)  # 不應渲染為真實 HTML

    def test_render_table_simple(self):
        """測試：簡化表格 | col1 | col2 | → <table>...</table>"""
        md = """| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |"""
        result = render_html(md)
        self.assertIn("<table>", result)
        self.assertIn("<th>Name</th>", result)
        self.assertIn("<th>Age</th>", result)
        self.assertIn("<td>Alice</td>", result)
        self.assertIn("<td>Bob</td>", result)

    def test_html_escape_script(self):
        """測試：HTML 跳脫 - <script> 標籤應被跳脫"""
        md = "# <script>alert('XSS')</script>"
        result = render_html(md)
        # 不應包含真實的 <script> 標籤
        self.assertNotIn("<script>", result)
        # 應被跳脫為 &lt;script&gt;
        self.assertIn("&lt;script&gt;", result)

    def test_html_escape_special_chars(self):
        """測試：HTML 跳脫 - 特殊字元 &, <, > 應被跳脫"""
        md = "Use A & B, not C < D > E"
        result = render_html(md)
        self.assertIn("&amp;", result)  # & → &amp;
        self.assertIn("&lt;", result)   # < → &lt;
        self.assertIn("&gt;", result)   # > → &gt;

    def test_full_document_structure(self):
        """測試：完整 HTML5 文件結構"""
        md = "# Title\n\nThis is content."
        result = render_html(md)

        # 檢查 HTML5 結構
        self.assertIn("<!doctype html>", result.lower())
        self.assertIn("<html", result)
        self.assertIn("<head>", result)
        self.assertIn("<body>", result)
        self.assertIn("</html>", result)

        # 檢查 meta 標籤
        self.assertIn('<meta charset="UTF-8">', result)
        self.assertIn('name="viewport"', result)

    def test_full_document_with_fixture(self):
        """Fixture files are repository-relative and must render key content."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        md = (fixtures_dir / "sample_text.md").read_text(encoding="utf-8")
        expected_html = (fixtures_dir / "expected" / "sample_text.html").read_text(
            encoding="utf-8"
        )
        result = render_html(md)
        self.assertIn("Document Converter Spec Test Sample", result)
        for expected_fragment in (
            "<h1>Document Converter Spec Test Sample</h1>",
            "<p>This is a test paragraph.</p>",
        ):
            self.assertIn(expected_fragment, expected_html)
            self.assertIn(expected_fragment, result)


class TestHTMLRendererEdgeCases(unittest.TestCase):
    """邊界案例測試"""

    def test_empty_markdown(self):
        """測試：空 Markdown 字串"""
        md = ""
        result = render_html(md)
        self.assertIn("<!doctype html>", result.lower())
        # 應產生有效 HTML，即使為空

    def test_mixed_content(self):
        """測試：混合多種語法"""
        md = """# Title

This is a paragraph.

## Section

- List item 1
- List item 2

```python
code = "block"
```

| Col1 | Col2 |
|------|------|
| A | B |
"""
        result = render_html(md)

        # 檢查所有語法都被正確渲染
        self.assertIn("<h1>Title</h1>", result)
        self.assertIn("<p>This is a paragraph.</p>", result)
        self.assertIn("<h2>Section</h2>", result)
        self.assertIn("<ul>", result)
        self.assertIn('<pre><code class="language-python">', result)
        self.assertIn("<table>", result)

    def test_code_block_preserves_indentation(self):
        """測試：程式碼區塊應保留縮排"""
        md = """```python
def nested():
    if True:
        print("Indented")
```"""
        result = render_html(md)
        # 應保留縮排（至少包含 4 個空格）
        self.assertIn("    ", result)

    def test_heading_with_special_chars(self):
        """測試：標題中的特殊字元應被跳脫"""
        md = "# A & B < C > D"
        result = render_html(md)
        self.assertIn("<h1>", result)
        self.assertIn("&amp;", result)
        self.assertIn("&lt;", result)
        self.assertIn("&gt;", result)


if __name__ == "__main__":
    # 執行測試
    unittest.main(verbosity=2)
