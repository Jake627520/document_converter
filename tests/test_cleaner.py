import unittest
from document_converter.cleaner import clean_markdown

class TestCleaner(unittest.TestCase):
    """Ref: specs/003-output-formats.md"""

    def test_clean_excess_newlines(self):
        raw = "Heading\n\n\n\nParagraph 1\n\n\n\nParagraph 2\n"
        cleaned = clean_markdown(raw)
        self.assertEqual(cleaned, "Heading\n\nParagraph 1\n\nParagraph 2\n")

    def test_clean_page_artifacts(self):
        raw = "Header content\nPage 1 of 12\nBody text\n- 2 -\nMore text\n15\nEnding"
        cleaned = clean_markdown(raw)
        self.assertNotIn("Page 1 of 12", cleaned)
        self.assertNotIn("- 2 -", cleaned)
        self.assertIn("Header content", cleaned)
        self.assertIn("Body text", cleaned)
        self.assertIn("More text", cleaned)

    def test_protects_fenced_code_blocks(self):
        code = "```python\ndef foo():\n\n\n    return 42\n```"
        raw = f"Intro\n\n\n\n{code}\n\n\n\nOutro"
        cleaned = clean_markdown(raw)
        self.assertIn(code, cleaned)

    def test_protects_math_blocks(self):
        math = "$$\nx = \\frac{1}{2}\n$$"
        raw = f"Formula:\n\n\n\n{math}\n\n\n\nEnd"
        cleaned = clean_markdown(raw)
        self.assertIn(math, cleaned)

    def test_preserve_layout_mode(self):
        raw = "Line 1   \n\n\nLine 2   \nPage 1 of 5\n"
        preserved = clean_markdown(raw, preserve_layout=True)
        # preserves all newlines and does not strip page numbers
        self.assertIn("Page 1 of 5", preserved)
        self.assertIn("Line 1\n\n\nLine 2", preserved)

if __name__ == "__main__":
    unittest.main()
