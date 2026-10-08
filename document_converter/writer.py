from pathlib import Path
from .models import ConversionResult, OutputFormat
from .cleaner import clean_markdown
from .renderer import render_html

def write_result(
    result: ConversionResult,
    output_dir: Path,
    formats: list[OutputFormat],
    clean: bool = False,
    preserve_layout: bool = False,
    output_stem: str | None = None,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem or result.source.stem

    md = result.markdown
    if md and clean:
        md = clean_markdown(md, preserve_layout=preserve_layout)

    values = {
        "md": md,
        "html": result.html,
        "json": result.json_text,
        "txt": result.text,
    }
    for fmt in formats:
        value = values.get(fmt)
        if value is None:
            if fmt == "html" and md is not None:
                value = render_html(md, title=stem)
            else:
                result.warnings.append(f"{fmt} is unavailable from engine {result.engine}")
                continue
        (output_dir / f"{stem}.{fmt}").write_text(value, encoding="utf-8")

    if result.assets:
        assets_dir = output_dir / f"{stem}_assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for name, data in result.assets.items():
            target = assets_dir / Path(name).name
            target.write_bytes(data)

def markdown_fallback_html(md: str, title: str) -> str:
    """Backwards compatibility helper."""
    return render_html(md, title=title)
