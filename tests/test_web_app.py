"""OpenSpec CHG-005: local web workbench behavior and security boundaries."""
from pathlib import Path
from unittest import TestCase, mock
import unittest
import tempfile

try:
    from fastapi.testclient import TestClient
    from document_converter import web_app
except ImportError:
    TestClient = None
    web_app = None


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class WebAppTests(TestCase):
    def setUp(self):
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def test_upload_page_exposes_accessible_conversion_controls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('type="file"', response.text)
        self.assertIn('accept="', response.text)
        self.assertIn('name="target"', response.text)
        self.assertIn('value="md"', response.text)
        self.assertIn('value="html"', response.text)
        self.assertIn('aria-live="polite"', response.text)
        self.assertIn("僅限本機使用", response.text)

    def test_rejects_remote_host(self):
        response = self.client.get("/", headers={"host": "evil.example"})
        self.assertEqual(response.status_code, 400)

    def test_rejects_cross_site_upload_before_form_parsing(self):
        response = self.client.post(
            "/convert", data={"target": "md"},
            files={"files": ("notes.md", b"hello", "text/markdown")},
            headers={"sec-fetch-site": "cross-site", "origin": "https://attacker.example"},
        )
        self.assertEqual(response.status_code, 403)

    def test_rejects_foreign_origin(self):
        response = self.client.post(
            "/convert", data={"target": "md"},
            files={"files": ("notes.md", b"hello", "text/markdown")},
            headers={"origin": "https://attacker.example"},
        )
        self.assertEqual(response.status_code, 403)

    def test_rejects_unsupported_upload_suffix(self):
        response = self.client.post(
            "/convert", data={"target": "md"},
            files={"files": ("payload.exe", b"ignored", "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_target(self):
        response = self.client.post(
            "/convert", data={"target": "json"},
            files={"files": ("notes.md", b"hello", "text/markdown")},
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch.object(web_app, "convert_one")
    def test_success_uses_generated_temp_path_and_returns_safe_download(self, convert):
        from document_converter.models import ConversionResult
        seen = {}
        def fake_convert(path, engine_name, image_mode):
            seen["path"] = Path(path)
            seen["name"] = Path(path).name
            seen["exists_during_conversion"] = Path(path).exists()
            return ConversionResult(source=Path(path), engine="mock", markdown="# Hello")
        convert.side_effect = fake_convert
        response = self.client.post(
            "/convert", data={"target": "md"},
            files={"files": ("../../private name.md", b"# Hello", "text/markdown")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"# Hello")
        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="converted-document.md"')
        self.assertNotIn("private", response.headers["content-disposition"])
        self.assertNotIn("private", seen["name"])
        self.assertTrue(seen["exists_during_conversion"])
        self.assertFalse(seen["path"].exists())

    @mock.patch.object(web_app, "convert_one", side_effect=RuntimeError("conversion failed"))
    def test_failure_returns_error_and_cleans_temp_upload(self, _convert):
        created = []
        real_tempdir = tempfile.TemporaryDirectory
        def tracked_tempdir(*args, **kwargs):
            directory = real_tempdir(*args, **kwargs)
            created.append(Path(directory.name))
            return directory
        with mock.patch.object(web_app.tempfile, "TemporaryDirectory", side_effect=tracked_tempdir):
            response = self.client.post(
                "/convert", data={"target": "md"},
                files={"files": ("notes.md", b"hello", "text/markdown")},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(created), 1)
        self.assertFalse(created[0].exists())

    def test_rejects_body_over_limit(self):
        with mock.patch.object(web_app, "MAX_REQUEST_BYTES", 64):
            response = self.client.post("/convert", content=b"x" * 100,
                                        headers={"content-type": "application/octet-stream"})
        self.assertEqual(response.status_code, 413)
