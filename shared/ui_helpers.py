from urllib.parse import urlencode


def first_param_value(value):
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def normalize_query_params(raw: dict | None) -> dict:
    out = {}
    for key, value in (raw or {}).items():
        first = first_param_value(value)
        if first is not None:
            out[key] = str(first)
    return out


def merge_query_params(current: dict | None, updates: dict | None) -> dict:
    params = dict(current or {})
    for key, value in (updates or {}).items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = str(value)
    return params


def build_query_string(params: dict | None) -> str:
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    qs = urlencode(clean)
    return "?" + qs if qs else ""


__all__ = ["normalize_query_params", "merge_query_params", "build_query_string", "first_param_value"]