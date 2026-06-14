from datetime import datetime, timezone
import base64
import time

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import socketio

from .settings import CORS_ORIGINS
from .auth import validate_token
from .db import (
    inbox_cliente,
    inbox_profesional,
    init_db,
    insert_message,
    list_messages,
    mark_read,
    unread_total,
)
from .schemas import (
    AuthLoginIn,
    AuthRegisterClienteIn,
    AuthRegisterProfesionalIn,
    CertCreateIn,
    ContratoCreateIn,
    FotoUpdateIn,
    JoinConversationIn,
    ProfileUpdateIn,
    SendMessageIn,
)

from basededatos.manejarbasededatos import (
    actualizar_cliente,
    actualizar_profesional,
    agregar_certificacion_profesional,
    autenticar_usuario,
    buscar_profesionales,
    crear_cliente,
    crear_contrato,
    crear_profesional,
    crear_sesion,
    crear_tablas_iniciales,
    eliminar_sesion,
    guardar_foto_cliente,
    guardar_foto_profesional,
    listar_certificaciones_profesional,
    listar_clientes_de_profesional,
    listar_profesionales_de_cliente,
    obtener_cliente_por_id,
    obtener_profesional_por_id,
    obtener_todos_los_profesionales,
)

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
    crear_tablas_iniciales()


MAX_HISTORY_LIMIT = 200
_MAX_MSG_LEN = 2000
_RATE_LIMIT_WINDOW_S = 8.0
_RATE_LIMIT_MAX = 18

_rl: dict[tuple[str, int, str], list[float]] = {}


def _sanitize_text(s: str) -> str:
    s = (s or "").strip()
    s = "".join(ch for ch in s if ch >= " " or ch in "\n\t")
    return s


def _check_rate_limit(*, rol: str, user_id: int, action: str):
    now = time.monotonic()
    key = (str(rol), int(user_id), str(action))
    arr = _rl.get(key)
    if arr is None:
        arr = []
        _rl[key] = arr
    cutoff = now - _RATE_LIMIT_WINDOW_S
    i = 0
    while i < len(arr) and arr[i] < cutoff:
        i += 1
    if i:
        del arr[:i]
    if len(arr) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many requests")
    arr.append(now)


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


def _b64(data: bytes | bytearray | None) -> str | None:
    if not data:
        return None
    return base64.b64encode(bytes(data)).decode("ascii")


def _strip_sensitive_user_fields(row: dict) -> dict:
    if not isinstance(row, dict):
        return {}
    out = dict(row)
    out.pop("password_hash", None)
    return out


def _serialize_user(row: dict, *, include_foto: bool) -> dict:
    out = _strip_sensitive_user_fields(row)
    if include_foto:
        out["foto_b64"] = _b64(out.pop("foto", None))
    else:
        out.pop("foto", None)
    return out


def _serialize_cert(row: dict, *, include_archivo: bool) -> dict:
    if not isinstance(row, dict):
        return {}
    out = dict(row)
    if include_archivo:
        out["archivo_b64"] = _b64(out.pop("archivo", None))
    else:
        out.pop("archivo", None)
    return out


def _serialize_contrato_join_row(row: dict, *, include_foto: bool) -> dict:
    out = _strip_sensitive_user_fields(row)
    if include_foto:
        out["foto_b64"] = _b64(out.pop("foto", None))
    else:
        out.pop("foto", None)
    return out


@api.get("/health")
async def health():
    return {"ok": True}


@api.post("/auth/login")
async def auth_login(body: AuthLoginIn):
    email = (body.email or "").strip().lower()
    password = body.password or ""

    try:
        res = autenticar_usuario(email, password)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))

    if not res:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    rol = str(res["rol"])
    user_id = int(res["id"])

    token = crear_sesion(rol, user_id)

    if rol == "cliente":
        row = obtener_cliente_por_id(user_id) or {}
        prof_en_verificacion = False
    else:
        row = obtener_profesional_por_id(user_id) or {}
        estado = (row or {}).get("estado_verificacion")
        prof_en_verificacion = (estado or "pendiente").strip().lower() != "verificado"

    profile = _serialize_user(row, include_foto=True)
    return {
        "ok": True,
        "token": str(token),
        "rol": rol,
        "user_id": user_id,
        "profile": profile,
        "prof_en_verificacion": bool(prof_en_verificacion),
    }


