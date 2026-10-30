"""Loopback-only browser interface for local document conversion."""
from __future__ import annotations

import io
import json
import re
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .models import ConversionResult
from .formats import PDF_TEXT_SUPPORTED, SUPPORTED, TEXT_SUPPORTED
from .web_security import (
    ALLOWED_TARGETS,
    CSP_DIRECTIVES,
    DEFAULT_LOCALE,
    MAX_ACTIVE_REQUESTS,
    MAX_FILE_COUNT,
    RequestAdmission,
    RequestBodyCounter,
    RequestBodyTooLarge,
    SECURITY_HEADERS,
    SUPPORTED_LOCALES,
    content_disposition,
    content_length_exceeds_limit,
    host_is_local,
    normalize_locale,
    origin_is_same_local,
    safe_output_stem,
    supported_suffix,
    valid_file_count,
    valid_target,
)
from .writer import plain_text_of, write_result

MAX_REQUEST_BYTES = 25 * 1024 * 1024
MAX_FILE_BYTES = 24 * 1024 * 1024


def size_limit(limit: int, locale: str = DEFAULT_LOCALE) -> str:
    """State a byte limit in both units a reader may be comparing against.

    The limits are set in mebibytes (1 MiB = 1,048,576 bytes), but Finder on
    macOS reports sizes in decimal megabytes (1 MB = 1,000,000 bytes). Naming
    only one leaves the reader comparing two different numbers: 24 MiB is
    about 25 MB, and a file Finder shows as 25.1 MB is still accepted.
    """
    mib = limit // (1024 * 1024)
    mb = round(limit / 1_000_000)
    if locale == "en":
        return f"{mib} MiB (approx. {mb} MB)"
    elif locale == "zh-CN":
        return f"{mib} MiB（约 {mb} MB）"
    return f"{mib} MiB（約 {mb} MB）"

TEXT_PROFILE = "text-only"
PDF_PROFILE = "pdf-text"
RELEASE_FORMATS = {TEXT_PROFILE: TEXT_SUPPORTED, PDF_PROFILE: PDF_TEXT_SUPPORTED}
# Docling JSON is the engine's own parse of a document, so a release that runs
# no engine cannot offer it at all, and in the pdf release only a PDF produces
# one: Markdown and text files are read directly. Markdown, HTML and plain text
# are available from every release, since the writer renders the last two from
# the Markdown.
RELEASE_TARGETS = {
    TEXT_PROFILE: frozenset({"md", "html", "txt"}),
    PDF_PROFILE: frozenset({"md", "html", "txt", "json"}),
}
MEDIA_TYPES = {
    "md": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
}

OUTPUT_NAMES = {"md": "Markdown", "html": "HTML", "txt": "純文字", "json": "Docling JSON"}
OUTPUT_NAMES_BY_LOCALE = {
    "zh-TW": {"md": "Markdown", "html": "HTML", "txt": "純文字", "json": "Docling JSON"},
    "zh-CN": {"md": "Markdown", "html": "HTML", "txt": "纯文本", "json": "Docling JSON"},
    "en": {"md": "Markdown", "html": "HTML", "txt": "Plain Text", "json": "Docling JSON"},
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh-TW": {
        "app_title": "文件轉換工作台",
        "brand_badge": "僅限本機使用",
        "eyebrow": "PRIVATE DOCUMENT WORKSPACE",
        "hero_h1": "讓文件轉換，<br>回到簡單。",
        "hero_p": "在這台電腦上將文件轉成 Markdown 或 HTML。選擇檔案、挑選格式，完成後立即下載。",
        "choose_doc_h2": "選擇文件",
        "choose_doc_hint": "最多 5 個檔案 · 單檔 24 MiB（約 25 MB）",
        "drop_title": "將文件拖放到這裡",
        "drop_p": "或從電腦中選取檔案",
        "choose_btn": "選擇檔案",
        "file_hint": "支援 PDF、Office、圖片、Markdown、文字與其他文件格式。",
        "file_list_aria": "已選擇的文件",
        "out_fmt_h2": "輸出格式",
        "out_fmt_hint": "選擇一種格式",
        "fmt_md_ext": "Markdown",
        "fmt_md_desc": ".md · 適合筆記與知識庫",
        "fmt_html_ext": "HTML",
        "fmt_html_desc": ".html · 可用瀏覽器直接開啟",
        "fmt_txt_ext": "純文字",
        "fmt_txt_desc": ".txt · 只有文字，不含格式",
        "fmt_json_ext": "Docling JSON",
        "fmt_json_desc": ".json · 文件結構，需引擎解析",
        "submit_btn": "開始轉換 →",
        "submitting_btn": "正在本機轉換…",
        "privacy_note": "文件由本機服務處理，轉換後會立即清除暫存檔。<br>引擎或模型的網路行為取決於其安裝與設定。",
        "footer_text": "<strong>支援格式</strong>　PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文字、圖片、CSV、RTF、OpenDocument。",
        "remove_btn": "移除",
        "remove_aria": "移除",
        "preview_heading": "預覽",
        "copy_btn": "複製內容",
        "copied_btn": "已複製！",
        "status_need_file": "請先選擇至少一個文件。",
        "status_single_limit": "單一檔案超過 24 MiB（約 25 MB），請移除或縮小檔案。",
        "status_total_limit": "檔案總量超過 24 MiB（約 25 MB），請減少檔案或分批轉換。",
        "status_processing": "文件正在這台電腦上處理。",
        "status_done": "轉換完成，下載已開始。",
        "note_model_free": "這次用的是不跑模型的 PDF 讀取方式（docling-native）：只取出文字，不還原標題層級、表格與閱讀順序。",
        "status_failed": "轉換失敗。請確認文件格式及本機引擎。",
    },
    "zh-CN": {
        "app_title": "文件转换工作台",
        "brand_badge": "仅限本地使用",
        "eyebrow": "PRIVATE DOCUMENT WORKSPACE",
        "hero_h1": "让文件转换，<br>回归简单。",
        "hero_p": "在这台电脑上将文件转成 Markdown 或 HTML。选择文件、挑选格式，完成后立即下载。",
        "choose_doc_h2": "选择文件",
        "choose_doc_hint": "最多 5 个文件 · 单文件 24 MiB（约 25 MB）",
        "drop_title": "将文件拖放到这里",
        "drop_p": "或从电脑中选取文件",
        "choose_btn": "选择文件",
        "file_hint": "支持 PDF、Office、图片、Markdown、文本与其他文档格式。",
        "file_list_aria": "已选择的文件",
        "out_fmt_h2": "输出格式",
        "out_fmt_hint": "选择一种格式",
        "fmt_md_ext": "Markdown",
        "fmt_md_desc": ".md · 适合笔记与知识库",
        "fmt_html_ext": "HTML",
        "fmt_html_desc": ".html · 可用浏览器直接打开",
        "fmt_txt_ext": "纯文本",
        "fmt_txt_desc": ".txt · 仅保留文本，无排版",
        "fmt_json_ext": "Docling JSON",
        "fmt_json_desc": ".json · 文档结构，需引擎解析",
        "submit_btn": "开始转换 →",
        "submitting_btn": "正在本地转换…",
        "privacy_note": "文件由本地服务处理，转换后立即清理临时文件。<br>引擎或模型的网络行为取决于其安装与配置。",
        "footer_text": "<strong>支持格式</strong>　PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文本、图片、CSV、RTF、OpenDocument。",
        "remove_btn": "移除",
        "remove_aria": "移除",
        "preview_heading": "预览",
        "copy_btn": "复制内容",
        "copied_btn": "已复制！",
        "status_need_file": "请先选择至少一个文件。",
        "status_single_limit": "单文件超过 24 MiB（约 25 MB），请移除或缩小文件。",
        "status_total_limit": "文件总量超过 24 MiB（约 25 MB），请减少文件或分批转换。",
        "status_processing": "文件正在这台电脑上处理。",
        "status_done": "转换完成，下载已开始。",
        "note_model_free": "这次使用的是不运行模型的 PDF 读取方式（docling-native）：只提取文本，不还原标题层级、表格和阅读顺序。",
        "status_failed": "转换失败。请检查文件格式及本地引擎。",
    },
    "en": {
        "app_title": "Document Converter Workbench",
        "brand_badge": "Local Only",
        "eyebrow": "PRIVATE DOCUMENT WORKSPACE",
        "hero_h1": "Simple, private<br>document conversion.",
        "hero_p": "Convert documents to Markdown or HTML right on this computer. Select files, choose a format, and download immediately.",
        "choose_doc_h2": "Select Documents",
        "choose_doc_hint": "Up to 5 files · 24 MiB each (approx. 25 MB)",
        "drop_title": "Drop documents here",
        "drop_p": "or choose files from your computer",
        "choose_btn": "Choose Files",
        "file_hint": "Supports PDF, Office, images, Markdown, text, and other document formats.",
        "file_list_aria": "Selected documents",
        "out_fmt_h2": "Output Format",
        "out_fmt_hint": "Choose one format",
        "fmt_md_ext": "Markdown",
        "fmt_md_desc": ".md · Best for notes and knowledge bases",
        "fmt_html_ext": "HTML",
        "fmt_html_desc": ".html · Viewable directly in any browser",
        "fmt_txt_ext": "Plain Text",
        "fmt_txt_desc": ".txt · Unformatted text only",
        "fmt_json_ext": "Docling JSON",
        "fmt_json_desc": ".json · Document structure, requires parser engine",
        "submit_btn": "Convert Now →",
        "submitting_btn": "Converting locally…",
        "privacy_note": "Documents processed locally; temporary files cleared immediately after conversion.<br>Engine and model network behavior depends on their installation and settings.",
        "footer_text": "<strong>Supported formats:</strong> PDF, Word, PowerPoint, Excel, HTML, EPUB, Markdown, Text, Images, CSV, RTF, OpenDocument.",
        "remove_btn": "Remove",
        "remove_aria": "Remove",
        "preview_heading": "Preview",
        "copy_btn": "Copy Content",
        "copied_btn": "Copied!",
        "status_need_file": "Please select at least one document.",
        "status_single_limit": "Single file exceeds 24 MiB (approx. 25 MB). Please remove or shrink the file.",
        "status_total_limit": "Total size exceeds 24 MiB (approx. 25 MB). Please reduce files or convert in batches.",
        "status_processing": "Processing document locally on this computer.",
        "status_done": "Conversion complete. Download has started.",
        "note_model_free": "This used the model-free PDF reader (docling-native): it extracts the text but does not rebuild heading levels, tables or reading order.",
        "status_failed": "Conversion failed. Please verify the document format and local engines.",
    },
}

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


