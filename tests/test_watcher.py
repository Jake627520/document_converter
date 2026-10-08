import tempfile
import unittest
import math
from pathlib import Path
from unittest.mock import patch

from document_converter.watcher import (
    DirectoryWatcher,
    validate_watch_interval,
    validate_watch_paths,
    watch_directory,
)


class TestDirectoryWatcher(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "in"
        self.root.mkdir()
        self.output = self.root / "converted"
        self.output.mkdir()
        self.doc = self.root / "one.md"
        self.doc.write_text("original", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_existing_file_requires_two_equal_snapshots_then_processes_once(self):
        watcher = DirectoryWatcher(self.root, self.output)
        with patch("document_converter.watcher.process_batch", return_value=[{"success": True}]) as batch:
            self.assertEqual(watcher.poll_once(), [])
            result = watcher.poll_once()
        self.assertEqual(result, [{"success": True}])
        batch.assert_called_once()
        self.assertEqual(batch.call_args.kwargs["inputs"], [self.doc.resolve()])
        self.assertEqual(watcher.poll_once(), [])
        batch.assert_called_once()

    def test_output_subtree_is_excluded(self):
        generated = self.output / "recursive.md"
        generated.write_text("ignore", encoding="utf-8")
        watcher = DirectoryWatcher(self.root, self.output)
        with patch("document_converter.watcher.process_batch", return_value=[]) as batch:
            watcher.poll_once()
            watcher.poll_once()
        self.assertEqual(batch.call_args.kwargs["inputs"], [self.doc.resolve()])

    def test_output_parent_does_not_exclude_source_files(self):
        watcher = DirectoryWatcher(self.root, self.root.parent)
        with patch("document_converter.watcher.process_batch", return_value=[{"success": True}]) as batch:
            watcher.poll_once()
            watcher.poll_once()
        self.assertEqual(batch.call_args.kwargs["inputs"], [self.doc.resolve()])

    def test_modified_file_is_processed_again_after_stabilizing(self):
        watcher = DirectoryWatcher(self.root, self.output)
        with patch("document_converter.watcher.process_batch", return_value=[{"success": True}]) as batch:
            watcher.poll_once()
            watcher.poll_once()
            self.doc.write_text("modified content", encoding="utf-8")
            watcher.poll_once()
            watcher.poll_once()
        self.assertEqual(batch.call_count, 2)

    def test_batch_receives_full_options_and_failure_results_are_not_retried(self):
        watcher = DirectoryWatcher(self.root, self.output, formats=["html"], parallel=2)
        with patch("document_converter.watcher.process_batch", return_value=[{"success": False}]) as batch:
            watcher.poll_once()
            watcher.poll_once()
            watcher.poll_once()
        self.assertEqual(batch.call_count, 1)
        self.assertEqual(batch.call_args.kwargs["formats"], ["html"])
        self.assertEqual(batch.call_args.kwargs["parallel"], 2)

    def test_rejects_same_source_and_output(self):
        with self.assertRaisesRegex(ValueError, "different"):
            validate_watch_paths(self.root, self.root)

    def test_rejects_file_source_and_nonpositive_interval(self):
        with self.assertRaisesRegex(ValueError, "directory"):
            validate_watch_paths(self.doc, self.output)
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            watch_directory(self.root, self.output, interval=0)

    def test_nonpositive_interval_is_allowed_when_watch_is_disabled(self):
        validate_watch_interval(False, 0)
        validate_watch_interval(False, -1)
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            validate_watch_interval(True, 0)
        for invalid in (math.nan, math.inf, -math.inf):
            with self.subTest(interval=invalid):
                with self.assertRaisesRegex(ValueError, "finite"):
                    validate_watch_interval(True, invalid)

    def test_unsupported_extensions_are_not_in_snapshot(self):
        unknown = self.root / "ignored.xyz"
        unknown.write_text("ignore", encoding="utf-8")
        watcher = DirectoryWatcher(self.root, self.output)
        self.assertNotIn(unknown, watcher.snapshot_fn(self.root, self.output))

    def test_watch_loop_uses_injected_sleep_and_stop_hooks(self):
        calls = []
        snapshots = iter([{}, {}])
        watch_directory(
            self.root,
            self.output,
            interval=0.25,
            snapshot_fn=lambda *_: next(snapshots),
            sleep_fn=lambda duration: calls.append(duration),
            stop_fn=lambda: len(calls) >= 2,
        )
        self.assertEqual(calls, [0.25, 0.25])


try:
    import typer  # noqa: F401
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False


@unittest.skipUnless(HAS_TYPER, "typer not installed in current environment")
class TestWatchCli(unittest.TestCase):
    def test_watch_rejects_file_source(self):
        from typer.testing import CliRunner
        from document_converter.cli import app

        result = CliRunner().invoke(app, ["convert", "tests/fixtures/sample_text.pdf", "--watch"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("directory", result.output.lower())

    def test_watch_rejects_nonpositive_interval(self):
        from typer.testing import CliRunner
        from document_converter.cli import app

        with tempfile.TemporaryDirectory() as temp:
            result = CliRunner().invoke(app, ["convert", temp, "--watch", "--watch-interval", "0"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("greater than 0", result.output.lower())

    def test_ctrl_c_exits_cleanly(self):
        from typer.testing import CliRunner
        from document_converter.cli import app

        with tempfile.TemporaryDirectory() as temp, patch("document_converter.cli.watch_directory", side_effect=KeyboardInterrupt):
            result = CliRunner().invoke(app, ["convert", temp, "--watch"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("stopped", result.output.lower())


if __name__ == "__main__":
    unittest.main()
