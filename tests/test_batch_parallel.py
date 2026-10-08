import tempfile
import unittest
import inspect
import ast
from pathlib import Path
from document_converter.pipeline import (
    DEFAULT_PARALLEL,
    MAX_WORKER_LIMIT,
    process_batch,
)

class TestBatchParallel(unittest.TestCase):
    """Regression tests for openspec/changes/CHG-002-batch-parallel-processing."""

    def test_default_and_hard_worker_limit(self):
        self.assertEqual(DEFAULT_PARALLEL, 1)
        self.assertEqual(inspect.signature(process_batch).parameters["parallel"].default, 1)
        self.assertEqual(MAX_WORKER_LIMIT, 4)
        cli_tree = ast.parse(
            (Path(__file__).parents[1] / "document_converter" / "cli.py").read_text(
                encoding="utf-8"
            )
        )
        convert_node = next(
            node for node in cli_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "convert"
        )
        parallel_index = next(
            i for i, arg in enumerate(convert_node.args.args) if arg.arg == "parallel"
        )
        parallel_default = convert_node.args.defaults[
            parallel_index - (len(convert_node.args.args) - len(convert_node.args.defaults))
        ]
        self.assertIsInstance(parallel_default, ast.Call)
        self.assertIsInstance(parallel_default.args[0], ast.Name)
        self.assertEqual(parallel_default.args[0].id, "DEFAULT_PARALLEL")
        rejected_out_of_range = any(
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "parallel"
            and any(
                isinstance(op, ast.Gt)
                and isinstance(comparator, ast.Name)
                and comparator.id == "MAX_WORKER_LIMIT"
                for op, comparator in zip(node.test.ops, node.test.comparators)
            )
            and any(isinstance(child, ast.Raise) for child in node.body)
            for node in ast.walk(convert_node)
        )
        self.assertTrue(rejected_out_of_range)

        with self.assertRaisesRegex(ValueError, "between 1 and 4"):
            process_batch([], Path("out"), ["md"], parallel=0)
        with self.assertRaisesRegex(ValueError, "between 1 and 4"):
            process_batch([], Path("out"), ["md"], parallel=5)

    def test_batch_parallel_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_dir = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            in_dir.mkdir()

            # Create 3 minimal valid text/markdown files
            files = []
            for i in range(3):
                p = in_dir / f"doc_{i}.md"
                p.write_text(f"# Doc {i}\nContent {i}\n", encoding="utf-8")
                files.append(p)

            results = process_batch(
                inputs=files,
                output_dir=out_dir,
                formats=["md", "html"],
                engine_name="auto",
                image_mode="none",
                parallel=2,
            )

            self.assertEqual(len(results), 3)
            for res in results:
                self.assertTrue(res["success"], f"Failed: {res.get('error')}")
                stem = res["path"].stem
                self.assertTrue((out_dir / f"{stem}.md").exists())
                self.assertTrue((out_dir / f"{stem}.html").exists())

    def test_batch_parallel_fault_isolation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_dir = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            in_dir.mkdir()

            # 2 good files, 1 non-existent/corrupted file
            good1 = in_dir / "good1.md"
            good1.write_text("# Good 1\n", encoding="utf-8")
            good2 = in_dir / "good2.md"
            good2.write_text("# Good 2\n", encoding="utf-8")
            bad = in_dir / "corrupted_nonexistent.unknown"

            results = process_batch(
                inputs=[good1, bad, good2],
                output_dir=out_dir,
                formats=["md"],
                engine_name="auto",
                image_mode="none",
                parallel=2,
            )

            self.assertEqual(len(results), 3)
            success_map = {r["path"].name: r["success"] for r in results}
            self.assertTrue(success_map["good1.md"])
            self.assertTrue(success_map["good2.md"])
            self.assertFalse(success_map["corrupted_nonexistent.unknown"])

    def test_nested_source_paths_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            (root / "department-a").mkdir(parents=True)
            (root / "department-b").mkdir()
            first = root / "department-a" / "report.md"
            second = root / "department-b" / "report.md"
            first.write_text("A report", encoding="utf-8")
            second.write_text("B report", encoding="utf-8")

            results = process_batch(
                [first, second], out_dir, ["md"], source_root=root, parallel=2
            )

            self.assertTrue(all(item["success"] for item in results))
            self.assertEqual(
                (out_dir / "department-a" / "report.md").read_text(encoding="utf-8"),
                "A report",
            )
            self.assertEqual(
                (out_dir / "department-b" / "report.md").read_text(encoding="utf-8"),
                "B report",
            )

    def test_same_stem_inputs_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            root.mkdir()
            markdown = root / "report.md"
            text = root / "report.txt"
            markdown.write_text("Markdown source", encoding="utf-8")
            text.write_text("Text source", encoding="utf-8")

            results = process_batch(
                [markdown, text], out_dir, ["md"], source_root=root, parallel=2
            )

            self.assertTrue(all(item["success"] for item in results))
            self.assertEqual(
                (out_dir / "report_md.md").read_text(encoding="utf-8"),
                "Markdown source",
            )
            self.assertEqual(
                (out_dir / "report_txt.md").read_text(encoding="utf-8"),
                "Text source",
            )
            self.assertEqual(len(list(out_dir.glob("*.md"))), 2)

    def test_case_only_stem_collision_without_source_root_is_disambiguated(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            first_dir = root / "a"
            second_dir = root / "b"
            first_dir.mkdir()
            second_dir.mkdir()
            first = first_dir / "Report.md"
            second = second_dir / "report.md"
            first.write_text("Upper-case path source", encoding="utf-8")
            second.write_text("Lower-case path source", encoding="utf-8")

            results = process_batch([first, second], out_dir, ["md"], parallel=2)

            self.assertTrue(all(item["success"] for item in results))
            output_files = sorted(out_dir.glob("*.md"))
            self.assertEqual(len(output_files), 2)
            self.assertCountEqual(
                [path.read_text(encoding="utf-8") for path in output_files],
                ["Upper-case path source", "Lower-case path source"],
            )

if __name__ == "__main__":
    unittest.main()
