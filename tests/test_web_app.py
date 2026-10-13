"""OpenSpec CHG-005: local web workbench behavior and security boundaries."""
import io
import zipfile
from pathlib import Path
from unittest import TestCase, mock
import unittest
import tempfile

from document_converter.models import ConversionResult
from pdf_samples import write_scanned_pdf, write_text_pdf

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
        # The download is named after the upload, which is why only its last
        # segment is used and the suffix dropped: the traversal is gone, and so
        # is any chance of ending the quoted header value.
        disposition = response.headers["content-disposition"]
        self.assertEqual(disposition, "attachment; filename=\"private name.md\"; filename*=UTF-8''private%20name.md")
        for dangerous in ("..", "/", "\\", "\r", "\n"):
            self.assertNotIn(dangerous, disposition)
        # The file on disk is still a generated name, never the uploaded one.
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


def _native_pdf_available():
    try:
        import docling.pipeline.native_pdf_pipeline  # noqa: F401
    except Exception:
        return False
    return True


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class ReleaseProfileTests(TestCase):
    """Ref: openspec/specs/release-profiles/spec.md"""

    def client_for(self, profile):
        patcher = mock.patch.object(web_app, "_RELEASE_PROFILE", profile)
        patcher.start()
        self.addCleanup(patcher.stop)
        return TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def post(self, client, filename, data, target="md"):
        return client.post("/convert", data={"target": target}, files={"files": (filename, data, "application/octet-stream")})

    def test_text_release_offers_and_accepts_text_only(self):
        client = self.client_for(web_app.TEXT_PROFILE)
        page = client.get("/").text
        self.assertIn('accept=".md,.markdown,.txt"', page)
        self.assertNotIn('accept=".pdf', page)
        self.assertEqual(self.post(client, "notes.md", b"# hi\n").status_code, 200)
        self.assertEqual(self.post(client, "paper.pdf", b"%PDF-1.7").status_code, 400)

    def test_pdf_release_offers_pdf_and_states_its_limits(self):
        client = self.client_for(web_app.PDF_PROFILE)
        page = client.get("/").text
        self.assertIn('accept=".pdf,.md,.markdown,.txt"', page)
        self.assertIn("僅限已有文字層者", page)
        self.assertIn("此版本不含 OCR", page)
        self.assertIn("不下載任何模型", page)

    def test_pdf_release_still_rejects_office_and_image_input(self):
        client = self.client_for(web_app.PDF_PROFILE)
        for filename in ("report.docx", "deck.pptx", "sheet.xlsx", "scan.png"):
            with self.subTest(filename=filename):
                self.assertEqual(self.post(client, filename, b"stub").status_code, 400)

    def test_pdf_release_keeps_converting_text_input(self):
        client = self.client_for(web_app.PDF_PROFILE)
        response = self.post(client, "notes.md", "# 標題\n".encode())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "# 標題\n".encode())

    def test_release_profile_cannot_be_switched_in_one_process(self):
        with mock.patch.object(web_app, "_RELEASE_PROFILE", web_app.TEXT_PROFILE):
            with self.assertRaises(RuntimeError):
                web_app.configure_pdf_release()

    @unittest.skipUnless(_native_pdf_available(), "install docling-slim to convert PDFs")
    def test_pdf_release_converts_a_text_layer_pdf(self):
        client = self.client_for(web_app.PDF_PROFILE)
        with tempfile.TemporaryDirectory() as temp:
            sample = write_text_pdf(Path(temp) / "sample.pdf")
            response = self.post(client, "sample.pdf", sample.read_bytes())
        self.assertEqual(response.status_code, 200)
        self.assertIn("readable text stream", response.text)

    @unittest.skipUnless(_native_pdf_available(), "install docling-slim to convert PDFs")
    def test_pdf_release_explains_a_scanned_pdf_instead_of_returning_nothing(self):
        client = self.client_for(web_app.PDF_PROFILE)
        with tempfile.TemporaryDirectory() as temp:
            sample = write_scanned_pdf(Path(temp) / "scan.pdf")
            response = self.post(client, "scan.pdf", sample.read_bytes())
        self.assertEqual(response.status_code, 422)
        self.assertIn("沒有文字層", response.json()["detail"])
        self.assertIn("OCR", response.json()["detail"])


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class DownloadNamingTests(TestCase):
    """A converted file keeps the name of the document it came from.

    The uploaded name is still never trusted as a path - the file on disk keeps
    a generated name - but discarding it entirely left a batch of spec sheets as
    document-1.md to document-5.md, with no way to tell which was which.
    Hostile name shapes are covered in tests/test_web_security.py, since a
    multipart encoder will not carry a quote or a newline in a filename.
    """

    def setUp(self):
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def convert(self, uploads):
        files = [("files", (name, body, "text/markdown")) for name, body in uploads]
        with mock.patch.object(web_app, "convert_one") as convert:
            convert.side_effect = lambda path, engine, mode: ConversionResult(
                source=Path(path), engine="mock", markdown="# Hello"
            )
            return self.client.post("/convert", data={"target": "md"}, files=files)

    def test_single_download_is_named_after_the_document(self):
        response = self.convert([("車燈規格表_v3.md", b"# Hello")])
        self.assertEqual(response.status_code, 200)
        disposition = response.headers["content-disposition"]
        self.assertIn("filename*=UTF-8''%E8%BB%8A%E7%87%88%E8%A6%8F%E6%A0%BC%E8%A1%A8_v3.md", disposition)
        # A client that reads only `filename` gets the fallback rather than the
        # fragment that dropping the Chinese characters would leave.
        self.assertIn('filename="converted-document.md"', disposition)

    def test_ascii_name_is_carried_in_both_forms(self):
        disposition = self.convert([("resume-1.md", b"# Hello")]).headers["content-disposition"]
        self.assertEqual(disposition, "attachment; filename=\"resume-1.md\"; filename*=UTF-8''resume-1.md")

    def test_archive_entries_keep_their_names_and_do_not_collide(self):
        response = self.convert([
            ("headlamp.md", b"# A"),
            ("headlamp.md", b"# B"),
            ("面板備忘.md", b"# C"),
        ])
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.content)) as bundle:
            self.assertEqual(bundle.namelist(), ["headlamp.md", "headlamp-2.md", "面板備忘.md"])
        self.assertIn('filename="converted-documents.zip"', response.headers["content-disposition"])

    def test_a_name_that_is_only_a_suffix_still_gets_a_download_name(self):
        response = self.convert([(".md", b"# Hello")])
        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="document.md"', response.headers["content-disposition"])