def release_targets() -> frozenset[str] | None:
    """Output formats this release can produce, or None outside a release."""
    if _RELEASE_PROFILE is None:
        return None
    return RELEASE_TARGETS[_RELEASE_PROFILE]


def release_formats() -> frozenset[str] | None:
    """Input suffixes the configured release accepts, or None outside a release."""
    if _RELEASE_PROFILE is None:
        return None
    return RELEASE_FORMATS[_RELEASE_PROFILE]


def _convert_text(path):
    """UTF-8-only path used by text/pdf release profiles.

    Read here rather than through TextDirectEngine: importing anything under
    document_converter.engines runs the package's __init__, which loads every
    adapter, and the text release forbids that package outright. convert_upload's
    failure handler answers a UnicodeDecodeError by naming Big5, GBK and UTF-16.
    """
    content = path.read_text(encoding="utf-8")
    return ConversionResult(source=path, engine="text_direct", markdown=content, text=plain_text_of(content, path.suffix))


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


def _request_locale(request: Request, form_lang: str | None = None) -> str:
    """Determine client locale from form field, query parameter, or Accept-Language header."""
    if form_lang and form_lang in SUPPORTED_LOCALES:
        return form_lang
    query_lang = request.query_params.get("lang") if hasattr(request, "query_params") else None
    if query_lang:
        return normalize_locale(query_lang)
    accept = request.headers.get("accept-language")
    if accept:
        return normalize_locale(accept)
    return DEFAULT_LOCALE


