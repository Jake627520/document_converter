from pathlib import Path
from .models import ConversionResult, OutputFormat
from .cleaner import clean_markdown

def write_result(
    result: ConversionResult,
    output_dir: Path,
    formats: list[OutputFormat],
    clean: bool = False,
    preserve_layout: bool = False,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = result.source.stem

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
            if fmt == "html" and md:
                value = markdown_fallback_html(md, stem)
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
    try:
        import markdown
        body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    except Exception:
        body = "<pre>" + _escape(md) + "</pre>"
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{_escape(title)}</title></head>
<body>
{body}
</body>
</html>
"""

def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
