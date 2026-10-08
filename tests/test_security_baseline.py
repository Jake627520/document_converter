import unittest
from pathlib import Path
import tomllib

class TestSecurityBaseline(unittest.TestCase):
    def test_gitignore_contains_security_exclusions(self):
        root = Path(__file__).parent.parent
        gitignore = (root / ".gitignore").read_text(encoding="utf-8")
        required_patterns = [
            ".env",
            "*.key",
            "converted/",
            "outputs/",
            "*.pdf",
            "*.docx",
            "models/",
        ]
        for pattern in required_patterns:
            self.assertIn(pattern, gitignore, f"Missing pattern in .gitignore: {pattern}")

    def test_pyproject_isolates_optional_engines(self):
        root = Path(__file__).parent.parent
        pyproject_path = root / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Core dependencies must NOT contain marker or mineru/magic-pdf
        core_deps = " ".join(data["project"]["dependencies"]).lower()
        self.assertNotIn("marker", core_deps, "Marker must not be in core dependencies")
        self.assertNotIn("magic-pdf", core_deps, "MinerU/Magic-PDF must not be in core dependencies")

        # Optional dependencies must contain marker and mineru
        opt_deps = data["project"]["optional-dependencies"]
        self.assertIn("marker", opt_deps, "Marker should be isolated in optional-dependencies")
        self.assertIn("mineru", opt_deps, "MinerU should be isolated in optional-dependencies")
        self.assertIn("dev", opt_deps, "Dev dependencies must be present")
        self.assertTrue(any("pip-audit" in dep for dep in opt_deps["dev"]))
        self.assertTrue(any("pip-licenses" in dep for dep in opt_deps["dev"]))

if __name__ == "__main__":
    unittest.main()