class LocalRequestBoundary:
    """Restrict local requests, active work, complete ASGI body size, and enforce CSP."""

    def __init__(self, app):
        self.app = app
        self.admission = RequestAdmission(MAX_ACTIVE_REQUESTS)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def secure_send(message):
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                existing = {k.lower() for k, _ in raw_headers}
                for k, v in SECURITY_HEADERS.items():
                    key_bytes = k.lower().encode("latin-1")
                    if key_bytes not in existing:
                        raw_headers.append((key_bytes, v.encode("latin-1")))
                message["headers"] = raw_headers
            await send(message)

        headers = dict(scope.get("headers", []))
        accept = headers.get(b"accept-language", b"").decode("latin-1")
        req_locale = normalize_locale(accept) if accept else DEFAULT_LOCALE
        if not host_is_local(headers.get(b"host")):
            msg = (
                "Please open using http://127.0.0.1 or http://localhost; this service only accepts local connections."
                if req_locale == "en"
                else (
                    "请使用 http://127.0.0.1 或 http://localhost 打开；本服务仅接受本地连接。"
                    if req_locale == "zh-CN"
                    else "請用 http://127.0.0.1 或 http://localhost 開啟；本服務只接受本機連線。"
                )
            )
            await self._error(send, 400, msg.encode())
            return
        if scope.get("method") == "POST":
            fetch_site = headers.get(b"sec-fetch-site", b"").decode("latin-1").lower()
            if fetch_site == "cross-site":
                msg = (
                    "Cross-site requests are not accepted."
                    if req_locale == "en"
                    else ("不接受跨站请求。" if req_locale == "zh-CN" else "不接受跨站請求。")
                )
                await self._error(send, 403, msg.encode())
                return
            origin = headers.get(b"origin")
            if origin and not origin_is_same_local(origin, headers.get(b"host")):
                msg = (
                    "Cross-origin requests are not accepted."
                    if req_locale == "en"
                    else ("不接受跨来源请求。" if req_locale == "zh-CN" else "不接受跨來源請求。")
                )
                await self._error(send, 403, msg.encode())
                return
        if not self.admission.try_enter():
            msg = (
                "Local converter is busy, please try again later."
                if req_locale == "en"
                else ("本地转换器忙碌中，请稍后再试。" if req_locale == "zh-CN" else "本機轉換器忙碌中，請稍後再試。")
            )
            await self._error(send, 429, msg.encode())
            return
        try:
            if content_length_exceeds_limit(headers.get(b"content-length"), MAX_REQUEST_BYTES):
                msg = (
                    f"Total upload request must not exceed {size_limit(MAX_REQUEST_BYTES, req_locale)}. Please reduce file count or convert in batches."
                    if req_locale == "en"
                    else (
                        f"整个上传请求不得超过 {size_limit(MAX_REQUEST_BYTES, req_locale)}。请减少文件数量或分批转换。"
                        if req_locale == "zh-CN"
                        else f"整個上傳請求不得超過 {size_limit(MAX_REQUEST_BYTES, req_locale)}。請減少檔案數量或分批轉換。"
                    )
                )
                await self._error(send, 413, msg.encode())
                return
            counter = RequestBodyCounter(MAX_REQUEST_BYTES)

            async def limited_receive():
                message = await receive()
                if message["type"] == "http.request":
                    counter.account(len(message.get("body", b"")))
                return message

            try:
                await self.app(scope, limited_receive, secure_send)
            except RequestBodyTooLarge:
                msg = (
                    f"Total upload request must not exceed {size_limit(MAX_REQUEST_BYTES, req_locale)}. Please reduce file count or convert in batches."
                    if req_locale == "en"
                    else (
                        f"整个上传请求不得超过 {size_limit(MAX_REQUEST_BYTES, req_locale)}。请减少文件数量或分批转换。"
                        if req_locale == "zh-CN"
                        else f"整個上傳請求不得超過 {size_limit(MAX_REQUEST_BYTES, req_locale)}。請減少檔案數量或分批轉換。"
                    )
                )
                await self._error(send, 413, msg.encode())
        finally:
            self.admission.leave()

    @staticmethod
    async def _error(send, status: int, body: bytes):
        headers = [
            (b"content-type", b"text/plain; charset=utf-8"),
            (b"content-length", str(len(body)).encode()),
            (b"content-security-policy", CSP_DIRECTIVES.encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
        ]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})


app = FastAPI(title="Document Converter", docs_url=None, redoc_url=None)


@app.exception_handler(RequestValidationError)
async def _explain_invalid_request(request: Request, exc: RequestValidationError):
    """Answer a malformed request in the client's language, not with its own schema."""
    loc = _request_locale(request)
    missing_file = any(tuple(error.get("loc", ()))[-1:] == ("files",) for error in exc.errors())
    if loc == "en":
        detail = (
            f"Please select 1 to {MAX_FILE_COUNT} files." if missing_file
            else "Invalid request format. Please refresh the page and try again."
        )
    elif loc == "zh-CN":
        detail = (
            f"请先选择 1 到 {MAX_FILE_COUNT} 个文件。" if missing_file
            else "请求格式不正确。请刷新页面后重试。"
        )
    else:
        detail = (
            f"請先選擇 1 到 {MAX_FILE_COUNT} 個檔案。" if missing_file
            else "請求格式不正確。請重新整理頁面後再試一次。"
        )
    return JSONResponse(status_code=400, content={"detail": detail})


app.add_middleware(LocalRequestBoundary)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str | None = None):
    client_locale = normalize_locale(lang) if lang is not None else _request_locale(request)
    if _RELEASE_PROFILE == TEXT_PROFILE:
        return HTMLResponse(text_release_page(client_locale))
    if _RELEASE_PROFILE == PDF_PROFILE:
        return HTMLResponse(pdf_release_page(client_locale))
    return HTMLResponse(base_page(client_locale))


