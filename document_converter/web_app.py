"""Loopback-only browser interface for local document conversion."""
from __future__ import annotations

import io
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from .models import ConversionResult
from .formats import PDF_TEXT_SUPPORTED, TEXT_SUPPORTED
from .web_security import MAX_ACTIVE_REQUESTS, MAX_FILE_COUNT, RequestAdmission, RequestBodyCounter, RequestBodyTooLarge, content_length_exceeds_limit, host_is_local, origin_is_same_local, supported_suffix, valid_file_count, valid_target
from .writer import write_result

MAX_REQUEST_BYTES = 25 * 1024 * 1024
MAX_FILE_BYTES = 24 * 1024 * 1024

TEXT_PROFILE = "text-only"
PDF_PROFILE = "pdf-text"
RELEASE_FORMATS = {TEXT_PROFILE: TEXT_SUPPORTED, PDF_PROFILE: PDF_TEXT_SUPPORTED}

_RELEASE_PROFILE: str | None = None


def configure_text_release():
    """Permanently restrict this process to the reviewed text-only release."""
    _configure_release(TEXT_PROFILE)


def configure_pdf_release():
    """Permanently restrict this process to the reviewed PDF-and-text release.

    PDF conversion uses the model-free reader only, so the process never loads a
    deep-learning runtime and never downloads model weights.
    """
    _configure_release(PDF_PROFILE)


def _configure_release(profile: str):
    global _RELEASE_PROFILE
    if _RELEASE_PROFILE is not None and _RELEASE_PROFILE != profile:
        raise RuntimeError(f"This process is already configured as the {_RELEASE_PROFILE} release")
    _RELEASE_PROFILE = profile


def release_profile() -> str | None:
    return _RELEASE_PROFILE


def release_formats() -> frozenset[str] | None:
    """Input suffixes the configured release accepts, or None outside a release."""
    if _RELEASE_PROFILE is None:
        return None
    return RELEASE_FORMATS[_RELEASE_PROFILE]


def _convert_text(path):
    return ConversionResult(source=path, engine="text_direct", markdown=path.read_text(encoding="utf-8"))


def convert_one(path, engine_name, image_mode):
    """Use the same writer while keeping optional engines out of text releases."""
    if _RELEASE_PROFILE == TEXT_PROFILE:
        if path.suffix.lower() not in TEXT_SUPPORTED:
            raise ValueError("The text release accepts Markdown and UTF-8 text only")
        return _convert_text(path)
    if _RELEASE_PROFILE == PDF_PROFILE:
        suffix = path.suffix.lower()
        if suffix not in PDF_TEXT_SUPPORTED:
            raise ValueError("This release accepts PDF, Markdown and UTF-8 text only")
        if suffix != ".pdf":
            return _convert_text(path)
        # Imported here so the text-only release never reaches engine code.
        from .engines.docling_native_engine import DoclingNativePdfEngine
        return DoclingNativePdfEngine().convert(path, "none")
    from .pipeline import convert_one as pipeline_convert_one
    return pipeline_convert_one(path, engine_name, image_mode)


