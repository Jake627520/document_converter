"""Shared web workbench launcher for the fixed text-only macOS release."""
from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
import webbrowser

import uvicorn
from document_converter import web_app


def main():
    parser = argparse.ArgumentParser(description="Local Markdown/UTF-8 text converter")
    parser.add_argument("--port", type=int, default=0, help="Loopback port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser (automated validation)")
    parser.add_argument("--diagnostics", action="store_true", help="Report runtime isolation and exit")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    web_app.configure_text_release()
    forbidden = ("fitz", "pymupdf", "docling", "torch", "marker", "magic_pdf", "pytest", "document_converter.pipeline", "document_converter.detector", "document_converter.engines")
    loaded = [name for name in sys.modules if any(name == item or name.startswith(item + ".") for item in forbidden)]
    if loaded:
        raise RuntimeError(f"Unexpected release modules: {loaded}")
    if args.diagnostics:
        print(json.dumps({"profile": "text-only", "frozen": bool(getattr(sys, "frozen", False)), "python": sys.version, "paths": sys.path, "forbidden_loaded": loaded}, indent=2))
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
