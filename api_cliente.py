import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from shared.constants import BACKEND_API_BASE, REQUEST_TIMEOUT_S


def _build_url(path: str, params: dict | None = None, *, base_url: str | None = None) -> str:
    base = (base_url or BACKEND_API_BASE).strip().rstrip("/")
    url = base + (path or "")
    if params:
        qs = urlencode({k: v for k, v in params.items() if v is not None})
        if qs:
            url += "?" + qs
    return url


def _read_http_error_body(e: HTTPError) -> str:
    try:
        body = e.read().decode("utf-8", errors="ignore")
    except Exception:
        body = ""
    return body or f"HTTP {getattr(e, 'code', 'error')}"


def backend_get_json(
    path: str,
    params: dict | None = None,
    *,
    base_url: str | None = None,
    timeout_s: int = REQUEST_TIMEOUT_S,
) -> dict:
    url = _build_url(path, params, base_url=base_url)
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=int(timeout_s)) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raise RuntimeError(_read_http_error_body(e))
    except URLError as e:
        reason = getattr(e, "reason", None)
        raise RuntimeError(str(reason) if reason else str(e))


def backend_post_json(
    path: str,
    params: dict | None,
    payload: dict,
    *,
    base_url: str | None = None,
    timeout_s: int = REQUEST_TIMEOUT_S,
) -> dict:
    url = _build_url(path, params, base_url=base_url)
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(req, timeout=int(timeout_s)) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        raise RuntimeError(_read_http_error_body(e))
    except URLError as e:
        reason = getattr(e, "reason", None)
        raise RuntimeError(str(reason) if reason else str(e))