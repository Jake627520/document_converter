"""Release integration checks without installing test dependencies.

Each reviewed profile runs the real launcher from its own isolated build
environment: `text` from build/private-release/venv, `pdf` from
build/private-release/venv-pdf. A profile whose environment is absent is
skipped, so this file is safe to run from a plain checkout.
"""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pdf_samples import write_scanned_pdf, write_text_pdf

ROOT = Path(__file__).resolve().parents[1]
BUILD_PYTHON = ROOT / "build/private-release/venv/bin/python"
PDF_BUILD_PYTHON = ROOT / "build/private-release/venv-pdf/bin/python"
LAUNCHER = ROOT / "scripts/packaging/release_launcher.py"


class ReleaseRuntimeMixin:
    """Start the launcher from an isolated build environment and talk to it."""

    build_python = BUILD_PYTHON
    launch_arguments: tuple[str, ...] = ()

    @classmethod
    def launcher_command(cls, *arguments):
        argv = [str(LAUNCHER), *cls.launch_arguments, *arguments]
        return [
            str(cls.build_python),
            "-I",
            "-c",
            f"import runpy,sys;sys.path.insert(0,{str(ROOT)!r});sys.argv={argv!r};"
            f"runpy.run_path({str(LAUNCHER)!r},run_name='__main__')",
        ]

    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.process = subprocess.Popen(
            cls.launcher_command("--no-browser", "--port", str(cls.port)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(200):
            try:
                with urlopen(cls.base, timeout=0.2):
                    return
            except OSError:
                if cls.process.poll() is not None:
                    raise RuntimeError(cls.process.communicate()[1])
                time.sleep(0.05)
        cls.process.terminate()
        cls.process.wait(timeout=5)
        raise RuntimeError("Isolated release did not start")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=5)

    def request_conversion(self, filename, data, target="md", headers=None):
        boundary = "release-smoke-boundary"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"target\"\r\n\r\n{target}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = Request(self.base + "/convert", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}", **(headers or {})})
        try:
            with urlopen(request, timeout=60) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def diagnostics(self):
        result = subprocess.run(self.launcher_command("--diagnostics"), check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def assert_shared_behavior(self):
        """Checks every profile must pass."""
        data = "# Release smoke\n\n**本機文件**\n".encode()
        self.assertEqual(self.request_conversion("notes.md", data), (200, data))
        status, html = self.request_conversion("notes.markdown", data, "html")
        self.assertEqual(status, 200)
        self.assertIn(b"<h1>Release smoke</h1>", html)
        self.assertIn("<strong>本機文件</strong>".encode(), html)
        status, html = self.request_conversion("plain.txt", "本機 UTF-8 文字".encode(), "html")
        self.assertEqual(status, 200)
        self.assertIn("<p>本機 UTF-8 文字</p>".encode(), html)
        self.assertEqual(self.request_conversion("plain.txt", b"\xff")[0], 422)
        # Plain text from every release: a text file comes back untouched, since
        # stripping its "#" or "- " would damage real content, and Markdown is
        # rendered.
        plain = "#1 優先\n- 5 件\n".encode()
        self.assertEqual(self.request_conversion("plain.txt", plain, "txt"), (200, plain))
        self.assertEqual(self.request_conversion("spec.md", "## 規格\n\n- 84 流明\n".encode(), "txt"), (200, "規格\n\n84 流明\n".encode()))
        self.assertEqual(self.request_conversion("report.docx", b"stub")[0], 400)
        self.assertEqual(self.request_conversion("notes.md", b"hello", headers={"Origin": "https://attacker.example"})[0], 403)
        try:
            urlopen(Request(self.base, headers={"Host": "attacker.example"}))
            self.fail("Remote Host accepted")
        except HTTPError as exc:
            self.assertEqual(exc.code, 400)
        diagnostic = self.diagnostics()
        self.assertEqual(diagnostic["forbidden_loaded"], [])
        for path in diagnostic["paths"]:
            if "site-packages" in path:
                self.assertTrue(Path(path).resolve().is_relative_to(self.build_python.parents[1].resolve()))
        return diagnostic


@unittest.skipUnless(BUILD_PYTHON.is_file(), "prepare the isolated text release environment first")
class TextReleaseRuntimeTests(ReleaseRuntimeMixin, unittest.TestCase):
    build_python = BUILD_PYTHON
    launch_arguments = ("--profile", "text")

    def test_page_has_only_reviewed_inputs(self):
        with urlopen(self.base) as response:
            page = response.read().decode()
        self.assertIn('accept=".md,.markdown,.txt"', page)
        self.assertIn("此版本不提供 PDF、Office、圖片或 OCR", page)
        self.assertNotIn('accept=".pdf', page)

    def test_pdf_is_rejected(self):
        self.assertEqual(self.request_conversion("sample.pdf", b"%PDF-1.7")[0], 400)

    def test_page_offers_no_docling_json(self):
        with urlopen(self.base) as response:
            page = response.read().decode()
        self.assertIn('value="txt"', page)
        self.assertNotIn('value="json"', page)
        self.assertEqual(self.request_conversion("notes.md", b"# A", "json")[0], 400)

    def test_shared_conversion_and_security_behavior(self):
        diagnostic = self.assert_shared_behavior()
        self.assertEqual(diagnostic["profile"], "text-only")
        self.assertEqual(diagnostic["inputs"], [".markdown", ".md", ".txt"])
        self.assertEqual(diagnostic["outputs"], ["html", "md", "txt"])


@unittest.skipUnless(PDF_BUILD_PYTHON.is_file(), "prepare the isolated pdf release environment first")
class PdfReleaseRuntimeTests(ReleaseRuntimeMixin, unittest.TestCase):
    build_python = PDF_BUILD_PYTHON
    launch_arguments = ("--profile", "pdf")

    def test_page_offers_pdf_and_states_its_limits(self):
        with urlopen(self.base) as response:
            page = response.read().decode()
        self.assertIn('accept=".pdf,.md,.markdown,.txt"', page)
        self.assertIn("僅限已有文字層者", page)
        self.assertIn("此版本不含 OCR", page)

    def test_text_layer_pdf_converts(self):
        with tempfile.TemporaryDirectory() as temp:
            sample = write_text_pdf(Path(temp) / "sample.pdf").read_bytes()
        status, markdown = self.request_conversion("sample.pdf", sample)
        self.assertEqual(status, 200)
        self.assertIn("readable text stream".encode(), markdown)
        status, html = self.request_conversion("sample.pdf", sample, "html")
        self.assertEqual(status, 200)
        self.assertIn(b"<html", html.lower())

    def test_scanned_pdf_is_explained_rather_than_returned_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            sample = write_scanned_pdf(Path(temp) / "scan.pdf").read_bytes()
        status, body = self.request_conversion("scan.pdf", sample)
        self.assertEqual(status, 422)
        self.assertIn("沒有文字層", body.decode())

    def test_docling_json_comes_from_a_pdf_only(self):
        with tempfile.TemporaryDirectory() as temp:
            sample = write_text_pdf(Path(temp) / "sample.pdf").read_bytes()
        status, body = self.request_conversion("sample.pdf", sample, "json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["schema_name"], "DoclingDocument")
        status, body = self.request_conversion("notes.md", b"# A", "json")
        self.assertEqual(status, 422)
        self.assertIn("沒有經過引擎解析", body.decode())

    def test_shared_conversion_and_security_behavior(self):
        diagnostic = self.assert_shared_behavior()
        self.assertEqual(diagnostic["profile"], "pdf-text")
        self.assertEqual(diagnostic["inputs"], [".markdown", ".md", ".pdf", ".txt"])
        self.assertEqual(diagnostic["outputs"], ["html", "json", "md", "txt"])


if __name__ == "__main__":
    unittest.main()
