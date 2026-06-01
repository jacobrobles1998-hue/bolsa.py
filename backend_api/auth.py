from datetime import datetime, timezone

from .db import get_session


def _is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return True
    try:
        dt = datetime.fromisoformat(expires_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt < datetime.now(timezone.utc)
    except Exception:
        return True


async def validate_token(token: str):
    ses = await get_session(token)
    if not ses:
        return None
    if _is_expired(ses.get("expires_at")):
        return None
    rol = (ses.get("rol") or "").strip().lower()
    user_id = ses.get("user_id")
    if rol not in {"cliente", "profesional"}:
        return None
    try:
        user_id = int(user_id)
    except Exception:
        return None
    return {"rol": rol, "user_id": user_id, "token": ses.get("token")}