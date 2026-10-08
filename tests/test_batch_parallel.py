import tempfile
import unittest
from pathlib import Path
from document_converter.pipeline import process_batch
from document_converter.models import ConversionResult

class TestBatchParallel(unittest.TestCase):
    """Ref: changes/002-batch-parallel-processing/"""

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

if __name__ == "__main__":
    unittest.main()