@app.post("/convert")
async def convert_upload(
    request: Request,
    target: str = Form(...),
    files: list[UploadFile] = File(...),
    lang: str | None = Form(None),
):
    locale = _request_locale(request, lang)
    permitted = release_targets() or ALLOWED_TARGETS
    names_map = OUTPUT_NAMES_BY_LOCALE.get(locale, OUTPUT_NAMES)
    sep = ", " if locale == "en" else "、"
    offered = sep.join(names_map[item] for item in sorted(permitted))
    if not valid_target(target):
        if locale == "en":
            raise HTTPException(400, f"Please choose an output format: {offered}.")
        elif locale == "zh-CN":
            raise HTTPException(400, f"请选择一种输出格式：{offered}。")
        raise HTTPException(400, f"請選擇一種輸出格式：{offered}。")
    if target not in permitted:
        if locale == "en":
            raise HTTPException(400, f"This release does not offer this output format. Available: {offered}.")
        elif locale == "zh-CN":
            raise HTTPException(400, f"此版本不提供这种输出格式。可用的输出：{offered}。")
        raise HTTPException(400, f"此版本不提供這種輸出格式。可用的輸出：{offered}。")
    if not valid_file_count(len(files)):
        if locale == "en":
            raise HTTPException(400, f"Please select 1 to {MAX_FILE_COUNT} files.")
        elif locale == "zh-CN":
            raise HTTPException(400, f"一次请选择 1 到 {MAX_FILE_COUNT} 个文件。")
        raise HTTPException(400, f"一次請選擇 1 到 {MAX_FILE_COUNT} 個檔案。")

    with tempfile.TemporaryDirectory(prefix="document-converter-") as temp_root:
        root = Path(temp_root)
        produced: list[tuple[str, bytes]] = []
        # Codes, not text: the page shows each in the reader's language.
        notes: set[str] = set()
        for upload in files:
            original_name = upload.filename or "document"
            suffix = supported_suffix(original_name)
            allowed = release_formats()
            if suffix is None or (allowed is not None and suffix not in allowed):
                raise HTTPException(400, _unsupported_input(suffix or Path(original_name).suffix.lower(), locale))
            content = await upload.read(MAX_FILE_BYTES + 1)
            if len(content) > MAX_FILE_BYTES:
                if locale == "en":
                    raise HTTPException(413, f"Single file must not exceed {size_limit(MAX_FILE_BYTES, locale)}. Please reduce file size or convert in batches.")
                elif locale == "zh-CN":
                    raise HTTPException(413, f"单文件不得超过 {size_limit(MAX_FILE_BYTES, locale)}。请缩小文件或分批转换。")
                raise HTTPException(413, f"單一檔案不得超過 {size_limit(MAX_FILE_BYTES, locale)}。請縮小檔案或分批轉換。")
            safe_input = root / f"input-{uuid.uuid4().hex}{suffix}"
            safe_input.write_bytes(content)
            try:
                result: ConversionResult = convert_one(safe_input, "auto", "none")
                _reject_text_free_result(result, locale)
                output_dir = root / f"output-{uuid.uuid4().hex}"
                write_result(result, output_dir, [target])
                output_path = output_dir / f"{safe_input.stem}.{target}"
                if not output_path.is_file():
                    raise HTTPException(422, _unavailable_target(target, result, locale))
                produced.append((safe_output_stem(original_name), output_path.read_bytes()))
                if result.engine == "docling-native":
                    notes.add("model-free")
            except HTTPException:
                raise
            except Exception as exc:
                cause = exc if isinstance(exc, UnicodeDecodeError) else getattr(exc, "__cause__", None)
                if isinstance(cause, UnicodeDecodeError) or "not valid UTF-8" in str(exc):
                    if locale == "en":
                        msg = f"'{original_name}' is not a UTF-8 text file. Please resave as UTF-8 in a text editor."
                    elif locale == "zh-CN":
                        msg = f"「{original_name}」不是 UTF-8 编码的文本文件（常见的为 Big5、GBK 或 UTF-16）。请先使用文本编辑器另存为 UTF-8 后再转换。"
                    else:
                        msg = f"「{original_name}」不是 UTF-8 編碼的文字檔（常見的是 Big5、GBK 或 UTF-16）。請先用文字編輯器另存為 UTF-8 再轉換。"
                    raise HTTPException(422, msg) from exc
                missing = _missing_component(exc)
                if missing is not None:
                    raise HTTPException(422, _missing_component_message(original_name, missing, locale)) from exc
                reason = str(exc).replace(str(safe_input), f"「{original_name}」")
                reason = reason.replace(safe_input.name, f"「{original_name}」").replace(str(root), "").strip()
                if locale == "en":
                    detail = "Conversion failed. Please verify the file content and local engines."
                elif locale == "zh-CN":
                    detail = "转换失败。请确认文件内容与本地安装的引擎。"
                else:
                    detail = "轉換失敗。請確認檔案內容與本機已安裝的引擎。"
                raise HTTPException(422, f"{detail} ({reason[:300]})" if reason else detail) from exc
            finally:
                await upload.close()

        if len(produced) == 1:
            stem, body = produced[0]
            disposition = content_disposition(stem, target)
            media_type = MEDIA_TYPES[target]
        else:
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                names = _archive_names([stem for stem, _ in produced], target)
                for name, (_, data) in zip(names, produced):
                    bundle.writestr(name, data)
            body = archive.getvalue()
            disposition = content_disposition("converted-documents", "zip")
            media_type = "application/zip"

    headers = {"Content-Disposition": disposition, "X-Content-Type-Options": "nosniff"}
    if notes:
        headers["X-Conversion-Notes"] = ",".join(sorted(notes))
    return Response(body, media_type=media_type, headers=headers)


def _archive_names(stems: list[str], target: str) -> list[str]:
    """Distinct entry names, so two uploads sharing a name do not overwrite each other."""
    taken: set[str] = set()
    names = []
    for stem in stems:
        candidate = f"{stem}.{target}"
        index = 1
        while candidate in taken:
            index += 1
            candidate = f"{stem}-{index}.{target}"
        taken.add(candidate)
        names.append(candidate)
    return names


def _accepted_inputs(locale: str = DEFAULT_LOCALE) -> str:
    """The accepted suffixes, so a rejection can say what would work."""
    allowed = release_formats()
    formats = sorted(allowed if allowed is not None else SUPPORTED)
    sep = ", " if locale == "en" else "、"
    return sep.join(formats)


def _unsupported_input(suffix: str, locale: str = DEFAULT_LOCALE) -> str:
    """Rejecting a file is only useful if it also says what this release takes."""
    if locale == "en":
        named = f"does not support '{suffix}' files" if suffix else "does not support files without an extension"
        return f"This release {named}. Accepted formats: {_accepted_inputs(locale)}."
    elif locale == "zh-CN":
        named = f"不支持「{suffix}」文件" if suffix else "不支持没有扩展名的文件"
        return f"该版本{named}。可转换格式：{_accepted_inputs(locale)}。"
    else:
        named = f"不支援「{suffix}」檔案" if suffix else "不支援沒有副檔名的檔案"
        return f"這個版本{named}。可以轉換的格式：{_accepted_inputs(locale)}。"


def _no_text_recovered(result: ConversionResult, locale: str = DEFAULT_LOCALE) -> str:
    """Never hand over an empty file; say what happened instead."""
    allowed = release_formats()
    if allowed is not None and not allowed - TEXT_SUPPORTED:
        if locale == "en":
            return "No text was extracted from this file. The file may be empty or contain only whitespace."
        elif locale == "zh-CN":
            return "该文件未提取出任何文本。文件可能为空，或仅包含空白字符。"
        else:
            return "這個檔案沒有抽出任何文字。檔案可能是空的，或只有空白。"

    profile = result.metadata.get("pdf_profile") if result.metadata else None
    if profile is not None and profile.classification == "unknown":
        if locale == "en":
            return (
                "No text was extracted from this file. The file structure could not be parsed reliably "
                "or may be empty. Extracting text requires a readable text layer or an OCR-capable engine."
            )
        elif locale == "zh-CN":
            return (
                "该文件未提取出任何文本。文件结构无法可靠解析或文件为空。"
                "提取文本需要可读取的文本层或具备 OCR 的引擎。"
            )
        else:
            return (
                "這個檔案沒有抽出任何文字。檔案結構無法可靠解析或檔案是空的。"
                "取出文字需要可讀取的文字層或具備 OCR 的引擎。"
            )

    if locale == "en":
        remedy = (
            "This release does not include OCR text recognition."
            if _RELEASE_PROFILE is not None
            else (
                f"Scanned files require an OCR-capable engine (used: {result.engine}). "
                "This project ships none; Marker or MinerU can be installed separately, under their own terms. "
                "`document-converter list-engines` shows what is installed."
            )
        )
        return (
            "No text was extracted from this file. It may be a scanned document, image-only page, "
            f"or empty. {remedy}"
        )
    elif locale == "zh-CN":
        remedy = (
            "此版本不包含 OCR 文本识别，无法从图像中提取文本。"
            if _RELEASE_PROFILE is not None
            else (
                f"扫描件需要具备 OCR 的引擎才能提取文本（本次使用的引擎：{result.engine}）。"
                "本项目不附带 OCR；可另行安装 Marker 或 MinerU，并按其各自的条款使用。"
                "`document-converter list-engines` 会列出已安装的引擎。"
            )
        )
        return (
            "该文件未提取出任何文本。可能是扫描或拍照的文件（仅有图像、无文本层）、"
            f"整页均为图片，或文件本身为空。{remedy}"
        )
    else:
        remedy = (
            "此版本不包含 OCR 文字辨識，無法從影像中取出文字。"
            if _RELEASE_PROFILE is not None
            else (
                f"掃描檔需要具備 OCR 的引擎才能取出文字（這次使用的引擎：{result.engine}）。"
                "本專案不附 OCR；可另行安裝 Marker 或 MinerU，並依其各自的條款使用。"
                "`document-converter list-engines` 會列出已安裝的引擎。"
            )
        )
        return (
            "這個檔案沒有抽出任何文字。可能是掃描或拍照的檔案（只有影像、沒有文字層）、"
            f"整頁都是圖片，或檔案本身是空的。{remedy}"
        )


