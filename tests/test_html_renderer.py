import unittest
from pathlib import Path
from document_converter.renderer import render_markdown_to_html

class TestStandaloneHtmlRenderer(unittest.TestCase):
    """Ref: openspec/changes/CHG-001-standalone-html-renderer/"""

    def test_headings_and_paragraphs(self):
        md = "# Main Title\n\n## Sub Title\n\nThis is a standard paragraph."
        html = render_markdown_to_html(md, title="Test Doc")
        self.assertIn("<h1>Main Title</h1>", html)
        self.assertIn("<h2>Sub Title</h2>", html)
        self.assertIn("<p>This is a standard paragraph.</p>", html)

    def test_table_rendering(self):
        md = "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |"
        html = render_markdown_to_html(md, title="Table Test")
        self.assertIn("<table>", html)
        self.assertIn("<th>Header 1</th>", html)
        self.assertIn("<th>Header 2</th>", html)
        self.assertIn("<td>Cell 1</td>", html)
        self.assertIn("<td>Cell 2</td>", html)
        self.assertIn("</tbody>", html)

    def test_unordered_and_ordered_lists(self):
        html = render_markdown_to_html("- first\n- second\n\n1. one\n2. two")
        self.assertIn("<ul><li>first</li><li>second</li></ul>", html)
        self.assertIn("<ol><li>one</li><li>two</li></ol>", html)

    def test_fenced_code_blocks(self):
        md = "```python\ndef add(a, b):\n    return a + b\n```"
        html = render_markdown_to_html(md, title="Code Test")
        self.assertIn("<pre><code", html)
        self.assertIn("def add(a, b):", html)
        self.assertIn("return a + b", html)

    def test_html_escaping_xss_protection(self):
        md = "Safe text <script>alert('xss')</script> & other <tag>"
        html = render_markdown_to_html(md, title="Escape Test")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&amp;", html)
        self.assertNotIn("<tag>", html)

    def test_title_is_html_escaped(self):
        html = render_markdown_to_html("body", title='<script>alert("x")</script>')
        self.assertNotIn("<title><script>", html)
        self.assertIn("<title>&lt;script&gt;", html)

    def test_empty_document_has_complete_structure(self):
        html = render_markdown_to_html("")
        self.assertIn("<main class=\"markdown-body\">", html)
        self.assertIn("</main>", html)

    def test_markdown_fixture_matches_expected_rendered_fragment(self):
        fixture_dir = Path(__file__).parent / "fixtures"
        md = (fixture_dir / "sample_text.md").read_text(encoding="utf-8")
        rendered = render_markdown_to_html(md)
        self.assertIn("<h1>Document Converter Spec Test Sample</h1>", rendered)

    def test_code_language_is_safe_attribute_value(self):
        html = render_markdown_to_html('```x" onmouseover="alert(1)\ncode\n```')
        self.assertNotIn('onmouseover="alert(1)', html)

    def test_offline_zero_cdn_guarantee(self):
        md = "# Offline Check\n\nTesting complete offline usability."
        html = render_markdown_to_html(md, title="Offline Test")
        self.assertIn("<style>", html)
        self.assertNotIn("href=\"http", html)
        self.assertNotIn("src=\"http", html)
        self.assertNotIn("href='http", html)
        self.assertNotIn("src='http", html)

if __name__ == "__main__":
    unittest.main()
