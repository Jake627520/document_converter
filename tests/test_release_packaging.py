"""Text-only release integration checks without installing test dependencies."""
from __future__ import annotations

import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BUILD_PYTHON = ROOT / "build/private-release/venv/bin/python"
LAUNCHER = ROOT / "scripts/packaging/release_launcher.py"


@unittest.skipUnless(BUILD_PYTHON.is_file(), "prepare the isolated release environment first")
class ReleaseRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        code = f"import runpy,sys;sys.path.insert(0,{str(ROOT)!r});sys.argv=[{str(LAUNCHER)!r},'--no-browser','--port',{str(cls.port)!r}];runpy.run_path({str(LAUNCHER)!r},run_name='__main__')"
        cls.process = subprocess.Popen([str(BUILD_PYTHON), "-I", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(80):
            try:
                with urlopen(cls.base, timeout=0.2):
                    return
            except OSError:
                if cls.process.poll() is not None:
                    raise RuntimeError(cls.process.communicate()[1])
                time.sleep(0.05)
        cls.process.terminate()
        cls.process.wait(timeout=5)
        raise RuntimeError("Isolated text release did not start")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=5)

    def request_conversion(self, filename, data, target="md", headers=None):
        boundary = "release-smoke-boundary"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"target\"\r\n\r\n{target}\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        request = Request(self.base + "/convert", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}", **(headers or {})})
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, exc.read()

    def test_page_has_only_reviewed_inputs(self):
        with urlopen(self.base) as response:
            page = response.read().decode()
        self.assertIn('accept=".md,.markdown,.txt"', page)
        self.assertIn("此版本不提供 PDF、Office、圖片或 OCR", page)
        self.assertNotIn('accept=".pdf', page)

    def test_markdown_round_trip_and_html(self):
        data = "# Release smoke\n\n**本機文件**\n".encode()
        self.assertEqual(self.request_conversion("notes.md", data), (200, data))
        status, html = self.request_conversion("notes.markdown", data, "html")
        self.assertEqual(status, 200)
        self.assertIn(b"<h1>Release smoke</h1>", html)
        self.assertIn("<strong>本機文件</strong>".encode(), html)

    def test_text_to_html(self):
        status, html = self.request_conversion("plain.txt", "本機 UTF-8 文字".encode(), "html")
        self.assertEqual(status, 200)
        self.assertIn("<p>本機 UTF-8 文字</p>".encode(), html)

    def test_pdf_is_rejected(self):
        self.assertEqual(self.request_conversion("sample.pdf", b"%PDF-1.7")[0], 400)

    def test_invalid_utf8_does_not_fall_back_to_engines(self):
        self.assertEqual(self.request_conversion("plain.txt", b"\xff")[0], 422)

    def test_security_boundary_is_shared(self):
        self.assertEqual(self.request_conversion("notes.md", b"hello", headers={"Origin": "https://attacker.example"})[0], 403)
        try:
            urlopen(Request(self.base, headers={"Host": "attacker.example"}))
            self.fail("Remote Host accepted")
        except HTTPError as exc:
            self.assertEqual(exc.code, 400)

    def test_release_does_not_load_optional_engines_or_system_packages(self):
        code = f"import runpy,sys;sys.path.insert(0,{str(ROOT)!r});sys.argv=[{str(LAUNCHER)!r},'--diagnostics'];runpy.run_path({str(LAUNCHER)!r},run_name='__main__')"
        result = subprocess.run([str(BUILD_PYTHON), "-I", "-c", code], check=True, capture_output=True, text=True)
        diagnostic = json.loads(result.stdout)
        self.assertEqual(diagnostic["forbidden_loaded"], [])
        self.assertEqual(diagnostic["profile"], "text-only")
        for path in diagnostic["paths"]:
            if "site-packages" in path:
                self.assertTrue(Path(path).resolve().is_relative_to(BUILD_PYTHON.parents[1].resolve()))


if __name__ == "__main__":
    unittest.main()