def _missing_component(error: BaseException) -> ImportError | None:
    failures = getattr(error, "failures", ()) or (error,)
    causes = []
    for failure in failures:
        while failure is not None and not isinstance(failure, ImportError):
            failure = failure.__cause__
        causes.append(failure)
    return causes[0] if all(causes) else None


_INSTALL_HINT = re.compile(r"pip install [^`\n]+")


def _missing_component_message(original_name: str, error: ImportError, locale: str = DEFAULT_LOCALE) -> str:
    module = error.name or getattr(error.__cause__, "name", None)
    hint = _INSTALL_HINT.search(str(error))
    if locale == "en":
        named = f" (Python module {module})" if module else ""
        how = (
            f"Install with: {hint.group(0).strip()}" if hint
            else "Please install the corresponding engine according to the README 'Running from source' section and try again."
        )
        return f"This installation lacks a component required to convert '{original_name}'{named}, so it cannot be converted. {how}"
    elif locale == "zh-CN":
        named = f"（Python 模块 {module}）" if module else ""
        how = (
            f"安装方式：{hint.group(0).strip()}" if hint
            else "请依 README「从源代码运行」一节安装对应的引擎后再试。"
        )
        return f"该安装缺少转换「{original_name}」所需的组件{named}，所以无法转换。{how}"
    else:
        named = f"（Python 模組 {module}）" if module else ""
        how = (
            f"安裝方式：{hint.group(0).strip()}" if hint
            else "請依 README「從原始碼執行」一節安裝對應的引擎後再試。"
        )
        return f"這個安裝缺少轉換「{original_name}」所需的元件{named}，所以無法轉換。{how}"


def _unavailable_target(target: str, result: ConversionResult, locale: str = DEFAULT_LOCALE) -> str:
    if target == "json":
        if locale == "en":
            return (
                "This file has no Docling JSON output. JSON is a parsed structure from a document engine; "
                "Markdown and plain text files are read directly without engine parsing. "
                "Please use Markdown, HTML, or plain text."
            )
        elif locale == "zh-CN":
            return (
                "该文件无可输出的 Docling JSON。JSON 是文档引擎解析出的结构，"
                "Markdown 与纯文本文件为直接读取，未经过引擎解析。请改用 Markdown、HTML 或纯文本。"
            )
        else:
            return (
                "這個檔案沒有可輸出的 Docling JSON。JSON 是文件引擎解析出來的結構，"
                "Markdown 與純文字檔是直接讀取的，沒有經過引擎解析。請改用 Markdown、HTML 或純文字。"
            )
    if locale == "en":
        return f"This file cannot produce {target} format (engine: {result.engine})."
    elif locale == "zh-CN":
        return f"该文件无法输出 {target} 格式（引擎：{result.engine}）。"
    else:
        return f"這個檔案無法輸出 {target} 格式（引擎：{result.engine}）。"


def _reject_text_free_result(result: ConversionResult, locale: str = DEFAULT_LOCALE):
    if not result.has_recovered_text():
        raise HTTPException(422, _no_text_recovered(result, locale))


def pdf_release_page(locale: str = DEFAULT_LOCALE) -> str:
    """Keep the shared interface truthful about this release's inputs and limits."""
    page = base_page(locale)
    page = page.replace(
        'accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp"',
        'accept=".pdf,.md,.markdown,.txt"',
    )
    if locale == "en":
        page = page.replace(
            "Supports PDF, Office, images, Markdown, text, and other document formats.",
            "Supports PDF (with text layer), Markdown, and UTF-8 text.",
        )
        page = page.replace(
            "PDF, Word, PowerPoint, Excel, HTML, EPUB, Markdown, text, image, CSV, RTF, OpenDocument.",
            "PDF (text layer only), Markdown (.md, .markdown), UTF-8 text (.txt). "
            "Extracts existing text from PDF without OCR. Office and image formats are not supported in this release.",
        )
        page = page.replace(".json · Document structure, requires engine", ".json · Document structure, PDF only")
        page = page.replace(
            "Engine or model network activity depends on installation and configuration.",
            "This release uses a model-free local PDF reader only and never downloads any models.",
        )
    elif locale == "zh-CN":
        page = page.replace(
            "支持 PDF、Office、图片、Markdown、文本与其他文档格式。",
            "支持 PDF（需有文本层）、Markdown 与 UTF-8 文本。",
        )
        page = page.replace(
            "PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文本、图片、CSV、RTF、OpenDocument。",
            "PDF（仅限已有文本层者）、Markdown（.md、.markdown）、UTF-8 文本（.txt）。"
            "PDF 会提取文件内既有的文本，不重建标题层级与表格；扫描件没有文本层，"
            "此版本不含 OCR，转出来会是空的。此版本不提供 Office 与图片格式。",
        )
        page = page.replace(".json · 文档结构，需引擎解析", ".json · 文档结构，仅 PDF 可输出")
        page = page.replace(
            "引擎或模型的网络行为取决于其安装与设置。",
            "此版本只使用不需模型的本地 PDF 读取器，不下载任何模型。",
        )
    else:
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
        page = page.replace(".json · 文件結構，需引擎解析", ".json · 文件結構，僅 PDF 可輸出")
        page = page.replace(
            "引擎或模型的網路行為取決於其安裝與設定。",
            "此版本只使用不需模型的本機 PDF 讀取器，不下載任何模型。",
        )
    return page