@api.post("/auth/logout")
async def auth_logout(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    try:
        eliminar_sesion(str(user.get("token") or token or ""))
    except Exception:
        pass
    return {"ok": True}


@api.post("/auth/register_profesional")
async def auth_register_profesional(body: AuthRegisterProfesionalIn):
    data = body.model_dump()
    data["email"] = (data.get("email") or "").strip().lower()
    data["estado_verificacion"] = "pendiente"

    try:
        profesional_id = int(crear_profesional(data))
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg and "email" in msg:
            raise HTTPException(status_code=400, detail="Ese correo ya ya está registrado como profesional")
        raise HTTPException(status_code=400, detail="No se pudo crear el profesional")

    token = crear_sesion("profesional", profesional_id)
    row = obtener_profesional_por_id(profesional_id) or {}
    profile = _serialize_user(row, include_foto=True)

    estado = (row or {}).get("estado_verificacion")
    prof_en_verificacion = (estado or "pendiente").strip().lower() != "verificado"

    return {
        "ok": True,
        "token": str(token),
        "rol": "profesional",
        "user_id": int(profesional_id),
        "profile": profile,
        "prof_en_verificacion": bool(prof_en_verificacion),
    }


@api.post("/auth/register_cliente")
async def auth_register_cliente(body: AuthRegisterClienteIn):
    data = body.model_dump()
    data["email"] = (data.get("email") or "").strip().lower()

    try:
        cliente_id = int(crear_cliente(data))
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg and "email" in msg:
            raise HTTPException(status_code=400, detail="Ese correo ya está registrado como cliente")
        raise HTTPException(status_code=400, detail="No se pudo crear el cliente")

    token = crear_sesion("cliente", cliente_id)
    row = obtener_cliente_por_id(cliente_id) or {}
    profile = _serialize_user(row, include_foto=True)

    return {
        "ok": True,
        "token": str(token),
        "rol": "cliente",
        "user_id": int(cliente_id),
        "profile": profile,
        "prof_en_verificacion": False,
    }


@api.post("/me/foto")
async def me_set_foto(
    body: FotoUpdateIn,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    raw = base64.b64decode(body.foto_b64.encode("ascii"))
    mime = (body.foto_mime or "").strip().lower() or None

    if user["rol"] == "cliente":
        guardar_foto_cliente(int(user["user_id"]), raw, mime)
    else:
        guardar_foto_profesional(int(user["user_id"]), raw, mime)

    return {"ok": True}


@api.post("/me/certificaciones")
async def me_add_certificacion(
    body: CertCreateIn,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    if user["rol"] != "profesional":
        raise HTTPException(status_code=403, detail="Forbidden")

    raw = base64.b64decode(body.archivo_b64.encode("ascii"))
    mime = (body.archivo_mime or "").strip().lower() or None
    titulo = (body.titulo or "").strip() or None

    try:
        cert_id = int(agregar_certificacion_profesional(int(user["user_id"]), titulo, raw, mime))
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo guardar el certificado")

    return {"ok": True, "id": cert_id}


@api.post("/me/profile")
async def me_update_profile(
    body: ProfileUpdateIn,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    cambios = body.cambios if isinstance(body.cambios, dict) else {}

    if user["rol"] == "cliente":
        ok = bool(actualizar_cliente(int(user["user_id"]), dict(cambios)))
    else:
        ok = bool(actualizar_profesional(int(user["user_id"]), dict(cambios)))

    if not ok:
        return {"ok": False}

    if user["rol"] == "cliente":
        row = obtener_cliente_por_id(int(user["user_id"])) or {}
    else:
        row = obtener_profesional_por_id(int(user["user_id"])) or {}

    return {"ok": True, "profile": _serialize_user(row, include_foto=True)}


@api.post("/contratos")
async def post_contrato(
    body: ContratoCreateIn,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    if user["rol"] != "cliente":
        raise HTTPException(status_code=403, detail="Forbidden")

    pid = int(body.profesional_id)
    if pid <= 0:
        raise HTTPException(status_code=400, detail="Invalid profesional_id")

    try:
        cid = int(crear_contrato(int(user["user_id"]), pid, body.monto))
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo crear el contrato")

    return {"ok": True, "id": int(cid)}


@api.get("/me")
async def get_me(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    rol = str(user["rol"])
    user_id = int(user["user_id"])

    if rol == "cliente":
        row = obtener_cliente_por_id(user_id) or {}
    else:
        row = obtener_profesional_por_id(user_id) or {}

    out = _serialize_user(row, include_foto=True)
    return {"rol": rol, "user_id": user_id, "profile": out}


@api.get("/profesionales")
async def get_profesionales(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    departamento: str | None = Query(default=None),
    especialidad: str | None = Query(default=None),
    presupuesto_max: float | None = Query(default=None),
    texto: str | None = Query(default=None),
    solo_verificados: bool = Query(default=True),
    include_foto: bool = Query(default=False),
):
    await _auth_from_headers_or_query(authorization, token)

    if any([departamento, especialidad, presupuesto_max is not None, texto]):
        items = buscar_profesionales(
            departamento=departamento,
            especialidad=especialidad,
            presupuesto_max=presupuesto_max,
            texto=texto,
            solo_verificados=bool(solo_verificados),
        )
    else:
        items = obtener_todos_los_profesionales(solo_verificados=bool(solo_verificados))

    out = [_serialize_user(dict(r), include_foto=bool(include_foto)) for r in (items or [])]
    return {"items": out}


@api.get("/profesionales/{profesional_id}")
async def get_profesional_by_id(
    profesional_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    include_foto: bool = Query(default=False),
):
    await _auth_from_headers_or_query(authorization, token)

    row = obtener_profesional_por_id(int(profesional_id))
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return {"item": _serialize_user(dict(row), include_foto=bool(include_foto))}


@api.get("/clientes/{cliente_id}")
async def get_cliente_by_id(
    cliente_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    include_foto: bool = Query(default=False),
):
    user = await _auth_from_headers_or_query(authorization, token)

    rol = str(user["rol"])
    user_id = int(user["user_id"])

    if rol == "cliente" and int(cliente_id) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    row = obtener_cliente_por_id(int(cliente_id))
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    item = dict(row)
    if rol == "profesional":
        allowed = {"id", "nombre", "foto", "foto_mime"}
        item = {k: item.get(k) for k in allowed}

    return {"item": _serialize_user(item, include_foto=bool(include_foto))}


@api.get("/contratos")
async def get_contratos(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    include_foto: bool = Query(default=False),
):
    user = await _auth_from_headers_or_query(authorization, token)

    rol = str(user["rol"])
    user_id = int(user["user_id"])

    if rol == "profesional":
        items = listar_clientes_de_profesional(int(user_id))
    else:
        items = listar_profesionales_de_cliente(int(user_id))

    out = [_serialize_contrato_join_row(dict(r), include_foto=bool(include_foto)) for r in (items or [])]
    return {"rol": rol, "user_id": user_id, "items": out}


@api.get("/profesionales/{profesional_id}/certificaciones")
async def get_certificaciones_profesional(
    profesional_id: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    include_archivo: bool = Query(default=False),
):
    await _auth_from_headers_or_query(authorization, token)

    items = listar_certificaciones_profesional(int(profesional_id))
    out = [_serialize_cert(dict(r), include_archivo=bool(include_archivo)) for r in (items or [])]
    return {"profesional_id": int(profesional_id), "items": out}


@api.get("/inbox")
async def get_inbox(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
    limit: int = Query(default=30),
    include_foto: bool = Query(default=False),
):
    user = await _auth_from_headers_or_query(authorization, token)

    include = bool(include_foto)
    if user["rol"] == "profesional":
        items = await inbox_profesional(
            profesional_id=int(user["user_id"]),
            limit=int(limit),
            include_foto=include,
        )
        out = []
        for it in items or []:
            row = dict(it)
            if include:
                row["foto_b64"] = _b64(row.pop("foto", None))
            else:
                row.pop("foto", None)
                row.pop("foto_mime", None)
            out.append(row)
        return {"rol": "profesional", "items": out}

    items = await inbox_cliente(
        cliente_id=int(user["user_id"]),
        limit=int(limit),
        include_foto=include,
    )
    out = []
    for it in items or []:
        row = dict(it)
        if include:
            row["foto_b64"] = _b64(row.pop("foto", None))
        else:
            row.pop("foto", None)
            row.pop("foto_mime", None)
        out.append(row)
    return {"rol": "cliente", "items": out}


@api.get("/unread_count")
async def get_unread_count(
    authorization: str | None = Header(default=None, alias="Authorization"),
    token: str | None = Query(default=None),
):
    user = await _auth_from_headers_or_query(authorization, token)
    total = await unread_total(rol=str(user["rol"]), user_id=int(user["user_id"]))
    return {"rol": str(user["rol"]), "user_id": int(user["user_id"]), "unread": int(total)}


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

    lim = int(limit)
    if lim <= 0:
        lim = 50
    lim = min(lim, MAX_HISTORY_LIMIT)

    msgs = await list_messages(
        cliente_id=int(cliente_id),
        profesional_id=int(profesional_id),
        limit=lim,
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
    texto = _sanitize_text(body.texto or "")
    if not texto:
        raise HTTPException(status_code=400, detail="Empty texto")
    if len(texto) > _MAX_MSG_LEN:
        raise HTTPException(status_code=400, detail="Texto too long")

    _check_rate_limit(rol=str(user["rol"]), user_id=int(user["user_id"]), action="post_message")

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
    await sio.emit("inbox_ping", payload, room=f"cliente_{int(cliente_id)}")
    await sio.emit("inbox_ping", payload, room=f"profesional_{int(profesional_id)}")
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

    room = f"{user['rol']}_{int(user['user_id'])}"
    await sio.enter_room(sid, room)


@sio.event
async def join_conversation(sid, data):
    user = await sio.get_session(sid)
    if not user:
        return

    try:
        _check_rate_limit(rol=str(user["rol"]), user_id=int(user["user_id"]), action="join_conversation")
    except HTTPException:
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

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await mark_read(cliente_id=cid, profesional_id=pid, rol=str(user["rol"]), at=now)
    await sio.emit(
        "seen_update",
        {"cliente_id": cid, "profesional_id": pid, "reader_rol": str(user["rol"]), "seen_at": now},
        room=room,
    )

    lim = int(payload.limit or 50)
    if lim <= 0:
        lim = 50
    lim = min(lim, MAX_HISTORY_LIMIT)

    items = await list_messages(cliente_id=cid, profesional_id=pid, limit=lim)
    await sio.emit("history", {"cliente_id": cid, "profesional_id": pid, "items": items}, room=sid)


@sio.event
async def send_message(sid, data):
    user = await sio.get_session(sid)
    if not user:
        return

    body = SendMessageIn.model_validate(data or {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    texto = _sanitize_text(body.texto or "")
    if not texto:
        return
    if len(texto) > _MAX_MSG_LEN:
        return

    try:
        _check_rate_limit(rol=str(user["rol"]), user_id=int(user["user_id"]), action="send_message")
    except HTTPException:
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
        "seen": False,
    }
    room = f"c{cliente_id}_p{profesional_id}"
    await sio.emit("message", msg, room=room)
    await sio.emit("inbox_ping", msg, room=f"cliente_{int(cliente_id)}")
    await sio.emit("inbox_ping", msg, room=f"profesional_{int(profesional_id)}")


@sio.event
async def mark_seen(sid, data):
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

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    await mark_read(cliente_id=cid, profesional_id=pid, rol=str(user["rol"]), at=now)
    await sio.emit(
        "seen_update",
        {"cliente_id": cid, "profesional_id": pid, "reader_rol": str(user["rol"]), "seen_at": now},
        room=f"c{cid}_p{pid}",
    )


app = socketio.ASGIApp(sio, other_asgi_app=api)