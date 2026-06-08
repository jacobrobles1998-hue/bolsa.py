import base64

from shared.constants import ALLOWED_IMAGE_MIME, MAX_CERT_BYTES, MAX_IMAGE_BYTES


def sniff_image_mime(data: bytes) -> str | None:
    if not data:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def bytes_to_b64(data: bytes) -> str:
    return base64.b64encode(data or b"").decode("ascii")


def b64_to_bytes(value: str | None) -> bytes | None:
    if not value:
        return None
    try:
        return base64.b64decode(str(value))
    except Exception:
        return None


def validate_upload_bytes(
    raw: bytes,
    declared_mime: str | None = None,
    *,
    max_bytes: int = MAX_IMAGE_BYTES,
    allowed_mimes: set[str] | None = None,
    empty_message: str = "El archivo está vacío.",
    size_message: str = "El archivo es demasiado grande.",
    format_message: str = "Formato de archivo no permitido.",
    mismatch_message: str = "El tipo de archivo no coincide con el contenido.",
) -> tuple[bytes, str]:
    data = bytes(raw or b"")
    if not data:
        raise ValueError(empty_message)
    if len(data) > int(max_bytes):
        raise ValueError(size_message)

    declared = (declared_mime or "").strip().lower()
    sniffed = sniff_image_mime(data)
    final_mime = sniffed or declared
    allowed = allowed_mimes or ALLOWED_IMAGE_MIME

    if not final_mime or final_mime not in allowed:
        raise ValueError(format_message)
    if sniffed and declared and sniffed != declared:
        raise ValueError(mismatch_message)

    return data, final_mime


def validate_image_upload(raw: bytes, declared_mime: str | None = None) -> tuple[bytes, str]:
    return validate_upload_bytes(
        raw,
        declared_mime,
        max_bytes=MAX_IMAGE_BYTES,
        allowed_mimes=ALLOWED_IMAGE_MIME,
        empty_message="La imagen está vacía.",
        size_message="La imagen es demasiado grande. Máximo 3MB.",
        format_message="Formato de imagen no permitido. Usa PNG, JPG/JPEG o WEBP.",
        mismatch_message="El tipo de archivo no coincide con el contenido de la imagen.",
    )


def validate_cert_upload(raw: bytes, declared_mime: str | None = None) -> tuple[bytes, str]:
    return validate_upload_bytes(
        raw,
        declared_mime,
        max_bytes=MAX_CERT_BYTES,
        allowed_mimes=ALLOWED_IMAGE_MIME,
        empty_message="El certificado está vacío.",
        size_message="El certificado es demasiado grande. Máximo 6MB.",
        format_message="Formato de certificado no permitido. Usa PNG, JPG/JPEG o WEBP.",
        mismatch_message="El tipo de archivo no coincide con el contenido del certificado.",
    )


__all__ = [
    "sniff_image_mime",
    "bytes_to_b64",
    "b64_to_bytes",
    "validate_upload_bytes",
    "validate_image_upload",
    "validate_cert_upload",
]