def text_release_page(locale: str = DEFAULT_LOCALE) -> str:
    """Keep the shared interface truthful about the bundled input formats."""
    page = base_page(locale)
    page = page.replace(
        'accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp"',
        'accept=".md,.markdown,.txt"',
    )
    if locale == "en":
        page = page.replace(
            "Supports PDF, Office, images, Markdown, text, and other document formats.",
            "Supports Markdown and UTF-8 text.",
        )
        page = page.replace(
            "PDF, Word, PowerPoint, Excel, HTML, EPUB, Markdown, text, image, CSV, RTF, OpenDocument.",
            "Markdown (.md, .markdown), UTF-8 text (.txt). This release does not provide PDF, Office, images, or OCR.",
        )
        page = page.replace(
            '<label class="format"><input type="radio" name="target" value="json"><span><span class="ext" id="fmt_json_ext">Docling JSON</span><span class="desc" id="fmt_json_desc">.json · Document structure, requires engine</span></span></label>',
            "",
        )
        page = page.replace(
            "Engine or model network activity depends on installation and configuration.",
            "This release contains no document engines or models and does not download models.",
        )
    elif locale == "zh-CN":
        page = page.replace(
            "支持 PDF、Office、图片、Markdown、文本与其他文档格式。",
            "支持 Markdown 与 UTF-8 文本。",
        )
        page = page.replace(
            "PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文本、图片、CSV、RTF、OpenDocument。",
            "Markdown（.md、.markdown）、UTF-8 文本（.txt）。此版本不提供 PDF、Office、图片或 OCR。",
        )
        page = page.replace(
            '<label class="format"><input type="radio" name="target" value="json"><span><span class="ext" id="fmt_json_ext">Docling JSON</span><span class="desc" id="fmt_json_desc">.json · 文档结构，需引擎解析</span></span></label>',
            "",
        )
        page = page.replace(
            "引擎或模型的网络行为取决于其安装与设置。",
            "此版本不包含文档引擎或模型，不需要下载模型。",
        )
    else:
        page = page.replace(
            "支援 PDF、Office、圖片、Markdown、文字與其他文件格式。",
            "支援 Markdown 與 UTF-8 文字。",
        )
        page = page.replace(
            "PDF、Word、PowerPoint、Excel、HTML、EPUB、Markdown、文字、圖片、CSV、RTF、OpenDocument。",
            "Markdown（.md、.markdown）、UTF-8 文字（.txt）。此版本不提供 PDF、Office、圖片或 OCR。",
        )
        page = page.replace(
            '<label class="format"><input type="radio" name="target" value="json"><span><span class="ext" id="fmt_json_ext">Docling JSON</span><span class="desc" id="fmt_json_desc">.json · 文件結構，需引擎解析</span></span></label>',
            "",
        )
        page = page.replace(
            "引擎或模型的網路行為取決於其安裝與設定。",
            "此版本不包含文件引擎或模型，不需要下載模型。",
        )
    return page


