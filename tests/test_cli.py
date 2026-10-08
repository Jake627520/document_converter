import unittest

try:
    from typer.testing import CliRunner
    from document_converter.cli import app
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False

@unittest.skipUnless(HAS_TYPER, "typer not installed in current environment")
class TestCli(unittest.TestCase):
    """Ref: openspec/specs/cli-interface/spec.md"""

    def setUp(self):
        self.runner = CliRunner()

    def test_help_command(self):
        result = self.runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Convert local documents", result.output)

    def test_list_engines_command(self):
        result = self.runner.invoke(app, ["list-engines"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("docling", result.output)
        self.assertIn("marker", result.output)
        self.assertIn("mineru", result.output)

    def test_inspect_fixture(self):
        result = self.runner.invoke(app, ["inspect", "tests/fixtures/sample_text.pdf"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("sample_text.pdf", result.output)
        self.assertIn("text_based", result.output)

if __name__ == "__main__":
    unittest.main()