class LocalRequestBoundary:
    """Restrict local requests, active work, and complete ASGI body size."""

    def __init__(self, app):
        self.app = app
        self.admission = RequestAdmission(MAX_ACTIVE_REQUESTS)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        if not host_is_local(headers.get(b"host")):
            await self._error(send, 400, b"Invalid local Host header")
            return
        if scope.get("method") == "POST":
            fetch_site = headers.get(b"sec-fetch-site", b"").decode("latin-1").lower()
            if fetch_site == "cross-site":
                await self._error(send, 403, b"Cross-site requests are not allowed")
                return
            origin = headers.get(b"origin")
            if origin and not origin_is_same_local(origin, headers.get(b"host")):
                await self._error(send, 403, b"Cross-origin requests are not allowed")
                return
        if not self.admission.try_enter():
            await self._error(send, 429, b"Local converter is busy; retry shortly")
            return
        try:
            if content_length_exceeds_limit(headers.get(b"content-length"), MAX_REQUEST_BYTES):
                await self._error(send, 413, b"Request exceeds the 25 MiB limit")
                return
            counter = RequestBodyCounter(MAX_REQUEST_BYTES)

            async def limited_receive():
                message = await receive()
                if message["type"] == "http.request":
                    counter.account(len(message.get("body", b"")))
                return message

            try:
                await self.app(scope, limited_receive, send)
            except RequestBodyTooLarge:
                await self._error(send, 413, b"Request exceeds the 25 MiB limit")
        finally:
            self.admission.leave()

    @staticmethod
    async def _error(send, status: int, body: bytes):
        await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"content-length", str(len(body)).encode())]})
        await send({"type": "http.response.body", "body": body})


app = FastAPI(title="Document Converter", docs_url=None, redoc_url=None)
app.add_middleware(LocalRequestBoundary)


@app.get("/", response_class=HTMLResponse)
async def index():
    if _RELEASE_PROFILE == TEXT_PROFILE:
        return HTMLResponse(text_release_page())
    if _RELEASE_PROFILE == PDF_PROFILE:
        return HTMLResponse(pdf_release_page())
    return HTMLResponse(PAGE)