def base_page(locale: str = DEFAULT_LOCALE) -> str:
    """Generate the workbench HTML page for the given locale."""
    t = TRANSLATIONS.get(locale, TRANSLATIONS[DEFAULT_LOCALE])
    i18n_json = json.dumps(TRANSLATIONS, ensure_ascii=False)
    lang_select_aria = (
        "選擇語言" if locale == "zh-TW" else ("选择语言" if locale == "zh-CN" else "Language selection")
    )
    preview_title = (
        "文件預覽" if locale == "zh-TW" else ("文档预览" if locale == "zh-CN" else "Document Preview")
    )
    return f'''<!doctype html>
<html lang="{locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>{t["app_title"]}</title>
<style>
:root{{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#20252d;background:#f5f6f8;font-synthesis:none;--muted:#657080;--line:#d9dee6;--blue:#2864d7}}*{{box-sizing:border-box}}body{{margin:0;min-height:100vh}}.topbar{{height:68px;border-bottom:1px solid var(--line);background:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 max(24px,calc((100vw - 1120px)/2))}}.topbar-right{{display:flex;align-items:center;gap:10px}}.brand{{display:flex;align-items:center;gap:11px;font-weight:680;letter-spacing:-.02em}}.mark{{width:34px;height:34px;border-radius:10px;background:#20252d;color:#fff;display:grid;place-items:center}}.badge{{font-size:12px;color:#405065;border:1px solid var(--line);border-radius:999px;padding:7px 11px}}.badge:before{{content:"";display:inline-block;width:7px;height:7px;background:#36a66e;border-radius:50%;margin-right:7px}}.lang-select{{background:#fff;border:1px solid var(--line);border-radius:7px;padding:6px 10px;font-size:12px;color:#405065;cursor:pointer;font-family:inherit}}.wrap{{max-width:920px;padding:66px 24px 72px;margin:auto}}.eyebrow{{text-transform:uppercase;font-size:11px;letter-spacing:.12em;color:var(--blue);font-weight:750}}.hero h1{{font-size:clamp(32px,5vw,46px);letter-spacing:-.045em;line-height:1.1;margin:12px 0}}.hero p{{color:var(--muted);font-size:16px;line-height:1.6;margin:0;max-width:660px}}.workspace{{margin-top:34px;background:#fff;border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 28px #20252d0b;overflow:hidden}}.section{{padding:26px 28px;border-bottom:1px solid #e9ecf0}}.head{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:16px}}.section h2{{font-size:15px;margin:0}}.hint{{font-size:12px;color:var(--muted)}}.drop{{min-height:190px;border:1.5px dashed #b8c4d4;border-radius:12px;background:#fafbfd;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:22px;transition:.15s}}.drop.drag{{border-color:var(--blue);background:#f0f5ff}}.upload{{width:42px;height:42px;background:#edf3ff;color:var(--blue);border-radius:12px;display:grid;place-items:center;margin-bottom:12px}}.drop strong{{font-size:14px}}.drop p{{margin:6px 0 12px;color:var(--muted);font-size:12px}}.choose{{background:#fff;border:1px solid var(--line);border-radius:7px;padding:8px 13px;font-size:12px;font-weight:650;cursor:pointer}}.vh{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}}.files{{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:8px}}.row{{display:flex;align-items:center;gap:11px;border:1px solid #e5e9ef;border-radius:9px;padding:10px 12px}}.file-icon{{width:30px;height:34px;display:grid;place-items:center;background:#f1f4f8;color:#58677b;border-radius:6px;font-size:9px;font-weight:800}}.file-name{{font-size:12px;font-weight:620;overflow-wrap:anywhere}}.file-size{{font-size:11px;color:var(--muted);margin-top:3px}}.remove{{margin-left:auto;border:0;background:transparent;color:#718096;cursor:pointer;padding:8px}}.options{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.format{{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:10px;padding:14px;cursor:pointer;min-height:74px}}.format:has(input:checked){{border-color:var(--blue);box-shadow:0 0 0 2px #2864d71a;background:#f8faff}}.format input{{accent-color:var(--blue);width:16px;height:16px}}.ext{{font-size:12px;font-weight:750;color:#33445d}}.desc{{display:block;font-size:11px;color:var(--muted);margin-top:4px}}.format:focus-within{{outline:3px solid #2864d744;outline-offset:2px}}.preview-section{{padding:26px 28px;border-bottom:1px solid #e9ecf0}}.preview-frame{{width:100%;height:380px;border:1px solid var(--line);border-radius:8px;background:#fff}}.preview-pre{{max-height:380px;overflow:auto;background:#fafbfd;border:1px solid var(--line);border-radius:8px;padding:14px;font-size:12px;line-height:1.5;margin:0;white-space:pre-wrap;word-break:break-all}}.copy-btn{{background:#fff;border:1px solid var(--line);border-radius:7px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;color:#405065}}.actions{{padding:20px 28px 24px;display:flex;align-items:center;gap:16px}}.submit{{border:0;border-radius:8px;background:var(--blue);color:white;font-weight:680;padding:11px 19px;cursor:pointer}}.submit:hover{{background:#1f4fae}}.submit:disabled{{opacity:.55;cursor:wait}}.privacy{{font-size:11px;line-height:1.5;color:var(--muted)}}.status{{margin:0 28px 20px;padding:11px 13px;border-radius:8px;background:#eff7f2;color:#1f7a55;font-size:12px;display:none}}.status.show{{display:block}}.status.error{{background:#fff1f0;color:#a13c31}}.footer{{margin:17px 0 0;color:#7a8492;font-size:11px;line-height:1.55}}.footer strong{{color:#515d6d}}@media(max-width:600px){{.topbar{{height:60px;padding:0 18px}}.wrap{{padding:42px 16px 48px}}.section,.preview-section{{padding:21px 18px}}.actions{{padding:17px 18px 20px;align-items:flex-start;flex-direction:column}}.status{{margin:0 18px 18px}}.options{{gap:8px}}.format{{padding:11px 9px}}.hero p{{font-size:14px}}}}@media(prefers-reduced-motion:reduce){{*,*:before,*:after{{scroll-behavior:auto!important;transition:none!important}}}}
</style></head><body>
<script id="i18n-data" type="application/json">{i18n_json}</script>
<header class="topbar"><div class="brand"><span class="mark" aria-hidden="true">↗</span><span id="app-title">{t["app_title"]}</span></div><div class="topbar-right"><select id="lang-select" class="lang-select" aria-label="{lang_select_aria}"><option value="zh-TW"{" selected" if locale == "zh-TW" else ""}>繁體中文</option><option value="zh-CN"{" selected" if locale == "zh-CN" else ""}>简体中文</option><option value="en"{" selected" if locale == "en" else ""}>English</option></select><span class="badge" id="brand-badge">{t["brand_badge"]}</span></div></header>
<main class="wrap"><section class="hero"><div class="eyebrow" id="eyebrow">{t["eyebrow"]}</div><h1 id="hero-h1">{t["hero_h1"]}</h1><p id="hero-p">{t["hero_p"]}</p></section>
<form id="form" class="workspace" enctype="multipart/form-data"><section class="section"><div class="head"><h2 id="choose_doc_h2">{t["choose_doc_h2"]}</h2><span class="hint" id="choose_doc_hint">{t["choose_doc_hint"]}</span></div><div id="drop" class="drop"><div class="upload" aria-hidden="true">↑</div><strong id="drop_title">{t["drop_title"]}</strong><p id="drop_p">{t["drop_p"]}</p><label class="choose" for="files" id="choose_btn">{t["choose_btn"]}</label><input class="vh" id="files" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.html,.htm,.epub,.md,.markdown,.txt,.png,.jpg,.jpeg,.webp,.csv,.rtf,.odt,.ods,.odp" aria-describedby="file-hint"><span id="file-hint" class="vh">{t["file_hint"]}</span></div><ul id="list" class="files" aria-label="{t["file_list_aria"]}"></ul></section>
<section class="section"><div class="head"><h2 id="out_fmt_h2">{t["out_fmt_h2"]}</h2><span class="hint" id="out_fmt_hint">{t["out_fmt_hint"]}</span></div><div class="options"><label class="format"><input type="radio" name="target" value="md" checked><span><span class="ext" id="fmt_md_ext">{t["fmt_md_ext"]}</span><span class="desc" id="fmt_md_desc">{t["fmt_md_desc"]}</span></span></label><label class="format"><input type="radio" name="target" value="html"><span><span class="ext" id="fmt_html_ext">{t["fmt_html_ext"]}</span><span class="desc" id="fmt_html_desc">{t["fmt_html_desc"]}</span></span></label><label class="format"><input type="radio" name="target" value="txt"><span><span class="ext" id="fmt_txt_ext">{t["fmt_txt_ext"]}</span><span class="desc" id="fmt_txt_desc">{t["fmt_txt_desc"]}</span></span></label><label class="format"><input type="radio" name="target" value="json"><span><span class="ext" id="fmt_json_ext">{t["fmt_json_ext"]}</span><span class="desc" id="fmt_json_desc">{t["fmt_json_desc"]}</span></span></label></div></section>
<section id="preview-section" class="preview-section" style="display:none"><div class="head"><h2 id="preview-heading">{t["preview_heading"]}</h2><button type="button" id="copy-preview" class="copy-btn">{t["copy_btn"]}</button></div><div id="preview-frame-wrap" class="preview-frame-wrap" style="display:none"><iframe id="preview-frame" sandbox="" class="preview-frame" title="{preview_title}"></iframe></div><div id="preview-raw-wrap" class="preview-raw-wrap" style="display:none"><pre class="preview-pre"><code id="preview-code"></code></pre></div></section>
<div class="actions"><button id="submit" class="submit" type="submit">{t["submit_btn"]}</button><span class="privacy" id="privacy-note">{t["privacy_note"]}</span></div><p id="status" class="status" role="status" aria-live="polite"></p></form>
<p class="footer" id="footer-text">{t["footer_text"]}</p></main>
<script>
const input=document.querySelector('#files'),list=document.querySelector('#list'),drop=document.querySelector('#drop'),form=document.querySelector('#form'),status=document.querySelector('#status'),button=document.querySelector('#submit'),langSelect=document.querySelector('#lang-select'),copyBtn=document.querySelector('#copy-preview'),previewSection=document.querySelector('#preview-section'),previewFrameWrap=document.querySelector('#preview-frame-wrap'),previewFrame=document.querySelector('#preview-frame'),previewRawWrap=document.querySelector('#preview-raw-wrap'),previewCode=document.querySelector('#preview-code');let selected=[];let currentPreviewText='';
const I18N=JSON.parse(document.getElementById('i18n-data').textContent);let currentLang=document.documentElement.lang||'zh-TW';
function t(k){{return (I18N[currentLang]&&I18N[currentLang][k])||(I18N['en']&&I18N['en'][k])||k}}
function size(n){{return n<1e6?(n/1e3).toFixed(0)+' KB':(n/1e6).toFixed(1)+' MB'}}
function draw(){{list.replaceChildren();selected.forEach((file,i)=>{{const li=document.createElement('li');li.className='row';const icon=document.createElement('span');icon.className='file-icon';icon.textContent=(file.name.split('.').pop()||'FILE').slice(0,4).toUpperCase();icon.setAttribute('aria-hidden','true');const info=document.createElement('span');info.style.minWidth='0';const name=document.createElement('span');name.className='file-name';name.textContent=file.name;const meta=document.createElement('span');meta.className='file-size';meta.textContent=size(file.size);info.append(name,meta);const remove=document.createElement('button');remove.type='button';remove.className='remove';remove.textContent=t('remove_btn');remove.setAttribute('aria-label',t('remove_aria')+' '+file.name);remove.onclick=()=>{{selected.splice(i,1);draw()}};li.append(icon,info,remove);list.append(li)}})}}
function add(files){{selected=selected.concat(Array.from(files)).slice(0,5);draw()}}input.addEventListener('change',e=>{{add(e.target.files);input.value=''}});['dragenter','dragover'].forEach(name=>drop.addEventListener(name,e=>{{e.preventDefault();drop.classList.add('drag')}}));['dragleave','drop'].forEach(name=>drop.addEventListener(name,e=>{{e.preventDefault();drop.classList.remove('drag')}}));drop.addEventListener('drop',e=>add(e.dataTransfer.files));
function detectLanguage(){{let saved=null;try{{saved=localStorage.getItem('doc_conv_lang')}}catch(e){{}}if(saved&&I18N[saved])return saved;const nav=(navigator.languages&&navigator.languages[0])||navigator.language||'';const lower=nav.toLowerCase();const parts=lower.split(/[-_]/);if(parts[0]==='zh'){{if(parts.includes('hant'))return 'zh-TW';if(parts.includes('hans'))return 'zh-CN';if(['tw','hk','mo'].some(p=>parts.includes(p)))return 'zh-TW';return 'zh-CN'}}if(lower.startsWith('en'))return 'en';return 'en'}}
function updateLanguage(lang,persist=true){{if(!I18N[lang])lang='en';currentLang=lang;if(persist){{try{{localStorage.setItem('doc_conv_lang',lang)}}catch(e){{}}}}document.documentElement.lang=lang;if(langSelect){{langSelect.value=lang;langSelect.setAttribute('aria-label',lang==='zh-TW'?'選擇語言':(lang==='zh-CN'?'选择语言':'Language selection'))}}if(previewFrame){{previewFrame.title=lang==='zh-TW'?'文件預覽':(lang==='zh-CN'?'文档预览':'Document Preview')}}const textIds=['app-title','brand-badge','eyebrow','hero-p','choose_doc_h2','choose_doc_hint','drop_title','drop_p','choose_btn','file-hint','out_fmt_h2','out_fmt_hint','fmt_md_ext','fmt_md_desc','fmt_html_ext','fmt_html_desc','fmt_txt_ext','fmt_txt_desc','fmt_json_ext','fmt_json_desc','preview-heading','copy-preview'];const keyMap={{'app-title':'app_title','brand-badge':'brand_badge','eyebrow':'eyebrow','hero-p':'hero_p','choose_doc_h2':'choose_doc_h2','choose_doc_hint':'choose_doc_hint','drop_title':'drop_title','drop_p':'drop_p','choose_btn':'choose_btn','file-hint':'file_hint','out_fmt_h2':'out_fmt_h2','out_fmt_hint':'out_fmt_hint','fmt_md_ext':'fmt_md_ext','fmt_md_desc':'fmt_md_desc','fmt_html_ext':'fmt_html_ext','fmt_html_desc':'fmt_html_desc','fmt_txt_ext':'fmt_txt_ext','fmt_txt_desc':'fmt_txt_desc','fmt_json_ext':'fmt_json_ext','fmt_json_desc':'fmt_json_desc','preview-heading':'preview_heading','copy-preview':'copy_btn'}};textIds.forEach(id=>{{const el=document.getElementById(id);if(el)el.textContent=t(keyMap[id])}});const heroH1=document.getElementById('hero-h1');if(heroH1)heroH1.innerHTML=t('hero_h1');const priv=document.getElementById('privacy-note');if(priv)priv.innerHTML=t('privacy_note');const footer=document.getElementById('footer-text');if(footer)footer.innerHTML=t('footer_text');const list=document.getElementById('list');if(list)list.setAttribute('aria-label',t('file_list_aria'));if(button&&!button.disabled)button.textContent=t('submit_btn');draw()}}
if(langSelect)langSelect.addEventListener('change',e=>updateLanguage(e.target.value));
const detected=detectLanguage();if(detected&&detected!==currentLang&&!location.search.includes('lang='))updateLanguage(detected,false);
if(copyBtn)copyBtn.addEventListener('click',async()=>{{if(!currentPreviewText)return;try{{await navigator.clipboard.writeText(currentPreviewText);copyBtn.textContent=t('copied_btn');setTimeout(()=>{{copyBtn.textContent=t('copy_btn')}},2000)}}catch(err){{}}}});
form.addEventListener('submit',async e=>{{e.preventDefault();status.className='status';if(!selected.length){{status.textContent=t('status_need_file');status.classList.add('show','error');return}}if(selected.some(f=>f.size>24*1048576)){{status.textContent=t('status_single_limit');status.classList.add('show','error');return}}if(selected.reduce((n,f)=>n+f.size,0)>24*1048576){{status.textContent=t('status_total_limit');status.classList.add('show','error');return}}button.disabled=true;button.textContent=t('submitting_btn');status.textContent=t('status_processing');status.classList.add('show');try{{const data=new FormData();selected.forEach(file=>data.append('files',file));const targetVal=form.querySelector('[name=target]:checked').value;data.append('target',targetVal);data.append('lang',currentLang);const response=await fetch('/convert',{{method:'POST',headers:{{'Accept-Language':currentLang}},body:data}});if(!response.ok){{let detail=t('status_failed');try{{detail=(await response.json()).detail||detail}}catch{{}}throw new Error(detail)}}const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;const disposition=response.headers.get('content-disposition')||'';const encoded=disposition.match(/UTF-8''([^;]+)/i);const plain=disposition.match(/filename="([^"]+)"/);a.download=encoded?decodeURIComponent(encoded[1]):(plain?plain[1]:'converted-document');a.click();URL.revokeObjectURL(url);if(selected.length===1&&previewSection){{try{{const text=await blob.text();currentPreviewText=text;previewSection.style.display='block';if(targetVal==='html'){{previewFrameWrap.style.display='block';previewRawWrap.style.display='none';previewFrame.srcdoc=text}}else{{previewFrameWrap.style.display='none';previewRawWrap.style.display='block';previewCode.textContent=text}}}}catch(err){{}}}}const notes=(response.headers.get('x-conversion-notes')||'').split(',');status.textContent=t('status_done')+(notes.includes('model-free')?(currentLang==='en'?' ':'')+t('note_model_free'):'');status.classList.add('show')}}catch(error){{status.textContent=error.message;status.classList.add('show','error')}}finally{{button.disabled=false;button.textContent=t('submit_btn')}}}});
</script></body></html>'''


PAGE = base_page(DEFAULT_LOCALE)

