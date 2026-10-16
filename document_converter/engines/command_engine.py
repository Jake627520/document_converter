import shutil
import subprocess
from pathlib import Path
from .base import Engine, EngineError
from ..models import ConversionResult, ImageMode

class MarkerEngine(Engine):
    name = "marker"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        exe = shutil.which("marker_single") or shutil.which("marker")
        if not exe:
            raise EngineError("Marker CLI not found. Install marker-pdf.")
        outdir = path.parent / ".document-converter-marker"
        outdir.mkdir(exist_ok=True)
        cmd = [exe, str(path), "--output_dir", str(outdir)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise EngineError(e.stderr or str(e)) from e
        candidates = list(outdir.rglob("*.md"))
        if not candidates:
            raise EngineError("Marker completed but no Markdown output was found.")
        md_path = max(candidates, key=lambda p: p.stat().st_mtime)
        md = md_path.read_text(encoding="utf-8")
        return ConversionResult(source=path, engine=self.name, markdown=md,
                                text=md, warnings=["Marker fallback does not synthesize HTML/JSON."])

class MinerUEngine(Engine):
    name = "mineru"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

    def convert(self, path: Path, image_mode: ImageMode) -> ConversionResult:
        # MinerU 4.x parses a file with `mineru-kit parse`. Its other command,
        # `mineru`, has no `kit` subcommand, and every `mineru` subcommand,
        # its own `parse` included, first prepares MinerU's usage telemetry; so
        # it is never called here. No --remote or --remote-url is passed, so
        # the document is parsed on this machine, not by a parse service.
        exe = shutil.which("mineru-kit")
        if not exe:
            raise EngineError("MinerU CLI not found. Install MinerU 4.x, which provides mineru-kit.")
        outdir = path.parent / ".document-converter-mineru"
        outdir.mkdir(exist_ok=True)
        out_md = outdir / f"{path.stem}.md"
        cmd = [exe, "parse", str(path), "-o", str(out_md), "--tier", "standard"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise EngineError(e.stderr or str(e)) from e
        if not out_md.exists():
            raise EngineError("MinerU completed but Markdown output was not found.")
        md = out_md.read_text(encoding="utf-8")
        return ConversionResult(source=path, engine=self.name, markdown=md,
                                text=md, warnings=["MinerU fallback output is currently consumed as Markdown."])
