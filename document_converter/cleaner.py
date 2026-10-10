import re

def clean_markdown(md: str, preserve_layout: bool = False, strip_bare_numbers: bool = False) -> str:
    """
    Clean Markdown output from document conversions.

    If preserve_layout is True, retains line breaks, indentations, and page delimiters.
    If preserve_layout is False (default clean mode):
      - Protects fenced code blocks (```...```) and block math ($$...$$) from alteration.
      - Normalizes excess blank lines (max 2 consecutive newlines).
      - Strips trailing whitespaces from lines.
      - Removes labelled page markers such as "Page 3 of 12", "4 / 20" and "- 5 -".
      - Ensures consistent heading spacing.

    A line holding nothing but digits is kept, because engines emit table cells
    and other document values on their own line and deleting them loses content.
    Pass strip_bare_numbers=True to also drop those lines, for documents whose
    page numbers survive as bare numerals.
    """
    if not md:
        return ""

    if preserve_layout:
        # In preserve-layout mode, only clean trailing whitespace per line
        return "\n".join(line.rstrip() for line in md.splitlines()) + ("\n" if md.endswith("\n") else "")

    # Split into protected blocks (code blocks and math blocks) and normal text
    protected_tokens = []
    
    def _stash_block(match):
        token = f"@@__PROTECTED_BLOCK_{len(protected_tokens)}__@@"
        protected_tokens.append(match.group(0))
        return token

    # Stash fenced code blocks (``` ... ``` or ~~~ ... ~~~)
    text = re.sub(r"(```[\s\S]*?```|~~~[\s\S]*?~~~)", _stash_block, md)
    # Stash display math blocks ($$ ... $$)
    text = re.sub(r"(\$\$[\s\S]*?\$\$)", _stash_block, text)

    lines = []
    for line in text.splitlines():
        trimmed = line.rstrip()
        
        # Filter out standalone page number patterns:
        # e.g., "Page 1 of 10", "- 1 -", "Page 1", "1 / 10", standalone integer on line
        if re.match(r"^(?:page\s+\d+(?:\s+of\s+\d+|\s*/\s*\d+)?|\d+\s*/\s*\d+|-\s*\d+\s*-)$", trimmed, re.IGNORECASE):
            continue
        # Standalone numeral: content by default, page footer only on request.
        if strip_bare_numbers and re.match(r"^\d{1,4}$", trimmed):
            continue
        # Repeated horizontal rules noise (e.g. page breaks like "---" followed immediately by "---")
        if re.match(r"^[-*_]{3,}$", trimmed) and lines and re.match(r"^[-*_]{3,}$", lines[-1].strip()):
            continue

        lines.append(trimmed)

    # Rejoin
    cleaned = "\n".join(lines)

    # Normalize excessive blank lines (more than 2 empty lines become 1 empty line)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Ensure header has clean newline before it
    cleaned = re.sub(r"([^\n])\n(#{1,6}\s+)", r"\1\n\n\2", cleaned)

    # Restore protected blocks
    for i, block in enumerate(protected_tokens):
        token = f"@@__PROTECTED_BLOCK_{i}__@@"
        cleaned = cleaned.replace(token, block)

    return cleaned.strip() + "\n"
