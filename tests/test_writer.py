import tempfile
import unittest
from pathlib import Path
from document_converter.models import ConversionResult
from document_converter.writer import write_result

class TestWriter(unittest.TestCase):
    def test_write_markdown(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="# Hello\n", text="Hello\n")
            write_result(result, tmp_path / "out", ["md"])
            self.assertEqual((tmp_path / "out" / "a.md").read_text(), "# Hello\n")

    def test_html_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="# Hello\n")
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<title>a</title>", html)
            self.assertIn("<h1>Hello</h1>", html)
            self.assertIn("<style>", html)

    def test_html_fallback_renders_tables_lists_and_escapes_html(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            md = "| H |\n| --- |\n| <script> |\n\n- item"
            result = ConversionResult(source=src, engine="test", markdown=md)
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<table>", html)
            self.assertIn("<ul><li>item</li></ul>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<script>", html)

    def test_native_html_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            native_html = "<html><body>native</body></html>"
            result = ConversionResult(source=src, engine="test", markdown="# fallback", html=native_html)
            write_result(result, tmp_path / "out", ["html"])
            self.assertEqual((tmp_path / "out" / "a.html").read_text(), native_html)

    def test_empty_markdown_still_writes_html_document(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            src = tmp_path / "a.pdf"
            src.write_bytes(b"")
            result = ConversionResult(source=src, engine="test", markdown="")
            write_result(result, tmp_path / "out", ["html"])
            html = (tmp_path / "out" / "a.html").read_text()
            self.assertIn("<!doctype html>", html)
            self.assertEqual(result.warnings, [])

    def test_referenced_images_map_markdown_and_html_to_nested_assets(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            md = (
                "![figure](<assets/chapter/figure 1.png>)\n\n"
                "[ordinary link](assets/chapter/figure%201.png)\n\n"
                "```md\n![example](assets/chapter/figure%201.png)\n```\n"
            )
            html = '<html><body><img src="assets/chapter/figure 1.png"></body></html>'
            result = ConversionResult(
                source=src,
                engine="test",
                markdown=md,
                html=html,
                assets={"assets/chapter/figure 1.png": b"image"},
            )

            write_result(result, root / "out", ["md", "html"], image_mode="referenced")

            expected_ref = "paper_assets/assets/chapter/figure%201.png"
            self.assertIn(f"](<{expected_ref}>)", (root / "out" / "paper.md").read_text())
            output_md = (root / "out" / "paper.md").read_text()
            self.assertIn("[ordinary link](assets/chapter/figure%201.png)", output_md)
            self.assertIn("![example](assets/chapter/figure%201.png)", output_md)
            self.assertIn(f'src="{expected_ref}"', (root / "out" / "paper.html").read_text())
            self.assertEqual(
                (root / "out" / "paper_assets" / "assets" / "chapter" / "figure 1.png").read_bytes(),
                b"image",
            )

    def test_native_html_external_data_and_non_image_links_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            native_html = (
                '<html><body><img src="assets/image.png">'
                '<img src=assets/unquoted.png>'
                '<img src="https://example.test/image.png">'
                '<img src="data:image/png;base64,AAAA">'
                '<a href="assets/image.png">link</a>'
                '<!-- <img src="assets/image.png"> -->'
                '<script>const example = \'<img src="assets/image.png">\';</script>'
                '<style>.x::after{content: \'<img src="assets/image.png">\';}</style>'
                '<textarea><img src="assets/image.png"></textarea>'
                '<!-- <img src="assets/image.png">'
            )
            result = ConversionResult(
                source=src,
                engine="test",
                html=native_html,
                assets={"assets/image.png": b"image", "assets/unquoted.png": b"unquoted"},
            )

            write_result(result, root / "out", ["html"], image_mode="referenced")

            html = (root / "out" / "paper.html").read_text()
            self.assertIn('<img src="paper_assets/assets/image.png">', html)
            self.assertIn('<img src=paper_assets/assets/unquoted.png>', html)
            self.assertIn('<img src="https://example.test/image.png">', html)
            self.assertIn('<img src="data:image/png;base64,AAAA">', html)
            self.assertIn('<a href="assets/image.png">link</a>', html)
            self.assertIn('<!-- <img src="assets/image.png"> -->', html)
            self.assertIn('<script>const example = \'<img src="assets/image.png">\';</script>', html)
            self.assertIn('<style>.x::after{content: \'<img src="assets/image.png">\';}</style>', html)
            self.assertIn('<textarea><img src="assets/image.png"></textarea>', html)
            self.assertIn('<!-- <img src="assets/image.png">', html)

    def test_referenced_images_map_fallback_html_and_preserve_external_uris(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            md = (
                "![local](images/local.png)\n\n"
                "![remote](https://example.test/image.png)\n\n"
                "![embedded](data:image/png;base64,AAAA)\n\n"
                "![unmatched](paper_assets/not-returned.png)"
            )
            result = ConversionResult(
                source=src,
                engine="test",
                markdown=md,
                assets={"images/local.png": b"local"},
            )

            write_result(result, root / "out", ["html"], image_mode="referenced")

            html = (root / "out" / "paper.html").read_text()
            self.assertIn('src="paper_assets/images/local.png"', html)
            self.assertIn("![remote](https://example.test/image.png)", html)
            self.assertIn("![embedded](data:image/png;base64,AAAA)", html)
            self.assertIn("![unmatched](paper_assets/not-returned.png)", html)
            self.assertNotIn('src="paper_assets/not-returned.png"', html)

    def test_referenced_asset_paths_reject_traversal_absolute_and_windows_paths(self):
        bad_names = ["../secret.png", "/tmp/secret.png", "C:/secret.png", "..\\secret.png"]
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            result = ConversionResult(
                source=src,
                engine="test",
                markdown="![bad](../secret.png)",
                assets={name: b"unsafe" for name in bad_names},
            )

            write_result(result, root / "out", ["md"], image_mode="referenced")

            self.assertEqual((root / "out" / "paper.md").read_text(), "![bad](../secret.png)")
            self.assertFalse((root / "out" / "paper_assets").exists())
            self.assertEqual(len(result.warnings), len(bad_names))

    def test_referenced_asset_casefold_collisions_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            result = ConversionResult(
                source=src,
                engine="test",
                markdown="![one](images/Figure.png) ![two](images/figure.png)",
                assets={"images/Figure.png": b"one", "images/figure.png": b"two"},
            )

            write_result(result, root / "out", ["md"], image_mode="referenced")

            self.assertEqual(
                (root / "out" / "paper.md").read_text(),
                "![one](images/Figure.png) ![two](images/figure.png)",
            )
            self.assertFalse((root / "out" / "paper_assets").exists())
            self.assertEqual(len(result.warnings), 2)

    def test_referenced_assets_reject_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            output = root / "out"
            assets = output / "paper_assets"
            assets.mkdir(parents=True)
            escaped = root / "outside"
            escaped.mkdir()
            (assets / "assets").symlink_to(escaped, target_is_directory=True)
            result = ConversionResult(
                source=src,
                engine="test",
                markdown="![image](assets/image.png)",
                assets={"assets/image.png": b"unsafe"},
            )

            write_result(result, output, ["md"], image_mode="referenced")

            self.assertFalse((escaped / "image.png").exists())
            self.assertEqual((output / "paper.md").read_text(), "![image](assets/image.png)")
            self.assertEqual(len(result.warnings), 1)

    def test_image_references_are_unchanged_for_none_and_embedded_modes(self):
        for mode in ("none", "embedded"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp_dir:
                root = Path(tmp_dir)
                src = root / "paper.pdf"
                src.write_bytes(b"")
                md = "![figure](paper_assets/figure.png)"
                result = ConversionResult(
                    source=src,
                    engine="test",
                    markdown=md,
                    assets={"assets/figure.png": b"image"},
                )

                write_result(result, root / "out", ["md", "html"], image_mode=mode)

                self.assertEqual((root / "out" / "paper.md").read_text(), md)
                fallback_html = (root / "out" / "paper.html").read_text()
                self.assertIn("![figure](paper_assets/figure.png)", fallback_html)
                self.assertNotIn("<img", fallback_html)
                # Preserve the writer's historical basename output outside referenced mode.
                self.assertEqual((root / "out" / "paper_assets" / "figure.png").read_bytes(), b"image")

    def test_referenced_mode_without_assets_leaves_image_reference_untouched(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            src = root / "paper.pdf"
            src.write_bytes(b"")
            md = "![figure](assets/missing.png)"
            result = ConversionResult(source=src, engine="test", markdown=md)

            write_result(result, root / "out", ["md"], image_mode="referenced")

            self.assertEqual((root / "out" / "paper.md").read_text(), md)
            self.assertFalse((root / "out" / "paper_assets").exists())


class CleanOptionTests(unittest.TestCase):
    """Ref: openspec/specs/output-formats/spec.md"""

    def write(self, tmp, **options):
        result = ConversionResult(
            source=Path("spec.pdf"),
            engine="stub",
            markdown="LED count\n\n84\n\nPage 2 of 9\n",
        )
        write_result(result=result, output_dir=Path(tmp), formats=["md"], clean=True, **options)
        return (Path(tmp) / "spec.md").read_text(encoding="utf-8")

    def test_clean_keeps_standalone_numbers_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = self.write(tmp)
        self.assertIn("84", written.splitlines())
        self.assertNotIn("Page 2 of 9", written)

    def test_strip_bare_numbers_reaches_the_cleaner(self):
        with tempfile.TemporaryDirectory() as tmp:
            written = self.write(tmp, strip_bare_numbers=True)
        self.assertNotIn("84", written.splitlines())
        self.assertIn("LED count", written)

if __name__ == "__main__":
    unittest.main()
