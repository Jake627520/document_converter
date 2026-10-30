"""OpenSpec CHG-005: local web workbench behavior and security boundaries."""
import io
import json
import shutil
import subprocess
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
        # JSON became a real output; a format nothing produces is still refused.
        response = self.client.post(
            "/convert", data={"target": "docx"},
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

    def test_a_model_free_conversion_tells_the_page_so(self):
        # The CLI prints docling-native's quality warning; the page used to
        # download the file and say nothing about the lost structure.
        def convert_with(engine):
            fake = lambda path, engine_name, image_mode: ConversionResult(source=Path(path), engine=engine, markdown="text")
            with mock.patch.object(web_app, "convert_one", side_effect=fake):
                response = self.client.post("/convert", data={"target": "md"}, files={"files": ("a.md", b"text", "text/markdown")})
            self.assertEqual(response.status_code, 200)
            return response.headers
        self.assertEqual(convert_with("docling-native").get("x-conversion-notes"), "model-free")
        self.assertNotIn("x-conversion-notes", convert_with("text_direct"))

    def test_the_page_shows_the_model_free_note_in_every_language(self):
        page = self.client.get("/").text
        self.assertIn("x-conversion-notes", page)
        self.assertIn("note_model_free", page)
        for locale, words in (("en", "tables"), ("zh-TW", "表格"), ("zh-CN", "表格")):
            self.assertIn(words, web_app.TRANSLATIONS[locale]["note_model_free"])

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


def _docling_available() -> bool:
    try:
        import docling  # noqa: F401
        return True
    except Exception:
        return False


requires_docling = unittest.skipUnless(
    _docling_available(),
    "docling not installed; install with: pip install -e '.[docling]'",
)


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



@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class OutputFormatTests(TestCase):
    """The page offers every output a release can actually produce, and no other.

    The README listed Markdown, HTML, Docling JSON and plain text, while the page
    offered only the first two.
    """

    def tearDown(self):
        web_app._RELEASE_PROFILE = None

    @staticmethod
    def offered(page):
        return [value for value in ("md", "html", "txt", "json") if f'value="{value}"' in page]

    def client(self, configure=None):
        web_app._RELEASE_PROFILE = None
        if configure:
            configure()
        return TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def test_each_release_offers_what_it_can_produce(self):
        self.assertEqual(self.offered(self.client().get("/").text), ["md", "html", "txt", "json"])
        pdf_page = self.client(web_app.configure_pdf_release).get("/").text
        self.assertEqual(self.offered(pdf_page), ["md", "html", "txt", "json"])
        self.assertIn("僅 PDF 可輸出", pdf_page)
        # The text release runs no engine, so it has no Docling JSON to give.
        self.assertEqual(self.offered(self.client(web_app.configure_text_release).get("/").text), ["md", "html", "txt"])

    def test_text_release_refuses_a_json_request_outright(self):
        client = self.client(web_app.configure_text_release)
        response = client.post("/convert", data={"target": "json"}, files={"files": ("a.md", b"# A", "text/markdown")})
        self.assertEqual(response.status_code, 400)
        self.assertIn("不提供這種輸出格式", response.json()["detail"])

    def test_plain_text_is_served_as_text_and_keeps_a_text_file_intact(self):
        client = self.client(web_app.configure_text_release)
        body = "#1 priority\n- 5 units\n".encode()
        response = client.post("/convert", data={"target": "txt"}, files={"files": ("notes.txt", body, "text/plain")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
        self.assertEqual(response.content, body)

    def test_markdown_becomes_plain_text(self):
        client = self.client(web_app.configure_text_release)
        response = client.post("/convert", data={"target": "txt"}, files={"files": ("a.md", b"## Spec\n\n- 84\n", "text/markdown")})
        self.assertEqual(response.content.decode(), "Spec\n\n84\n")

    def test_json_for_a_file_no_engine_parsed_says_why(self):
        client = self.client(web_app.configure_pdf_release)
        response = client.post("/convert", data={"target": "json"}, files={"files": ("a.md", b"# A", "text/markdown")})
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertIn("Docling JSON", detail)
        self.assertIn("沒有經過引擎解析", detail)

    @requires_docling
    def test_json_for_a_pdf_is_the_docling_document(self):
        client = self.client(web_app.configure_pdf_release)
        with tempfile.TemporaryDirectory() as temp:
            sample = write_text_pdf(Path(temp) / "spec.pdf", "Headlamp module 84 lumens & bright")
            response = client.post("/convert", data={"target": "json"}, files={"files": ("spec.pdf", sample.read_bytes(), "application/pdf")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json; charset=utf-8")
        document = json.loads(response.content)
        self.assertEqual(document["schema_name"], "DoclingDocument")
        self.assertIn("84 lumens & bright", response.content.decode())



@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class RejectionMessageTests(TestCase):
    """A refusal has to say what happened and what would work instead.

    Half of these answered in English on a Traditional Chinese page, and none
    named the formats the release accepts.
    """

    def tearDown(self):
        web_app._RELEASE_PROFILE = None

    def client(self, configure=None):
        web_app._RELEASE_PROFILE = None
        if configure:
            configure()
        return TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def post(self, client, name, body, target="md", kind="application/octet-stream"):
        return client.post("/convert", data={"target": target}, files={"files": (name, body, kind)})

    def test_unsupported_input_names_what_the_release_accepts(self):
        for configure, accepted, refused in (
            (web_app.configure_text_release, ".markdown、.md、.txt", ".pdf"),
            (web_app.configure_pdf_release, ".markdown、.md、.pdf、.txt", ".docx"),
        ):
            client = self.client(configure)
            with self.subTest(accepted=accepted):
                response = self.post(client, f"report{refused}", b"stub")
                self.assertEqual(response.status_code, 400)
                detail = response.json()["detail"]
                self.assertIn(refused, detail)
                self.assertIn(accepted, detail)

    def test_a_file_without_a_suffix_is_named_as_such(self):
        detail = self.post(self.client(web_app.configure_pdf_release), "noext", b"hello").json()["detail"]
        self.assertIn("沒有副檔名", detail)
        self.assertNotIn("「」", detail)

    def test_size_and_count_limits_state_the_limit(self):
        client = self.client(web_app.configure_text_release)
        oversize = self.post(client, "big.md", b"x" * (web_app.MAX_FILE_BYTES + 1), kind="text/markdown")
        self.assertEqual(oversize.status_code, 413)
        self.assertIn("24 MiB（約 25 MB）", oversize.json()["detail"])
        many = client.post("/convert", data={"target": "md"}, files=[
            ("files", (f"f{index}.md", b"# A", "text/markdown")) for index in range(web_app.MAX_FILE_COUNT + 1)
        ])
        self.assertEqual(many.status_code, 400)
        self.assertIn(f"1 到 {web_app.MAX_FILE_COUNT}", many.json()["detail"])

    def test_a_request_with_no_file_is_answered_in_plain_language(self):
        response = self.client(web_app.configure_text_release).post("/convert", data={"target": "md"})
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("請先選擇", detail)
        # Not FastAPI's own validation structure, which tells the reader nothing.
        self.assertNotIn("loc", detail)
        self.assertNotIn("Field required", detail)

    def test_an_invalid_output_lists_only_what_this_release_offers(self):
        text = self.post(self.client(web_app.configure_text_release), "a.md", b"# A", target="docx").json()["detail"]
        self.assertIn("Markdown", text)
        self.assertNotIn("Docling JSON", text)
        pdf = self.post(self.client(web_app.configure_pdf_release), "a.md", b"# A", target="docx").json()["detail"]
        self.assertIn("Docling JSON", pdf)

    def test_a_text_file_that_is_not_utf8_says_so_and_how_to_fix_it(self):
        response = self.post(self.client(web_app.configure_text_release), "規格.txt",
                             "車燈規格 84".encode("big5"), kind="text/plain")
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertIn("UTF-8", detail)
        self.assertIn("Big5", detail)
        self.assertIn("規格.txt", detail)


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class EmptyResultTests(TestCase):
    """A conversion that recovered nothing must say so, not send an empty file.

    The guard this replaces ran only in the pdf release and recognised only one
    engine's warning, so a full install returned 200 with a lone image
    placeholder - the empty download it exists to prevent.
    """

    def tearDown(self):
        web_app._RELEASE_PROFILE = None

    def convert(self, configure, name, body, kind="application/pdf"):
        web_app._RELEASE_PROFILE = None
        if configure:
            configure()
        client = TestClient(web_app.app, headers={"host": "127.0.0.1"})
        return client.post("/convert", data={"target": "md"}, files={"files": (name, body, kind)})

    @requires_docling
    def test_a_pdf_with_no_text_layer_is_refused_in_every_release(self):
        with tempfile.TemporaryDirectory() as temp:
            scan = write_scanned_pdf(Path(temp) / "scan.pdf").read_bytes()
        for configure in (web_app.configure_pdf_release, None):
            with self.subTest(release=configure and configure.__name__ or "full install"):
                response = self.convert(configure, "scan.pdf", scan)
                self.assertEqual(response.status_code, 422)
                self.assertIn("沒有抽出任何文字", response.json()["detail"])

    def test_an_empty_text_file_is_refused_rather_than_downloaded_empty(self):
        response = self.convert(web_app.configure_text_release, "empty.md", b"   \n\n  ", "text/markdown")
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertIn("沒有抽出任何文字", detail)
        # A Markdown-and-text release has no scan or picture to blame.
        self.assertNotIn("掃描", detail)
        self.assertNotIn("OCR", detail)

    @requires_docling
    def test_the_reason_names_ocr_only_where_a_scan_could_arrive(self):
        with tempfile.TemporaryDirectory() as temp:
            scan = write_scanned_pdf(Path(temp) / "scan.pdf").read_bytes()
        release = self.convert(web_app.configure_pdf_release, "scan.pdf", scan).json()["detail"]
        self.assertIn("此版本不包含 OCR", release)
        full = self.convert(None, "scan.pdf", scan).json()["detail"]
        self.assertIn("OCR", full)
        self.assertIn("引擎", full)

    def test_only_a_source_install_is_told_which_ocr_engines_to_install(self):
        # A packaged app cannot install an engine, so only a source install
        # is pointed at Marker, MinerU and list-engines.
        scan = ConversionResult(source=Path("scan.pdf"), engine="docling-native", markdown="")
        for locale in ("en", "zh-TW", "zh-CN"):
            with self.subTest(locale=locale):
                with mock.patch.object(web_app, "_RELEASE_PROFILE", None):
                    source = web_app._no_text_recovered(scan, locale)
                for name in ("Marker", "MinerU", "document-converter list-engines"):
                    self.assertIn(name, source)
                with mock.patch.object(web_app, "_RELEASE_PROFILE", web_app.PDF_PROFILE):
                    release = web_app._no_text_recovered(scan, locale)
                self.assertNotIn("Marker", release)
                self.assertNotIn("list-engines", release)

    def test_a_caption_beside_an_unreadable_image_still_converts(self):
        # Some text with a picture is a real document, not an empty result.
        result = ConversionResult(source=Path("fig.pdf"), engine="mock", markdown="圖 1：配光曲線\n\n<!-- image -->\n")
        self.assertTrue(result.has_recovered_text())
        self.assertFalse(ConversionResult(source=Path("x.pdf"), engine="mock", markdown="<!-- image -->\n").has_recovered_text())



@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class EngineFailureMessageTests(TestCase):
    """A failed conversion has to name what the user can act on.

    A from-source install without Word support answered a .docx upload with
    the engine chain's English text, naming the generated temporary file and
    the internal word "All engines failed".
    """

    def setUp(self):
        web_app._RELEASE_PROFILE = None
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def post_failing(self, *failures):
        """Upload a .docx while every engine fails as given; failures name the real temp path."""
        from document_converter.engines.base import EngineError

        def fail(path, engine_name, image_mode):
            raised = []
            for make in failures:
                raised.append(make(path))
            message = "All engines failed:\n" + "\n".join(f"docling: {error}" for error in raised)
            raise EngineError(message, failures=raised)

        with mock.patch.object(web_app, "convert_one", side_effect=fail):
            return self.client.post(
                "/convert", data={"target": "md"},
                files={"files": ("規格書.docx", b"PK\x03\x04", "application/octet-stream")},
            )

    @staticmethod
    def missing_package(path):
        from document_converter.engines.base import EngineError
        cause = ModuleNotFoundError("No module named 'docx'", name="docx")
        try:
            try:
                raise cause
            except ModuleNotFoundError as missing:
                raise ImportError(
                    "The 'python-docx' package is required to process Word files. "
                    "Install it with `pip install 'docling-slim[format-docx]'`."
                ) from missing
        except ImportError as error:
            wrapped = EngineError(f"Docling failed for {path}: {error}")
            wrapped.__cause__ = error
            return wrapped

    @staticmethod
    def broken_file(path):
        from document_converter.engines.base import EngineError
        return EngineError(f"Conversion failed for: {path.name} with status: failure")

    def test_missing_package_is_named_with_how_to_install_it(self):
        response = self.post_failing(self.missing_package)
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(
            detail,
            "這個安裝缺少轉換「規格書.docx」所需的元件（Python 模組 docx），所以無法轉換。"
            "安裝方式：pip install 'docling-slim[format-docx]'",
        )

    def test_missing_package_without_an_install_hint_points_to_the_readme(self):
        from document_converter.engines.base import EngineError

        def bare(path):
            wrapped = EngineError(f"Docling is not installed for {path}")
            wrapped.__cause__ = ImportError("No module named 'docling'", name="docling")
            return wrapped

        detail = self.post_failing(bare).json()["detail"]
        self.assertIn("（Python 模組 docling）", detail)
        self.assertIn("請依 README「從原始碼執行」一節安裝對應的引擎後再試。", detail)

    def test_a_broken_file_is_not_blamed_on_a_missing_package(self):
        detail = self.post_failing(self.missing_package, self.broken_file).json()["detail"]
        self.assertTrue(detail.startswith("轉換失敗。請確認檔案內容與本機已安裝的引擎。"), detail)
        self.assertNotIn("缺少", detail)

    def test_an_import_handled_earlier_is_not_the_cause(self):
        from document_converter.engines.base import EngineError

        def handled_then_failed(path):
            try:
                raise ImportError("optional accelerator missing")
            except ImportError:
                # Raised while handling, without "from": __context__, not __cause__.
                try:
                    raise EngineError(f"Conversion failed for: {path.name}")
                except EngineError as error:
                    return error

        detail = self.post_failing(handled_then_failed).json()["detail"]
        self.assertTrue(detail.startswith("轉換失敗。"), detail)

    def test_failure_names_the_upload_not_the_temporary_file(self):
        for failure in (self.missing_package, self.broken_file):
            with self.subTest(failure=failure.__name__):
                detail = self.post_failing(failure).json()["detail"]
                self.assertIn("「規格書.docx」", detail)
                self.assertNotIn("input-", detail)
                self.assertNotIn("/tmp", detail)


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class TextReleaseEngineBoundaryTests(TestCase):
    """The text release must convert without loading engine code.

    Routing its Markdown and text through TextDirectEngine imported
    document_converter.engines, whose __init__ loads every adapter, and the
    frozen text app then refused to start. Only the release runtime job, which
    runs separately, caught it. This runs the text release's conversions in a
    fresh interpreter and lists what they loaded.
    """

    SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[1] + "/scripts/packaging")
import profiles
from fastapi.testclient import TestClient
from document_converter import web_app
web_app.configure_text_release()
client = TestClient(web_app.app, headers={"host": "127.0.0.1"})
answers = [
    client.post("/convert", data={"target": "md"}, files={"files": ("notes.md", "# 本機\\n".encode(), "text/markdown")}),
    client.post("/convert", data={"target": "md"}, files={"files": ("big5.txt", "規格".encode("big5"), "text/plain")}),
]
own = [name for name in profiles.TEXT.forbidden if name.startswith("document_converter")]
loaded = sorted(m for m in sys.modules if any(m == name or m.startswith(name + ".") for name in own))
print(json.dumps({"status": [a.status_code for a in answers], "big5": answers[1].json()["detail"], "loaded": loaded}))
"""

    def test_text_release_conversions_load_no_forbidden_module(self):
        import subprocess
        import sys

        root = Path(__file__).resolve().parent.parent
        run = subprocess.run([sys.executable, "-c", self.SCRIPT, str(root)], capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(report["loaded"], [])
        self.assertEqual(report["status"], [200, 422])
        self.assertIn("不是 UTF-8 編碼的文字檔", report["big5"])


class SizeLimitWordingTests(TestCase):
    """A limit is stated in both units, and the page agrees with the server.

    The limits are set in mebibytes, while Finder reports decimal megabytes; a
    page that said only "24 MiB" left most readers unsure what it meant, and
    its size display divided by 1,048,576 while labelling the result "MB", so a
    file Finder lists as 25.2 MB appeared as 24.0 MB.
    """

    @unittest.skipIf(web_app is None, "install the optional web extra to run web tests")
    def test_both_units_are_derived_from_the_same_byte_limit(self):
        self.assertEqual(web_app.size_limit(24 * 1024 * 1024), "24 MiB（約 25 MB）")
        self.assertEqual(web_app.size_limit(25 * 1024 * 1024), "25 MiB（約 26 MB）")

    @unittest.skipIf(web_app is None, "install the optional web extra to run web tests")
    def test_the_page_states_the_limit_the_server_enforces(self):
        stated = web_app.size_limit(web_app.MAX_FILE_BYTES)
        page = web_app.PAGE
        # The hint and both client-side refusals name the same limit.
        self.assertGreaterEqual(page.count(stated), 3, stated)
        # And the client checks the same number of bytes the server does.
        self.assertIn(f"{web_app.MAX_FILE_BYTES // 1048576}*1048576", page)

    @unittest.skipIf(web_app is None, "install the optional web extra to run web tests")
    def test_the_page_shows_sizes_the_way_finder_does(self):
        # Decimal, so the page and Finder show one number for one file.
        self.assertIn("(n/1e6).toFixed(1)+' MB'", web_app.PAGE)
        self.assertNotIn("(n/1048576).toFixed(1)+' MB'", web_app.PAGE)


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class CspAndResponseHeaderTests(TestCase):
    def setUp(self):
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def test_get_page_includes_strict_csp_and_security_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("content-security-policy", response.headers)
        csp = response.headers["content-security-policy"]
        self.assertIn("default-src 'none'", csp)
        self.assertIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("style-src 'self' 'unsafe-inline'", csp)
        self.assertIn("img-src 'self' data: blob:", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("frame-src 'self' blob: data:", csp)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("referrer-policy"), "no-referrer")

    def test_post_convert_includes_security_headers(self):
        response = self.client.post(
            "/convert",
            data={"target": "md"},
            files={"files": ("notes.md", b"# hello", "text/markdown")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("content-security-policy", response.headers)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class PreviewBoundaryTests(TestCase):
    def setUp(self):
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def test_workbench_page_contains_isolated_preview_frame(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Verify an iframe with sandbox attribute is present for HTML preview
        self.assertIn('<iframe', response.text)
        self.assertIn('sandbox=', response.text)
        # Sandbox MUST NOT permit scripts in converted HTML
        self.assertNotIn('allow-scripts', response.text)
        # Copy to clipboard button
        self.assertIn('id="copy-preview"', response.text)


@unittest.skipIf(TestClient is None, "install the optional web extra to run web tests")
class InternationalizationTests(TestCase):
    def setUp(self):
        self.client = TestClient(web_app.app, headers={"host": "127.0.0.1"})

    def test_page_contains_language_selector_with_all_supported_locales(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="lang-select"', response.text)
        self.assertIn('value="en"', response.text)
        self.assertIn('value="zh-TW"', response.text)
        self.assertIn('value="zh-CN"', response.text)

    def test_all_translations_have_matching_keys(self):
        translations = web_app.TRANSLATIONS
        self.assertEqual(set(translations.keys()), {"en", "zh-TW", "zh-CN"})
        tw_keys = set(translations["zh-TW"].keys())
        en_keys = set(translations["en"].keys())
        cn_keys = set(translations["zh-CN"].keys())
        self.assertEqual(tw_keys, en_keys)
        self.assertEqual(tw_keys, cn_keys)

    def test_negotiated_language_rendering_via_query_param(self):
        res_en = self.client.get("/?lang=en")
        self.assertEqual(res_en.status_code, 200)
        self.assertIn('lang="en"', res_en.text)
        self.assertIn("Local Only", res_en.text)

        res_cn = self.client.get("/?lang=zh-CN")
        self.assertEqual(res_cn.status_code, 200)
        self.assertIn('lang="zh-CN"', res_cn.text)
        self.assertIn("仅限本地使用", res_cn.text)

        res_tw = self.client.get("/?lang=zh-TW")
        self.assertEqual(res_tw.status_code, 200)
        self.assertIn('lang="zh-TW"', res_tw.text)
        self.assertIn("僅限本機使用", res_tw.text)

    def test_three_part_language_tag_renders_chinese(self):
        res = self.client.get("/", headers={"accept-language": "zh-Hant-TW,zh;q=0.9"})
        self.assertIn('lang="zh-TW"', res.text)
        res = self.client.get("/?lang=zh-Hans-CN")
        self.assertIn('lang="zh-CN"', res.text)

    def test_page_detects_browser_language_by_script_then_region(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "node is required to run the page's detectLanguage()")
        page = self.client.get("/").text
        start = page.index("function detectLanguage()")
        end = page.index("\n", start)
        cases = {
            "zh-Hant-TW": "zh-TW", "zh-Hant-HK": "zh-TW", "ZH-HANT-TW": "zh-TW",
            "zh-Hans-CN": "zh-CN", "zh-Hans-TW": "zh-CN", "zh-Hans-HK": "zh-CN",
            "zh-TW": "zh-TW", "zh-HK": "zh-TW", "zh-MO": "zh-TW", "zh-Hant": "zh-TW",
            "zh-CN": "zh-CN", "zh-SG": "zh-CN", "zh-Hans": "zh-CN", "zh": "zh-CN",
            "zh_TW": "zh-TW", "en-GB": "en", "fr-FR": "en", "": "en",
        }
        script = (
            "const I18N={};const localStorage={getItem(){return null}};"
            f"{page[start:end]}\n"
            f"const cases={json.dumps(cases)};const got={{}};"
            "for(const tag of Object.keys(cases)){"
            # Node defines its own read-only navigator, so replace the property.
            "Object.defineProperty(globalThis,'navigator',"
            "{value:{languages:[tag],language:tag},configurable:true});got[tag]=detectLanguage()}"
            "console.log(JSON.stringify(got))"
        )
        out = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), cases)

    def test_unsupported_language_falls_back_to_english(self):
        res = self.client.get("/?lang=fr-FR")
        self.assertEqual(res.status_code, 200)
        self.assertIn('lang="en"', res.text)
        self.assertIn("Local Only", res.text)

    def test_error_message_is_localized_when_requested(self):
        # Client requests English via Accept-Language
        res_en = self.client.post(
            "/convert",
            data={"target": "invalid_format"},
            files={"files": ("notes.md", b"hello", "text/markdown")},
            headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        self.assertEqual(res_en.status_code, 400)
        self.assertIn("Please choose an output format", res_en.json()["detail"])

        # Default without preference remains Traditional Chinese for backward compatibility
        res_tw = self.client.post(
            "/convert",
            data={"target": "invalid_format"},
            files={"files": ("notes.md", b"hello", "text/markdown")},
        )
        self.assertEqual(res_tw.status_code, 400)
        self.assertIn("請選擇一種輸出格式", res_tw.json()["detail"])

    def test_unsupported_format_error_is_localized_in_en_and_zh_cn(self):
        res_en = self.client.post(
            "/convert",
            data={"target": "md"},
            files={"files": ("doc.xyz", b"hello", "application/octet-stream")},
            headers={"Accept-Language": "en"},
        )
        self.assertEqual(res_en.status_code, 400)
        self.assertIn("does not support '.xyz' files", res_en.json()["detail"])

        res_cn = self.client.post(
            "/convert",
            data={"target": "md"},
            files={"files": ("doc.xyz", b"hello", "application/octet-stream")},
            headers={"Accept-Language": "zh-CN"},
        )
        self.assertEqual(res_cn.status_code, 400)
        self.assertIn("不支持「.xyz」文件", res_cn.json()["detail"])

    def test_oversize_single_file_error_is_localized_in_en_and_zh_cn(self):
        big = b"x" * (web_app.MAX_FILE_BYTES + 1)
        res_en = self.client.post(
            "/convert",
            data={"target": "md"},
            files={"files": ("big.md", big, "text/markdown")},
            headers={"Accept-Language": "en"},
        )
        self.assertEqual(res_en.status_code, 413)
        self.assertIn("Single file must not exceed", res_en.json()["detail"])

        res_cn = self.client.post(
            "/convert",
            data={"target": "md"},
            files={"files": ("big.md", big, "text/markdown")},
            headers={"Accept-Language": "zh-CN"},
        )
        self.assertEqual(res_cn.status_code, 413)
        self.assertIn("单文件不得超过", res_cn.json()["detail"])

    def test_security_boundary_errors_are_localized_with_accept_language(self):
        # Invalid host header
        r_en = self.client.get("/", headers={"host": "evil.com", "accept-language": "en"})
        self.assertEqual(r_en.status_code, 400)
        self.assertIn("Please open using http://127.0.0.1", r_en.text)

        r_cn = self.client.get("/", headers={"host": "evil.com", "accept-language": "zh-CN"})
        self.assertEqual(r_cn.status_code, 400)
        self.assertIn("请使用 http://127.0.0.1", r_cn.text)

        # Cross-site request
        r_cs_en = self.client.post("/convert", headers={"sec-fetch-site": "cross-site", "accept-language": "en"})
        self.assertEqual(r_cs_en.status_code, 403)
        self.assertIn("Cross-site requests are not accepted", r_cs_en.text)

    def test_page_attributes_are_localized_per_language(self):
        res_en = self.client.get("/?lang=en")
        self.assertIn('aria-label="Language selection"', res_en.text)
        self.assertIn('title="Document Preview"', res_en.text)

        res_cn = self.client.get("/?lang=zh-CN")
        self.assertIn('aria-label="选择语言"', res_cn.text)
        self.assertIn('title="文档预览"', res_cn.text)

        res_tw = self.client.get("/?lang=zh-TW")
        self.assertIn('aria-label="選擇語言"', res_tw.text)
        self.assertIn('title="文件預覽"', res_tw.text)

