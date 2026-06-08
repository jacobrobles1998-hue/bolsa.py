import re

from shared.media import validate_cert_upload, validate_image_upload

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE_RE = re.compile(r"^[0-9+\-\s()]{7,20}$")


def is_valid_email(value: str | None) -> bool:
    return bool(_EMAIL_RE.match((value or "").strip().lower()))


def is_valid_phone(value: str | None) -> bool:
    raw = (value or "").strip()
    return (not raw) or bool(_PHONE_RE.match(raw))


def validate_password(value: str | None, *, min_length: int = 8) -> tuple[bool, str | None]:
    pwd = value or ""
    if len(pwd) < int(min_length):
        return False, f"La contraseña debe tener mínimo {int(min_length)} caracteres."
    return True, None


def validate_required_text(value: str | None, field_name: str) -> tuple[bool, str | None]:
    if not (value or "").strip():
        return False, f"{field_name} es obligatorio."
    return True, None


def validate_image_file(uploaded) -> tuple[bytes, str]:
    raw = uploaded.getvalue() if uploaded is not None else b""
    declared = getattr(uploaded, "type", None) if uploaded is not None else None
    return validate_image_upload(raw, declared)


def validate_cert_file(uploaded) -> tuple[bytes, str]:
    raw = uploaded.getvalue() if uploaded is not None else b""
    declared = getattr(uploaded, "type", None) if uploaded is not None else None
    return validate_cert_upload(raw, declared)


__all__ = [
    "is_valid_email",
    "is_valid_phone",
    "validate_password",
    "validate_required_text",
    "validate_image_file",
    "validate_cert_file",
]