"""Small standard-library validation helpers shared by the local web app."""
import re
from urllib.parse import quote, urlsplit
from threading import Lock

from .formats import SUPPORTED

ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}
ALLOWED_TARGETS = {"md", "html", "json", "txt"}
MAX_FILE_COUNT = 5
MAX_ACTIVE_REQUESTS = 2


class RequestAdmission:
    """Non-blocking cap for active requests; callers release in a finally block."""

    def __init__(self, limit: int = MAX_ACTIVE_REQUESTS):
        if limit < 1:
            raise ValueError("request limit must be at least one")
        self.limit = limit
        self._active = 0
        self._lock = Lock()

    def try_enter(self) -> bool:
        with self._lock:
            if self._active >= self.limit:
                return False
            self._active += 1
            return True

    def leave(self) -> None:
        with self._lock:
            if self._active < 1:
                raise RuntimeError("request admission released without acquisition")
            self._active -= 1

    @property
    def active(self) -> int:
        with self._lock:
            return self._active


class RequestBodyTooLarge(Exception):
    """Raised before forwarding a body chunk that would exceed the cap."""


class RequestBodyCounter:
    def __init__(self, limit: int):
        self.limit = limit
        self.received = 0

    def account(self, size: int) -> None:
        if size < 0 or self.received + size > self.limit:
            raise RequestBodyTooLarge
        self.received += size


def content_length_exceeds_limit(value: bytes | str | None, limit: int) -> bool:
    if value is None:
        return False
    try:
        size = int(value)
    except (TypeError, ValueError):
        return False
    return size < 0 or size > limit


def host_is_local(host_header: bytes | str | None) -> bool:
    if not host_header:
        return False
    host = host_header.decode("latin-1") if isinstance(host_header, bytes) else host_header
    host = host.strip().lower()
    if host.startswith("["):
        closing = host.find("]")
        if closing < 0:
            return False
        hostname, suffix = host[1:closing], host[closing + 1:]
        return hostname in ALLOWED_HOSTS and (not suffix or (suffix.startswith(":") and suffix[1:].isdigit()))
    if host.count(":") > 1:
        return False
    hostname, separator, port = host.partition(":")
    return hostname in ALLOWED_HOSTS and (not separator or port.isdigit())


def origin_is_same_local(origin_header: bytes | str | None, host_header: bytes | str | None) -> bool:
    """Accept only HTTP origins matching this local host and port.

    `localhost` and loopback IP aliases are considered compatible when they use
    the same port. Missing Origin is handled by the caller for non-browser clients.
    """
    if not origin_header or not host_header:
        return False
    origin = origin_header.decode("latin-1") if isinstance(origin_header, bytes) else origin_header
    host = host_header.decode("latin-1") if isinstance(host_header, bytes) else host_header
    try:
        parsed_origin = urlsplit(origin)
        parsed_host = urlsplit("http://" + host)
        origin_name, host_name = parsed_origin.hostname, parsed_host.hostname
        origin_port = parsed_origin.port or 80
        host_port = parsed_host.port or 80
    except ValueError:
        return False
    if (
        parsed_origin.scheme != "http" or parsed_origin.path or parsed_origin.query
        or parsed_origin.fragment or parsed_origin.username or parsed_origin.password
        or origin_name not in ALLOWED_HOSTS or host_name not in ALLOWED_HOSTS
    ):
        return False
    return origin_port == host_port


def supported_suffix(filename: str) -> str | None:
    """Return an accepted normalized suffix without using the name as a path."""
    suffix = filename.rpartition(".")[2]
    if not suffix or filename.endswith("."):
        return None
    normalized = "." + suffix.lower()
    return normalized if normalized in SUPPORTED else None


DOWNLOAD_STEM_LIMIT = 120
_SEPARATORS = re.compile(r"[/\\]")
# Anything that could end the quoted value of a header, split a header line, or
# be read as a path component. Non-ASCII is deliberately kept: a Chinese
# document name is the point, and the header carries it percent-encoded.
_UNSAFE_STEM = re.compile(r"[\x00-\x1f\x7f\"\'`;:*?<>|%]+")


def safe_output_stem(filename: str, fallback: str = "document") -> str:
    """Derive a download name from an upload name without trusting it.

    The uploaded name is controlled by whoever made the file, so only its last
    path segment is considered and its final suffix dropped, without ever
    treating the name as a path. A name that sanitizes away to nothing falls
    back, so every download still gets a usable name.
    """
    segment = _SEPARATORS.split(filename or "")[-1]
    stem = segment.rpartition(".")[0] if "." in segment else segment
    stem = _UNSAFE_STEM.sub("-", stem).strip(". -")
    return stem[:DOWNLOAD_STEM_LIMIT].strip(". -") or fallback


def content_disposition(stem: str, target: str, fallback: str = "converted-document") -> str:
    """An attachment header that carries a non-ASCII name correctly (RFC 6266).

    ``filename`` is read by a client that understands nothing else, so it holds
    the name only when that name is ASCII throughout. A name with any character
    outside ASCII uses the fallback there instead, because dropping those
    characters leaves a fragment rather than a name - "車燈規格表_v3" would read
    "_v3". ``filename*`` always carries the real name, percent-encoded as UTF-8.
    """
    ascii_stem = stem if stem.isascii() else fallback
    encoded = quote(f"{stem}.{target}", safe="")
    return f'attachment; filename="{ascii_stem}.{target}"; filename*=UTF-8\'\'{encoded}'


def valid_target(target: str) -> bool:
    return target in ALLOWED_TARGETS


def valid_file_count(count: int) -> bool:
    return 1 <= count <= MAX_FILE_COUNT


def request_exceeds_limit(size: int, limit: int) -> bool:
    return size > limit
