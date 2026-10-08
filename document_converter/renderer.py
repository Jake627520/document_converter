"""
Standalone HTML Renderer
Change ID: 001 - Standalone Offline HTML Renderer
"""

import html
import re
from typing import Optional

EMBEDDED_CSS = """
:root {
  --bg-color: #ffffff;
  --text-color: #1f2328;
  --border-color: #d0d7de;
  --code-bg: #f6f8fa;
  --table-zebra: #f6f8fa;
  --link-color: #0969da;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #0d1117;
    --text-color: #e6edf3;
    --border-color: #30363d;
    --code-bg: #161b22;
    --table-zebra: #161b22;
    --link-color: #4493f8;
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-color);
  background-color: var(--bg-color);
  margin: 0;
  padding: 40px 20px;
}

.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 900px;
  margin: 0 auto;
}

h1, h2, h3, h4, h5, h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

h1 { font-size: 2em; border-bottom: 1px solid var(--border-color); padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--border-color); padding-bottom: .3em; }
h3 { font-size: 1.25em; }

p { margin-top: 0; margin-bottom: 16px; }

code {
  padding: .2em .4em;
  margin: 0;
  font-size: 85%;
  background-color: var(--code-bg);
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: var(--code-bg);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

pre code {
  padding: 0;
  background-color: transparent;
  border-radius: 0;
}

table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-top: 0;
  margin-bottom: 16px;
  display: block;
  width: max-content;
  max-width: 100%;
  overflow: auto;
}

table tr {
  background-color: var(--bg-color);
  border-top: 1px solid var(--border-color);
}

table tr:nth-child(2n) {
  background-color: var(--table-zebra);
}

table th, table td {
  padding: 6px 13px;
  border: 1px solid var(--border-color);
}

table th {
  font-weight: 600;
}

ul, ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}
"""

def render_html(markdown: str, title: Optional[str] = "Document") -> str:
    """
    Convert Markdown to semantic HTML5.
    100% offline self-contained document with zero external network CDN dependencies.
    """
    safe_title = html.escape(title or "Document")
    body_content = _parse_markdown_to_body(markdown)
    
    return f"""<!doctype html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>{EMBEDDED_CSS.strip()}</style>
</head>
<body>
    <main class="markdown-body">
{body_content}
    </main>
</body>
</html>
"""

def render_markdown_to_html(md: str, title: str = "Document") -> str:
    """Alias for backwards compatibility with existing writer and tests."""
    return render_html(md, title=title)

def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)

def _format_inline(text: str) -> str:
    """Handle inline formatting: inline code, bold, italic, and HTML escaping."""
    parts = re.split(r"(`[^`]+`)", text)
    formatted_parts = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            code_content = html.escape(part[1:-1])
            formatted_parts.append(f"<code>{code_content}</code>")
        else:
            escaped = html.escape(part)
            escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
            escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
            formatted_parts.append(escaped)
    return "".join(formatted_parts)

def _parse_markdown_to_body(md: str) -> str:
    if not md or not md.strip():
        return ""

    lines = md.splitlines()
    output = []
    idx = 0
    total = len(lines)

    while idx < total:
        line = lines[idx]
        stripped = line.strip()

        # 1. Blank line
        if not stripped:
            idx += 1
            continue

        # 2. Fenced code block (``` or ~~~)
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            raw_lang = stripped[3:].strip()
            # Sanitize language attribute
            clean_lang = re.sub(r'[^a-zA-Z0-9_-]', '', raw_lang)
            idx += 1
            code_lines = []
            while idx < total:
                cur_line = lines[idx]
                if cur_line.strip().startswith(fence):
                    idx += 1
                    break
                code_lines.append(cur_line)
                idx += 1
            code_str = html.escape("\n".join(code_lines))
            lang_attr = f' class="language-{clean_lang}"' if clean_lang else ""
            output.append(f"<pre><code{lang_attr}>{code_str}</code></pre>")
            continue

        # 3. Heading
        h_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if h_match:
            level = len(h_match.group(1))
            heading_text = _format_inline(h_match.group(2).strip())
            output.append(f"<h{level}>{heading_text}</h{level}>")
            idx += 1
            continue

        # 4. Table
        if stripped.startswith("|") and stripped.endswith("|") and idx + 1 < total and "|" in lines[idx + 1]:
            header_cells = [c.strip() for c in stripped[1:-1].split("|")]
            next_line = lines[idx + 1].strip()
            sep_cells = [c.strip() for c in next_line[1:-1].split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in sep_cells if c):
                idx += 2
                table_html = ["<table>", "<thead><tr>"]
                for hc in header_cells:
                    table_html.append(f"<th>{_format_inline(hc)}</th>")
                table_html.append("</tr></thead>")
                
                rows_html = []
                while idx < total:
                    row_line = lines[idx].strip()
                    if not (row_line.startswith("|") and row_line.endswith("|")):
                        break
                    cells = [c.strip() for c in row_line[1:-1].split("|")]
                    rows_html.append("<tr>" + "".join(f"<td>{_format_inline(c)}</td>" for c in cells) + "</tr>")
                    idx += 1
                if rows_html:
                    table_html.append("<tbody>" + "".join(rows_html) + "</tbody>")
                table_html.append("</table>")
                output.append("".join(table_html))
                continue

        # 5. Unordered List (- or *)
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while idx < total and re.match(r"^[-*]\s+", lines[idx].strip()):
                item_text = re.sub(r"^[-*]\s+", "", lines[idx].strip())
                items.append(f"<li>{_format_inline(item_text)}</li>")
                idx += 1
            output.append("<ul>" + "".join(items) + "</ul>")
            continue

        # 6. Ordered List (1. 2.)
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while idx < total and re.match(r"^\d+\.\s+", lines[idx].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[idx].strip())
                items.append(f"<li>{_format_inline(item_text)}</li>")
                idx += 1
            output.append("<ol>" + "".join(items) + "</ol>")
            continue

        # 7. Paragraph
        p_lines = []
        while idx < total:
            cur_line = lines[idx]
            cur_stripped = cur_line.strip()
            if not cur_stripped:
                break
            if cur_stripped.startswith("```") or cur_stripped.startswith("~~~"):
                break
            if re.match(r"^(#{1,6})\s+", cur_stripped):
                break
            if re.match(r"^[-*]\s+", cur_stripped) or re.match(r"^\d+\.\s+", cur_stripped):
                break
            if cur_stripped.startswith("|") and cur_stripped.endswith("|"):
                break
            p_lines.append(cur_line)
            idx += 1

        if p_lines:
            raw_p_text = "\n".join(p_lines)
            output.append(f"<p>{_format_inline(raw_p_text)}</p>")

    return "\n\n".join(output)
