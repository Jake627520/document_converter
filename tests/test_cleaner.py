import unittest
from document_converter.cleaner import clean_markdown

class TestCleaner(unittest.TestCase):
    """Ref: openspec/specs/output-formats/spec.md"""

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

    def test_keeps_a_standalone_number_that_is_document_content(self):
        """A table cell on its own line must survive --clean."""
        raw = "LED count\n\n84\n\nmatrix ADB\n"
        cleaned = clean_markdown(raw)
        self.assertIn("84", cleaned.splitlines())
        self.assertIn("LED count", cleaned)
        self.assertIn("matrix ADB", cleaned)

    def test_strip_bare_numbers_removes_standalone_numerals_on_request(self):
        raw = "LED count\n\n84\n\nmatrix ADB\n"
        cleaned = clean_markdown(raw, strip_bare_numbers=True)
        self.assertNotIn("84", cleaned.splitlines())
        self.assertIn("LED count", cleaned)
        self.assertIn("matrix ADB", cleaned)

    def test_labelled_page_markers_are_removed_without_the_flag(self):
        raw = "Body\nPage 3 of 12\n4 / 20\n- 5 -\nEnd\n"
        cleaned = clean_markdown(raw)
        for marker in ("Page 3 of 12", "4 / 20", "- 5 -"):
            self.assertNotIn(marker, cleaned)
        self.assertIn("Body", cleaned)
        self.assertIn("End", cleaned)

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