@app.post("/convert")
async def convert_upload(target: str = Form(...), files: list[UploadFile] = File(...)):
    if not valid_target(target):
        raise HTTPException(400, "Choose Markdown or HTML output.")
    if not valid_file_count(len(files)):
        raise HTTPException(400, f"Choose between 1 and {MAX_FILE_COUNT} files.")

    with tempfile.TemporaryDirectory(prefix="document-converter-") as temp_root:
        root = Path(temp_root)
        produced: list[tuple[str, bytes]] = []
        for upload in files:
            original_name = upload.filename or "document"
            suffix = supported_suffix(original_name)
            allowed = release_formats()
            if suffix is None or (allowed is not None and suffix not in allowed):
                raise HTTPException(400, "Unsupported input type")
            content = await upload.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES:
                raise HTTPException(413, "A file exceeds the 24 MiB limit")
            safe_input = root / f"input-{uuid.uuid4().hex}{suffix}"
            safe_input.write_bytes(content)
            try:
                result: ConversionResult = convert_one(safe_input, "auto", "none")
                _reject_empty_pdf(result)
                output_dir = root / f"output-{uuid.uuid4().hex}"
                write_result(result, output_dir, [target])
                output_path = output_dir / f"{safe_input.stem}.{target}"
                if not output_path.is_file():
                    raise RuntimeError("The selected output format was not produced")
                produced.append((output_path.name, output_path.read_bytes()))
            except HTTPException:
                raise
            except Exception as exc:
                # The server is loopback-only and processes the operator's own
                # files, so the reason is more useful to them than a bare failure.
                reason = str(exc).replace(str(root), "").strip()
                detail = "Conversion failed. Check the document and installed local engine."
                raise HTTPException(422, f"{detail} ({reason[:300]})" if reason else detail) from exc
            finally:
                await upload.close()

        if len(produced) == 1:
            body = produced[0][1]
            filename = f"converted-document.{target}"
            media_type = "text/markdown; charset=utf-8" if target == "md" else "text/html; charset=utf-8"
        else:
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                for index, (_, data) in enumerate(produced, start=1):
                    bundle.writestr(f"document-{index}.{target}", data)
            body = archive.getvalue()
            filename = "converted-documents.zip"
            media_type = "application/zip"

    return Response(body, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"', "X-Content-Type-Options": "nosniff"})


def _reject_empty_pdf(result: ConversionResult):
    """Tell the reader a scanned PDF produced nothing instead of sending an empty file."""
    if _RELEASE_PROFILE != PDF_PROFILE:
        return
    from .engines.docling_native_engine import NO_TEXT_WARNING

    if NO_TEXT_WARNING in result.warnings:
        raise HTTPException(
            422,
            "這個 PDF 沒有文字層（例如掃描或拍照的檔案）。此版本不包含 OCR 文字辨識，"
            "無法從影像中取出文字。",
        )


def pdf_release_page():
    """Keep the shared interface truthful about this release's inputs and limits."""
    page = PAGE.replace(
        'accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp"',
        'accept=".pdf,.md,.markdown,.txt"',
    )
    page = page.replace(
        "支援 PDF、Office、圖片、Markdown、文字與其他文件格式。",
        "支援 PDF（需有文字層）、Markdown 與 UTF-8 文字。",
    )
    page = page.replace(
        "PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文字、圖片、CSV、RTF、OpenDocument。",
        "PDF（僅限已有文字層者）、Markdown（.md、.markdown）、UTF-8 文字（.txt）。"
        "PDF 會抽取檔案內既有的文字，不重建標題階層與表格；掃描檔沒有文字層，"
        "此版本不含 OCR，轉出來會是空的。此版本不提供 Office 與圖片格式。",
    )
    return page.replace(
        "引擎或模型的網路行為取決於其安裝與設定。",
        "此版本只使用不需模型的本機 PDF 讀取器，不下載任何模型。",
    )


def text_release_page():
    """Keep the shared interface truthful about the bundled input formats."""
    page = PAGE.replace('accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp"', 'accept=".md,.markdown,.txt"')
    page = page.replace("支援 PDF、Office、圖片、Markdown、文字與其他文件格式。", "支援 Markdown 與 UTF-8 文字。")
    page = page.replace("PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文字、圖片、CSV、RTF、OpenDocument。", "Markdown（.md、.markdown）、UTF-8 文字（.txt）。此版本不提供 PDF、Office、圖片或 OCR。")
    return page.replace("引擎或模型的網路行為取決於其安裝與設定。", "此版本不包含文件引擎或模型，不需要下載模型。")


PAGE = '''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>文件轉換工作台</title>
<style>
:root{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#20252d;background:#f5f6f8;font-synthesis:none;--muted:#657080;--line:#d9dee6;--blue:#2864d7}*{box-sizing:border-box}body{margin:0;min-height:100vh}.topbar{height:68px;border-bottom:1px solid var(--line);background:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 max(24px,calc((100vw - 1120px)/2))}.brand{display:flex;align-items:center;gap:11px;font-weight:680;letter-spacing:-.02em}.mark{width:34px;height:34px;border-radius:10px;background:#20252d;color:#fff;display:grid;place-items:center}.badge{font-size:12px;color:#405065;border:1px solid var(--line);border-radius:999px;padding:7px 11px}.badge:before{content:"";display:inline-block;width:7px;height:7px;background:#36a66e;border-radius:50%;margin-right:7px}.wrap{max-width:920px;padding:66px 24px 72px;margin:auto}.eyebrow{text-transform:uppercase;font-size:11px;letter-spacing:.12em;color:var(--blue);font-weight:750}.hero h1{font-size:clamp(32px,5vw,46px);letter-spacing:-.045em;line-height:1.1;margin:12px 0}.hero p{color:var(--muted);font-size:16px;line-height:1.6;margin:0;max-width:660px}.workspace{margin-top:34px;background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 28px #20252d0b;overflow:hidden}.section{padding:26px 28px;border-bottom:1px solid #e9ecf0}.head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:16px}.section h2{font-size:15px;margin:0}.hint{font-size:12px;color:var(--muted)}.drop{min-height:190px;border:1.5px dashed #b8c4d4;border-radius:12px;background:#fafbfd;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:22px;transition:.15s}.drop.drag{border-color:var(--blue);background:#f0f5ff}.upload{width:42px;height:42px;background:#edf3ff;color:var(--blue);border-radius:12px;display:grid;place-items:center;margin-bottom:12px}.drop strong{font-size:14px}.drop p{margin:6px 0 12px;color:var(--muted);font-size:12px}.choose{background:#fff;border:1px solid var(--line);border-radius:7px;padding:8px 13px;font-size:12px;font-weight:650;cursor:pointer}.vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.files{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:8px}.row{display:flex;align-items:center;gap:11px;border:1px solid #e5e9ef;border-radius:9px;padding:10px 12px}.file-icon{width:30px;height:34px;display:grid;place-items:center;background:#f1f4f8;color:#58677b;border-radius:6px;font-size:9px;font-weight:800}.file-name{font-size:12px;font-weight:620;overflow-wrap:anywhere}.file-size{font-size:11px;color:var(--muted);margin-top:3px}.remove{margin-left:auto;border:0;background:transparent;color:#718096;cursor:pointer;padding:8px}.options{display:grid;grid-template-columns:1fr 1fr;gap:12px}.format{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:10px;padding:14px;cursor:pointer;min-height:74px}.format:has(input:checked){border-color:var(--blue);box-shadow:0 0 0 2px #2864d71a;background:#f8faff}.format input{accent-color:var(--blue);width:16px;height:16px}.ext{font-size:12px;font-weight:750;color:#33445d}.desc{display:block;font-size:11px;color:var(--muted);margin-top:4px}.format:focus-within{outline:3px solid #2864d744;outline-offset:2px}.actions{padding:20px 28px 24px;display:flex;align-items:center;gap:16px}.submit{border:0;border-radius:8px;background:var(--blue);color:white;font-weight:680;padding:11px 19px;cursor:pointer}.submit:hover{background:#1f4fae}.submit:disabled{opacity:.55;cursor:wait}.privacy{font-size:11px;line-height:1.5;color:var(--muted)}.status{margin:0 28px 20px;padding:11px 13px;border-radius:8px;background:#eff7f2;color:#1f7a55;font-size:12px;display:none}.status.show{display:block}.status.error{background:#fff1f0;color:#a13c31}.footer{margin:17px 0 0;color:#7a8492;font-size:11px;line-height:1.55}.footer strong{color:#515d6d}@media(max-width:600px){.topbar{height:60px;padding:0 18px}.wrap{padding:42px 16px 48px}.section{padding:21px 18px}.actions{padding:17px 18px 20px;align-items:flex-start;flex-direction:column}.status{margin:0 18px 18px}.options{gap:8px}.format{padding:11px 9px}.hero p{font-size:14px}}@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition:none!important}}
</style></head><body>
<header class="topbar"><div class="brand"><span class="mark" aria-hidden="true">↗</span><span>文件轉換工作台</span></div><span class="badge">僅限本機使用</span></header>
<main class="wrap"><section class="hero"><div class="eyebrow">PRIVATE DOCUMENT WORKSPACE</div><h1>讓文件轉換，<br>回到簡單。</h1><p>在這台電腦上將文件轉成 Markdown 或 HTML。選擇檔案、挑選格式，完成後立即下載。</p></section>
<form id="form" class="workspace" enctype="multipart/form-data"><section class="section"><div class="head"><h2>選擇文件</h2><span class="hint">最多 5 個檔案 · 單檔 24 MiB · 請控制總量</span></div><div id="drop" class="drop"><div class="upload" aria-hidden="true">↑</div><strong>將文件拖放到這裡</strong><p>或從電腦中選取檔案</p><label class="choose" for="files">選擇檔案</label><input class="vh" id="files" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp" aria-describedby="file-hint"><span id="file-hint" class="vh">支援 PDF、Office、圖片、Markdown、文字與其他文件格式。</span></div><ul id="list" class="files" aria-label="已選擇的文件"></ul></section>
<section class="section"><div class="head"><h2>輸出格式</h2><span class="hint">選擇一種格式</span></div><div class="options"><label class="format"><input type="radio" name="target" value="md" checked><span><span class="ext">Markdown</span><span class="desc">.md · 適合筆記與知識庫</span></span></label><label class="format"><input type="radio" name="target" value="html"><span><span class="ext">HTML</span><span class="desc">.html · 可用瀏覽器直接開啟</span></span></label></div></section><div class="actions"><button id="submit" class="submit" type="submit">開始轉換 →</button><span class="privacy">文件由本機服務處理，轉換後會立即清除暫存檔。<br>引擎或模型的網路行為取決於其安裝與設定。</span></div><p id="status" class="status" role="status" aria-live="polite"></p></form>
<p class="footer"><strong>支援格式</strong>　PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文字、圖片、CSV、RTF、OpenDocument。</p></main>
<script>
const input=document.querySelector('#files'),list=document.querySelector('#list'),drop=document.querySelector('#drop'),form=document.querySelector('#form'),status=document.querySelector('#status'),button=document.querySelector('#submit');let selected=[];
function size(n){return n<1048576?(n/1024).toFixed(0)+' KB':(n/1048576).toFixed(1)+' MB'}
function draw(){list.replaceChildren();selected.forEach((file,i)=>{const li=document.createElement('li');li.className='row';const icon=document.createElement('span');icon.className='file-icon';icon.textContent=(file.name.split('.').pop()||'FILE').slice(0,4).toUpperCase();icon.setAttribute('aria-hidden','true');const info=document.createElement('span');info.style.minWidth='0';const name=document.createElement('span');name.className='file-name';name.textContent=file.name;const meta=document.createElement('span');meta.className='file-size';meta.textContent=size(file.size);info.append(name,meta);const remove=document.createElement('button');remove.type='button';remove.className='remove';remove.textContent='移除';remove.setAttribute('aria-label','移除 '+file.name);remove.onclick=()=>{selected.splice(i,1);draw()};li.append(icon,info,remove);list.append(li)})}
function add(files){selected=selected.concat(Array.from(files)).slice(0,5);draw()}input.addEventListener('change',e=>{add(e.target.files);input.value=''});['dragenter','dragover'].forEach(name=>drop.addEventListener(name,e=>{e.preventDefault();drop.classList.add('drag')}));['dragleave','drop'].forEach(name=>drop.addEventListener(name,e=>{e.preventDefault();drop.classList.remove('drag')}));drop.addEventListener('drop',e=>add(e.dataTransfer.files));
form.addEventListener('submit',async e=>{e.preventDefault();status.className='status';if(!selected.length){status.textContent='請先選擇至少一個文件。';status.classList.add('show','error');return}if(selected.some(f=>f.size>24*1048576)){status.textContent='單一檔案超過 24 MiB，請移除或縮小檔案。';status.classList.add('show','error');return}if(selected.reduce((n,f)=>n+f.size,0)>24*1048576){status.textContent='檔案總量超過 24 MiB，請減少檔案或分批轉換。';status.classList.add('show','error');return}button.disabled=true;button.textContent='正在本機轉換…';status.textContent='文件正在這台電腦上處理。';status.classList.add('show');try{const data=new FormData();selected.forEach(file=>data.append('files',file));data.append('target',form.querySelector('[name=target]:checked').value);const response=await fetch('/convert',{method:'POST',body:data});if(!response.ok){let detail='轉換失敗。請確認文件格式及本機引擎。';try{detail=(await response.json()).detail||detail}catch{}throw new Error(detail)}const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;const disposition=response.headers.get('content-disposition')||'';const match=disposition.match(/filename="([^"]+)"/);a.download=match?match[1]:'converted-document';a.click();URL.revokeObjectURL(url);status.textContent='轉換完成，下載已開始。';status.classList.add('show')}catch(error){status.textContent=error.message;status.classList.add('show','error')}finally{button.disabled=false;button.textContent='開始轉換 →'}});
</script></body></html>'''
