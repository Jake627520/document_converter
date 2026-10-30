import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from .cleaner import clean_markdown
from .models import ConversionResult, OutputFormat
from .renderer import render_html


_MARKDOWN_IMAGE = re.compile(r"(?<!\\)!\[(?P<alt>(?:\\.|[^\]])*)\]\((?P<destination><[^>\n]*>|[^)\n]+)\)")
_HTML_IMAGE = re.compile(
    r"(?P<prefix><img\b[^>]*?\s+src\s*=\s*)(?:(?P<quote>['\"])(?P<quoted>[^'\"]*)(?P=quote)|(?P<bare>[^\s>]+))",
    re.IGNORECASE | re.DOTALL,
)
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(`+)(.+?)\1")
_HTML_PROTECTED = re.compile(
    r"<!--.*?(?:-->|$)|<(?P<tag>script|style|textarea|title|xmp|iframe|noembed|noframes|noscript)\b[^>]*>.*?(?:</(?P=tag)\s*>|$)",
    re.IGNORECASE | re.DOTALL,
)


def _safe_relative_asset_path(value: str) -> str | None:
    """Normalize a portable asset key, rejecting paths that can escape its root."""
    if not value or "\\" in value or "\x00" in value or value.startswith("/"):
        return None
    if re.match(r"^[A-Za-z]:", value):
        return None
    parts = value.split("/")
    if any(part == ".." or part == "" for part in parts):
        return None
    normalized = [part for part in parts if part != "."]
    return "/".join(normalized) if normalized else None


def _referenced_asset_map(result: ConversionResult) -> dict[str, tuple[Path, bytes]]:
    """Return safe, collision-free asset keys and paths under the output asset root."""
    candidates: dict[str, tuple[Path, bytes]] = {}
    collision_groups: dict[str, list[str]] = {}
    for raw_name, data in result.assets.items():
        name = str(raw_name)
        relative = _safe_relative_asset_path(name)
        if relative is None:
            result.warnings.append(f"Rejected unsafe image asset path: {name!r}")
            continue
        collision_groups.setdefault(relative.casefold(), []).append(relative)
        candidates[relative] = (PurePosixPath(relative), data)

    collided = {name for names in collision_groups.values() if len(names) > 1 for name in names}
    for name in sorted(collided):
        candidates.pop(name, None)
        result.warnings.append(f"Rejected colliding image asset path: {name!r}")
    return candidates


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _mapped_reference(destination: str, asset_paths: dict[str, str]) -> str | None:
    """Map only a local reference that exactly identifies a returned asset key."""
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("//"):
        return None
    decoded_path = unquote(parsed.path)
    normalized = _safe_relative_asset_path(decoded_path)
    if normalized is None:
        return None
    target = asset_paths.get(normalized)
    if target is None:
        return None
    return urlunsplit(("", "", quote(target, safe="/-._~"), parsed.query, parsed.fragment))


def _rewrite_markdown_images(markdown: str, asset_paths: dict[str, str]) -> str:
    def replace_image(match: re.Match[str]) -> str:
        raw_destination = match.group("destination")
        angle_wrapped = raw_destination.startswith("<") and raw_destination.endswith(">")
        destination = raw_destination[1:-1] if angle_wrapped else raw_destination.strip()
        mapped = _mapped_reference(destination, asset_paths)
        if mapped is None:
            return match.group(0)
        rewritten = f"<{mapped}>" if angle_wrapped or any(ch.isspace() for ch in mapped) else mapped
        start = match.start("destination") - match.start()
        end = start + len(raw_destination)
        return match.group(0)[:start] + rewritten + match.group(0)[end:]

    def rewrite_line(line: str) -> str:
        chunks = []
        cursor = 0
        for code in _INLINE_CODE.finditer(line):
            chunks.append(_MARKDOWN_IMAGE.sub(replace_image, line[cursor:code.start()]))
            chunks.append(code.group(0))
            cursor = code.end()
        chunks.append(_MARKDOWN_IMAGE.sub(replace_image, line[cursor:]))
        return "".join(chunks)

    output = []
    fence: tuple[str, int] | None = None
    for line in markdown.splitlines(keepends=True):
        marker = _FENCE.match(line)
        if fence:
            output.append(line)
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= fence[1]
                and not line[marker.end():].strip()
            ):
                fence = None
        elif marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            output.append(line)
        else:
            output.append(rewrite_line(line))
    return "".join(output)


def _rewrite_html_images(html: str, asset_paths: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        destination = match.group("quoted") if match.group("quote") else match.group("bare")
        mapped = _mapped_reference(destination, asset_paths)
        if mapped is None:
            return match.group(0)
        if match.group("quote"):
            return f"{match.group('prefix')}{match.group('quote')}{mapped}{match.group('quote')}"
        return f"{match.group('prefix')}{mapped}"

    chunks = []
    cursor = 0
    for protected in _HTML_PROTECTED.finditer(html):
        chunks.append(_HTML_IMAGE.sub(replace, html[cursor:protected.start()]))
        chunks.append(protected.group(0))
        cursor = protected.end()
    chunks.append(_HTML_IMAGE.sub(replace, html[cursor:]))
    return "".join(chunks)


def markdown_to_text(md: str) -> str:
    """Render Markdown as plain text: drop fences, heading marks and list bullets."""
    lines = []
    for line in md.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
            continue
        if s.startswith("```"):
            continue
        while s.startswith("#"):
            s = s[1:].lstrip()
        if s.startswith(("- ", "* ", "+ ")):
            s = s[2:]
        lines.append(s)
    return "\n".join(lines).strip() + "\n"


def plain_text_of(content: str, suffix: str) -> str:
    """The plain-text rendering of a document read directly from disk.

    A .txt file already is plain text, so it is returned untouched: stripping
    heading marks and bullets from it would damage genuine lines such as
    "#1 priority" or "- 5 units". Markdown is rendered.
    """
    return content if suffix.lower() == ".txt" else markdown_to_text(content)


def write_result(
    result: ConversionResult,
    output_dir: Path,
    formats: list[OutputFormat],
    clean: bool = False,
    preserve_layout: bool = False,
    output_stem: str | None = None,
    image_mode: str = "none",
    strip_bare_numbers: bool = False,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_stem or result.source.stem

    md = result.markdown
    if md and clean:
        md = clean_markdown(md, preserve_layout=preserve_layout, strip_bare_numbers=strip_bare_numbers)

    referenced_assets: dict[str, tuple[Path, bytes]] = {}
    asset_paths: dict[str, str] = {}
    assets_dir = output_dir / f"{stem}_assets"
    if image_mode == "referenced" and result.assets:
        referenced_assets = _referenced_asset_map(result)
        if not _is_within(assets_dir, output_dir):
            result.warnings.append("Rejected image assets because the assets directory resolves outside the output directory")
            referenced_assets = {}
        else:
            safe_assets = {}
            for key, entry in referenced_assets.items():
                target = assets_dir.joinpath(*entry[0].parts)
                if _is_within(target, assets_dir):
                    safe_assets[key] = entry
                else:
                    result.warnings.append(f"Rejected image asset path through a symbolic link: {key!r}")
            referenced_assets = safe_assets
        for key, (relative_path, _) in referenced_assets.items():
            asset_paths[key] = f"{assets_dir.name}/{relative_path.as_posix()}"
        if md is not None:
            md = _rewrite_markdown_images(md, asset_paths)

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
                mapped_images = {path: path for path in asset_paths.values()}
                value = render_html(md, title=stem, image_paths=mapped_images)
            elif fmt == "txt" and md is not None:
                # Plain text is a rendering of the Markdown, so it is available
                # from any engine that produced Markdown - including a release
                # that reads a text file directly and runs no engine at all.
                value = markdown_to_text(md)
            else:
                result.warnings.append(f"{fmt} is unavailable from engine {result.engine}")
                continue
        elif fmt == "html" and image_mode == "referenced" and asset_paths:
            value = _rewrite_html_images(value, asset_paths)
        # newline="\n": Windows would otherwise write CRLF, unlike every other platform.
        (output_dir / f"{stem}.{fmt}").write_text(value, encoding="utf-8", newline="\n")

    if image_mode == "referenced":
        for relative_path, data in referenced_assets.values():
            target = assets_dir.joinpath(*relative_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not _is_within(target, assets_dir):
                result.warnings.append(f"Skipped image asset path that resolved outside its asset directory: {relative_path.as_posix()!r}")
                continue
            target.write_bytes(data)
    elif result.assets:
        # Retain the historical output behavior for none/embedded modes.
        assets_dir.mkdir(parents=True, exist_ok=True)
        for name, data in result.assets.items():
            target = assets_dir / Path(name).name
            target.write_bytes(data)


def markdown_fallback_html(md: str, title: str) -> str:
    """Backwards compatibility helper."""
    return render_html(md, title=title)
