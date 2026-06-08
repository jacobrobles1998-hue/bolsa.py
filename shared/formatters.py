from datetime import datetime


def format_cop(value) -> str:
    try:
        return f"${float(value):,.0f} COP"
    except Exception:
        return str(value)


def format_cop_input(value) -> str:
    try:
        return f"{int(float(value)):,.0f}".replace(",", ".")
    except Exception:
        return str(value or "")


def format_datetime_short(value) -> str:
    if not value:
        return ""
    s = str(value).replace("T", " ")
    return s[:16] if len(s) >= 16 else s


def format_date_only(value) -> str:
    if not value:
        return ""
    s = str(value).replace("T", " ")
    return s[:10]


def shorten_text(value: str | None, max_len: int = 56) -> str:
    text = (value or "").strip().replace("\n", " ")
    if len(text) <= int(max_len):
        return text
    return text[: max_len - 1].rstrip() + "…"


def initials(nombre: str | None) -> str:
    parts = [p for p in (nombre or "").strip().split() if p]
    return ("".join([p[0] for p in parts[:2]]) or "?").upper()


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


__all__ = [
    "format_cop",
    "format_cop_input",
    "format_datetime_short",
    "format_date_only",
    "shorten_text",
    "initials",
    "parse_iso_datetime",
]