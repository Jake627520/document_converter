"""UAT: every rejection and edge case a user can hit, with the exact message."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/document_converter")
from fastapi.testclient import TestClient
from document_converter import web_app

S = Path(__file__).parent / "samples"  # where make_samples.py writes them
PDF = (S / "01-spec-table-zh.pdf").read_bytes()
MD = "# 標題\n\n內容 84\n".encode()

def client(conf):
    web_app._RELEASE_PROFILE = None
    if conf: conf()
    return TestClient(web_app.app, headers={"host": "127.0.0.1"})

def post(c, files, data=None, headers=None):
    return c.post("/convert", data=data or {"target": "md"}, files=files, headers=headers or {})

CASES = [
    ("不支援的格式 .docx", lambda c: post(c, {"files": ("report.docx", b"stub", "application/octet-stream")})),
    ("不支援的格式 .png", lambda c: post(c, {"files": ("photo.png", b"\x89PNG stub", "image/png")})),
    ("不支援的格式 .exe", lambda c: post(c, {"files": ("payload.exe", b"MZ", "application/octet-stream")})),
    ("沒有副檔名", lambda c: post(c, {"files": ("noext", MD, "text/plain")})),
    ("單一檔案 > 24 MiB", lambda c: post(c, {"files": ("big.md", b"x" * (24*1024*1024 + 10), "text/markdown")})),
    ("6 個檔案（上限 5）", lambda c: post(c, [("files", (f"f{i}.md", MD, "text/markdown")) for i in range(6)])),
    ("0 個檔案", lambda c: post(c, [])),
    ("無效的輸出格式 docx", lambda c: post(c, {"files": ("a.md", MD, "text/markdown")}, {"target": "docx"})),
    ("非 UTF-8 的 .txt", lambda c: post(c, {"files": ("bad.txt", b"\xff\xfe\x00", "text/plain")})),
    ("空的 .md 檔", lambda c: post(c, {"files": ("empty.md", b"", "text/markdown")})),
    ("只有圖片的 PDF", lambda c: post(c, {"files": ("scan.pdf", (S/"05-image-only-no-text.pdf").read_bytes(), "application/pdf")})),
    ("JSON 給 .md 輸入", lambda c: post(c, {"files": ("a.md", MD, "text/markdown")}, {"target": "json"})),
    ("跨站 Origin", lambda c: post(c, {"files": ("a.md", MD, "text/markdown")}, None, {"Origin": "https://evil.example"})),
    ("正常 PDF（對照）", lambda c: post(c, {"files": ("spec.pdf", PDF, "application/pdf")})),
]

for label, conf in (("pdf 版 App", web_app.configure_pdf_release), ("text 版 App", web_app.configure_text_release)):
    c = client(conf)
    print(f"\n{'='*100}\n{label}\n{'='*100}")
    for name, run in CASES:
        try:
            r = run(c)
        except Exception as exc:
            print(f"  {name:22} → 例外 {type(exc).__name__}: {str(exc)[:50]}"); continue
        if r.status_code == 200:
            msg = f"成功，{len(r.content)} bytes"
        else:
            try: msg = r.json().get("detail", r.text)[:150]
            except Exception: msg = r.text[:150]
        print(f"  {name:22} → {r.status_code}  {msg}")
