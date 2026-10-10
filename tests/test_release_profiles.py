"""Reviewed release profiles: what each build may freeze and pin.

These checks run anywhere; they read the packaging modules and the pinned
requirement files rather than a built candidate.
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "scripts/packaging"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, PACKAGING / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


profiles = load("profiles")


def normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def pinned(stem: str) -> dict[str, str]:
    pins = {}
    for line in (PACKAGING / f"{stem}.txt").read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if entry and not entry.startswith("#"):
            name, version = entry.split("==")
            pins[normalized(name)] = version
    return pins


class ProfileDefinitionTests(unittest.TestCase):
    """Ref: openspec/specs/release-profiles/spec.md"""

    def test_text_profile_restrictions_are_unchanged(self):
        """The reviewed text-only candidate must not be weakened by a new profile."""
        text = profiles.TEXT
        self.assertEqual(text.manifest_profile, "text-only")
        for module in ("document_converter.engines", "document_converter.pipeline", "docling", "torch"):
            self.assertIn(module, text.excludes)
            self.assertIn(module, text.forbidden)
        self.assertEqual(text.collect_all, [])
        self.assertEqual(text.sources, profiles.SHARED_SOURCES)

    def test_pdf_profile_keeps_model_runtimes_out(self):
        pdf = profiles.PDF
        self.assertEqual(pdf.manifest_profile, "pdf-text")
        for module in ("torch", "torchvision", "transformers", "fitz", "pymupdf", "marker", "magic_pdf", "mineru"):
            self.assertIn(module, pdf.excludes)
            self.assertIn(module, pdf.forbidden)
        for module in ("document_converter.cli", "document_converter.pipeline", "document_converter.detector"):
            self.assertIn(module, pdf.excludes)
        # The model-free engine is the one thing this profile adds.
        self.assertNotIn("docling", pdf.excludes)
        self.assertNotIn("document_converter.engines", pdf.excludes)
        self.assertIn("document_converter.engines.docling_native_engine", pdf.hidden_imports)
        self.assertIn("engines/docling_native_engine.py", pdf.sources)

    def test_profiles_use_separate_candidates_and_identifiers(self):
        names = {profile.candidate_name for profile in profiles.PROFILES.values()}
        identifiers = {profile.bundle_identifier for profile in profiles.PROFILES.values()}
        stems = {profile.requirements_stem for profile in profiles.PROFILES.values()}
        self.assertEqual(len(names), len(profiles.PROFILES))
        self.assertEqual(len(identifiers), len(profiles.PROFILES))
        self.assertEqual(len(stems), len(profiles.PROFILES))

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(SystemExit):
            profiles.get("ocr")


class PinnedRequirementTests(unittest.TestCase):
    """Ref: openspec/specs/release-profiles/spec.md"""

    def test_each_profile_pins_only_reviewed_distributions(self):
        for profile in profiles.PROFILES.values():
            with self.subTest(profile=profile.name):
                pins = pinned(profile.requirements_stem)
                self.assertTrue(pins)
                self.assertEqual(profile.forbidden_distributions & set(pins), set())

    def test_pdf_profile_pins_the_model_free_stack(self):
        pins = pinned(profiles.PDF.requirements_stem)
        for distribution in ("docling-slim", "docling-core", "docling-parse", "fastapi", "uvicorn", "pyinstaller"):
            self.assertIn(distribution, pins)
        for distribution in ("torch", "torchvision", "transformers", "docling-ibm-models", "accelerate"):
            self.assertNotIn(distribution, pins)

    def test_each_lock_hashes_exactly_its_pinned_distributions(self):
        for profile in profiles.PROFILES.values():
            with self.subTest(profile=profile.name):
                pins = pinned(profile.requirements_stem)
                lock = (PACKAGING / f"{profile.requirements_stem}.lock").read_text(encoding="utf-8")
                locked = dict(re.findall(r"^([A-Za-z0-9_.\-]+)==(\S+?) \\$", lock, re.MULTILINE))
                self.assertEqual({normalized(name): version for name, version in locked.items()}, pins)
                for name, version in locked.items():
                    entry = lock.split(f"{name}=={version} \\", 1)[1]
                    self.assertIn("--hash=sha256:", entry.split("\n    # via", 1)[0])


class SpecRenderingTests(unittest.TestCase):
    """Ref: openspec/specs/release-profiles/spec.md"""

    @classmethod
    def setUpClass(cls):
        cls.build = load("build_macos")

    def render(self, profile):
        return self.build.render_spec(
            profile,
            legal=Path("/tmp/legal"),
            marker=Path("/tmp/marker"),
            inventory=Path("/tmp/FROZEN_INVENTORY.json"),
        )

    def test_every_profile_renders_a_valid_arm64_spec(self):
        for profile in profiles.PROFILES.values():
            with self.subTest(profile=profile.name):
                text = self.render(profile)
                ast.parse(text)
                self.assertIn('target_arch="arm64"', text)
                self.assertIn(profile.bundle_identifier, text)
                self.assertIn(repr(profile.excludes), text)
                self.assertIn(repr(profile.forbidden), text)

    def test_spec_rejects_forbidden_entries_and_outside_packages(self):
        text = self.render(profiles.PDF)
        self.assertIn("Forbidden frozen entry", text)
        self.assertIn("External site-packages entry", text)


class LauncherProfileTests(unittest.TestCase):
    """Ref: openspec/specs/release-profiles/spec.md"""

    @classmethod
    def setUpClass(cls):
        try:
            cls.launcher = load("release_launcher")
        except ImportError as exc:  # uvicorn or fastapi absent
            raise unittest.SkipTest(f"release launcher dependencies missing: {exc}")

    def test_frozen_bundle_reads_its_profile_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / self.launcher.PROFILE_MARKER).write_text("pdf\n", encoding="utf-8")
            with unittest.mock.patch.object(sys, "_MEIPASS", temp, create=True):
                self.assertEqual(self.launcher.frozen_profile(), "pdf")
                (Path(temp) / self.launcher.PROFILE_MARKER).write_text("nonsense\n", encoding="utf-8")
                self.assertIsNone(self.launcher.frozen_profile())
            (Path(temp) / self.launcher.PROFILE_MARKER).unlink()
            with unittest.mock.patch.object(sys, "_MEIPASS", temp, create=True):
                self.assertIsNone(self.launcher.frozen_profile())

    def test_unfrozen_run_has_no_profile_marker(self):
        self.assertIsNone(self.launcher.frozen_profile())

    def test_every_profile_has_a_forbidden_module_list_and_configurator(self):
        for name in profiles.PROFILES:
            self.assertIn(name, self.launcher.FORBIDDEN_MODULES)
            self.assertIn(name, self.launcher.CONFIGURE)
        self.assertIn("torch", self.launcher.FORBIDDEN_MODULES["pdf"])
        self.assertIn("docling", self.launcher.FORBIDDEN_MODULES["text"])
        self.assertNotIn("docling", self.launcher.FORBIDDEN_MODULES["pdf"])


if __name__ == "__main__":
    unittest.main()
