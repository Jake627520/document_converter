"""Shared web workbench launcher for the fixed local macOS release candidates.

Two reviewed profiles exist. ``text`` is the original candidate: Markdown and
UTF-8 text only, with no engine code frozen into the app. ``pdf`` additionally
accepts PDFs that already carry a text layer, converted by Docling's model-free
reader, so the app still contains no deep-learning runtime and downloads no
model weights. A frozen app carries its profile in ``release_profile.txt``
beside the bundled resources; ``--profile`` overrides it for validation.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import webbrowser

import uvicorn
from document_converter import web_app

PROFILE_MARKER = "release_profile.txt"

FORBIDDEN_MODULES = {
    "text": (
        "fitz",
        "pymupdf",
        "docling",
        "torch",
        "marker",
        "magic_pdf",
        "pytest",
        "document_converter.pipeline",
        "document_converter.detector",
        "document_converter.engines",
    ),
    # The PDF profile loads the model-free engine on demand, so engine code is
    # expected; a deep-learning runtime and the optional engines are not.
    "pdf": (
        "fitz",
        "pymupdf",
        "torch",
        "torchvision",
        "transformers",
        "marker",
        "magic_pdf",
        "mineru",
        "pytest",
        "document_converter.cli",
        "document_converter.pipeline",
        "document_converter.detector",
    ),
}

CONFIGURE = {"text": web_app.configure_text_release, "pdf": web_app.configure_pdf_release}


def frozen_profile() -> str | None:
    """Read the profile baked into a frozen bundle, if this is one."""
    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return None
    try:
        with open(os.path.join(base, PROFILE_MARKER), encoding="utf-8") as marker:
            value = marker.read().strip()
    except OSError:
        return None
    return value if value in CONFIGURE else None


def main(argv: list[str] | None = None):
    default_profile = frozen_profile() or "text"
    parser = argparse.ArgumentParser(description="Local document converter")
    parser.add_argument("--port", type=int, default=0, help="Loopback port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser (automated validation)")
    parser.add_argument("--diagnostics", action="store_true", help="Report runtime isolation and exit")
    parser.add_argument(
        "--profile",
        choices=sorted(CONFIGURE),
        default=default_profile,
        help="Reviewed release profile: text accepts Markdown and UTF-8 text; pdf also accepts text-layer PDFs",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    CONFIGURE[args.profile]()
    forbidden = FORBIDDEN_MODULES[args.profile]
    loaded = [name for name in sys.modules if any(name == item or name.startswith(item + ".") for item in forbidden)]
    if loaded:
        raise RuntimeError(f"Unexpected release modules: {loaded}")
    if args.diagnostics:
        print(json.dumps({"profile": web_app.release_profile(), "inputs": sorted(web_app.release_formats()), "frozen": bool(getattr(sys, "frozen", False)), "python": sys.version, "paths": sys.path, "forbidden_loaded": loaded}, indent=2))
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", args.port))
    sock.listen(128)
    sock.setblocking(False)
    port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    if sys.stdout:
        print(url, flush=True)
    config = uvicorn.Config(web_app.app, host="127.0.0.1", port=port, loop="asyncio", http="h11", ws="none", lifespan="off", log_config=None, access_log=False)
    server = uvicorn.Server(config)
    if not args.no_browser:
        def open_when_ready():
            # Only opens after the server has completed startup.
            if server.started:
                webbrowser.open(url)
            elif not server.should_exit:
                timer = threading.Timer(0.1, open_when_ready)
                timer.daemon = True
                timer.start()
        timer = threading.Timer(0.1, open_when_ready)
        timer.daemon = True
        timer.start()
    try:
        server.run(sockets=[sock])
    finally:
        sock.close()


if __name__ == "__main__":
    main()
