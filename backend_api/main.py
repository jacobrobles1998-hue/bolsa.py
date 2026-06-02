from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import socketio

from .settings import CORS_ORIGINS
from .auth import validate_token
# notificaciones
from .db import init_db, inbox_cliente, inbox_profesional, insert_message, list_messages, mark_conversation_read
from .schemas import JoinConversationIn, SendMessageIn

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=CORS_ORIGINS)
api = FastAPI(title="Axon Backend API", version="0.1.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.on_event("startup")
async def _startup():
    await init_db()


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


async def _auth_from_headers_or_query(authorization: str | None, token_q: str | None):
    token = token_q or _bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    user = await validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid/expired token")
    return user


@api.get("/health")
async def health():
    return {"ok": True}


@api.get("/inbox")
async def get_inbox(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    limit: int = Query(default=30),
):
    user = await _auth_from_headers_or_query(authorization, token)
    if user["rol"] == "profesional":
        items = await inbox_profesional(profesional_id=int(user["user_id"]), limit=int(limit))
        return {"rol": "profesional", "items": items}
    items = await inbox_cliente(cliente_id=int(user["user_id"]), limit=int(limit))
    return {"rol": "cliente", "items": items}


@api.get("/messages")
async def get_messages(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    cliente_id: int | None = Query(default=None),
    profesional_id: int | None = Query(default=None),
    limit: int = Query(default=50),
):
    user = await _auth_from_headers_or_query(authorization, token)

    if user["rol"] == "cliente":
        if profesional_id is None:
            raise HTTPException(status_code=400, detail="Missing profesional_id")
        cliente_id = user["user_id"]
    else:
        if cliente_id is None:
            raise HTTPException(status_code=400, detail="Missing cliente_id")
        profesional_id = user["user_id"]

    msgs = await list_messages(
        cliente_id=int(cliente_id),
        profesional_id=int(profesional_id),
        limit=int(limit),
    )
#codigo de notificaciones

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await mark_conversation_read(
        cliente_id=int(cliente_id),
        profesional_id=int(profesional_id),
        reader_rol=str(user["rol"]),
        read_at=now,
    )

    return {
        "cliente_id": int(cliente_id),
        "profesional_id": int(profesional_id),
        "items": msgs,
    }


@api.post("/messages")
async def post_message(
    body: SendMessageIn,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    texto = (body.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Empty texto")

    if user["rol"] == "cliente":
        if body.profesional_id is None:
            raise HTTPException(status_code=400, detail="Missing profesional_id")
        cliente_id = user["user_id"]
        profesional_id = int(body.profesional_id)
    else:
        if body.cliente_id is None:
            raise HTTPException(status_code=400, detail="Missing cliente_id")
        profesional_id = user["user_id"]
        cliente_id = int(body.cliente_id)

    await insert_message(
        cliente_id=int(cliente_id),
        profesional_id=int(profesional_id),
        sender_rol=user["rol"],
        sender_id=int(user["user_id"]),
        texto=texto,
        created_at=now,
    )

    payload = {
        "cliente_id": int(cliente_id),
        "profesional_id": int(profesional_id),
        "sender_rol": user["rol"],
        "sender_id": int(user["user_id"]),
        "texto": texto,
        "created_at": now,
    }
    room = f"c{int(cliente_id)}_p{int(profesional_id)}"
    await sio.emit("message", payload, room=room)
    return {"ok": True, "message": payload}


@sio.event
async def connect(sid, environ, auth):
    token = None
    if isinstance(auth, dict):
        token = auth.get("token")
    if not token:
        qs = (environ or {}).get("QUERY_STRING") or ""
        for part in qs.split("&"):
            if part.startswith("token="):
                token = part.split("=", 1)[1]
                break
    user = await validate_token(token or "")
    if not user:
        return False
    await sio.save_session(sid, user)


@sio.event
async def join_conversation(sid, data):
    user = await sio.get_session(sid)
    if not user:
        return

    payload = JoinConversationIn.model_validate(data or {})
    cid = int(payload.cliente_id)
    pid = int(payload.profesional_id)

    if user["rol"] == "cliente" and user["user_id"] != cid:
        return
    if user["rol"] == "profesional" and user["user_id"] != pid:
        return

    room = f"c{cid}_p{pid}"
    await sio.enter_room(sid, room)

    items = await list_messages(cliente_id=cid, profesional_id=pid, limit=int(payload.limit or 50))
    # codigo de notificaciones
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await mark_conversation_read(
        cliente_id=int(cid),
        profesional_id=int(pid),
        reader_rol=str(user["rol"]),
        read_at=now,
    )
    await sio.emit("history", {"cliente_id": cid, "profesional_id": pid, "items": items}, room=sid)


@sio.event
async def send_message(sid, data):
    user = await sio.get_session(sid)
    if not user:
        return

    body = SendMessageIn.model_validate(data or {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    texto = (body.texto or "").strip()
    if not texto:
        return

    if user["rol"] == "cliente":
        if body.profesional_id is None:
            return
        cliente_id = int(user["user_id"])
        profesional_id = int(body.profesional_id)
    else:
        if body.cliente_id is None:
            return
        profesional_id = int(user["user_id"])
        cliente_id = int(body.cliente_id)

    await insert_message(
        cliente_id=cliente_id,
        profesional_id=profesional_id,
        sender_rol=user["rol"],
        sender_id=int(user["user_id"]),
        texto=texto,
        created_at=now,
    )

    msg = {
        "cliente_id": cliente_id,
        "profesional_id": profesional_id,
        "sender_rol": user["rol"],
        "sender_id": int(user["user_id"]),
        "texto": texto,
        "created_at": now,
    }
    room = f"c{cliente_id}_p{profesional_id}"
    await sio.emit("message", msg, room=room)


app = socketio.ASGIApp(sio, other_asgi_app=api)