from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


PROFESIONAL_FIELDS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "nombre": "TEXT NOT NULL",
    "email": "TEXT NOT NULL UNIQUE",
    "telefono": "TEXT",
    "password_hash": "TEXT NOT NULL",
    "foto": "BLOB",
    "foto_mime": "TEXT",
    "departamento": "TEXT",
    "ciudad": "TEXT",
    "genero": "TEXT",
    "edad": "INTEGER",
    "altura": "REAL",
    "peso": "REAL",
    "especialidad": "TEXT",
    "universidad": "TEXT",
    "certificacion": "TEXT",
    "experiencia": "INTEGER",
    "tarifa": "REAL",
    "metodologia": "TEXT",
    "url_tiktok": "TEXT",
    "url_instagram": "TEXT",
    "url_facebook": "TEXT",
    "url_youtube": "TEXT",
    "estado_verificacion": "TEXT",
    "created_at": "TEXT NOT NULL",
}

CLIENT_FIELDS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "nombre": "TEXT NOT NULL",
    "email": "TEXT NOT NULL UNIQUE",
    "telefono": "TEXT",
    "password_hash": "TEXT NOT NULL",
    "foto": "BLOB",
    "foto_mime": "TEXT",
    "departamento": "TEXT",
    "ciudad": "TEXT",
    "genero": "TEXT",
    "edad": "INTEGER",
    "altura": "REAL",
    "peso": "REAL",
    "patologia_familiar": "TEXT",
    "metodologia": "TEXT",
    "created_at": "TEXT NOT NULL",
}

CONTRATO_FIELDS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "id_profesional": "INTEGER NOT NULL",
    "id_cliente": "INTEGER NOT NULL",
    "monto": "REAL",
    "fecha": "TEXT",
    "estado": "TEXT NOT NULL DEFAULT 'activo'",
}

SESION_FIELDS: dict[str, str] = {
    "token": "TEXT PRIMARY KEY",
    "rol": "TEXT NOT NULL",
    "user_id": "INTEGER NOT NULL",
    "created_at": "TEXT NOT NULL",
    "expires_at": "TEXT NOT NULL",
}

CERTIFICACION_PROFESIONAL_FIELDS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "id_profesional": "INTEGER NOT NULL",
    "titulo": "TEXT",
    "archivo": "BLOB",
    "archivo_mime": "TEXT",
    "created_at": "TEXT NOT NULL",
}

MENSAJE_FIELDS: dict[str, str] = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "conv_id": "TEXT NOT NULL",
    "cliente_id": "INTEGER NOT NULL",
    "profesional_id": "INTEGER NOT NULL",
    "sender_rol": "TEXT NOT NULL",
    "sender_id": "INTEGER NOT NULL",
    "texto": "TEXT NOT NULL",
    "created_at": "TEXT NOT NULL",
}

PROFESIONAL_COLUMNS: list[tuple[str, str]] = [(k, v) for k, v in PROFESIONAL_FIELDS.items() if k != "id"]
CLIENT_COLUMNS: list[tuple[str, str]] = [(k, v) for k, v in CLIENT_FIELDS.items() if k != "id"]
CONTRATO_COLUMNS: list[tuple[str, str]] = [(k, v) for k, v in CONTRATO_FIELDS.items() if k != "id"]
SESION_COLUMNS: list[tuple[str, str]] = [(k, v) for k, v in SESION_FIELDS.items() if k != "token"]
CERTIFICACION_PROFESIONAL_COLUMNS: list[tuple[str, str]] = [
    (k, v) for k, v in CERTIFICACION_PROFESIONAL_FIELDS.items() if k != "id"
]
MENSAJE_COLUMNS: list[tuple[str, str]] = [(k, v) for k, v in MENSAJE_FIELDS.items() if k != "id"]


def _mget(m: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return m.get(key, default)


def _int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None

def _float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v)
    return s


@dataclass(frozen=True)
class Profesional:
    id: int | None = None
    nombre: str | None = None
    email: str | None = None
    telefono: str | None = None
    departamento: str | None = None
    ciudad: str | None = None
    genero: str | None = None
    edad: int | None = None
    altura: float | None = None
    peso: float | None = None
    especialidad: str | None = None
    universidad: str | None = None
    certificacion: str | None = None
    experiencia: int | None = None
    tarifa: float | None = None
    metodologia: str | None = None
    url_tiktok: str | None = None
    url_instagram: str | None = None
    url_facebook: str | None = None
    url_youtube: str | None = None
    estado_verificacion: str | None = None
    created_at: str | None = None

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "Profesional":
        return cls(
            id=_int(_mget(m, "id")),
            nombre=_str(_mget(m, "nombre")),
            email=_str(_mget(m, "email")),
            telefono=_str(_mget(m, "telefono")),
            departamento=_str(_mget(m, "departamento")),
            ciudad=_str(_mget(m, "ciudad")),
            genero=_str(_mget(m, "genero")),
            edad=_int(_mget(m, "edad")),
            altura=_float(_mget(m, "altura")),
            peso=_float(_mget(m, "peso")),
            especialidad=_str(_mget(m, "especialidad")),
            universidad=_str(_mget(m, "universidad")),
            certificacion=_str(_mget(m, "certificacion")),
            experiencia=_int(_mget(m, "experiencia")),
            tarifa=_float(_mget(m, "tarifa")),
            metodologia=_str(_mget(m, "metodologia")),
            url_tiktok=_str(_mget(m, "url_tiktok")),
            url_instagram=_str(_mget(m, "url_instagram")),
            url_facebook=_str(_mget(m, "url_facebook")),
            url_youtube=_str(_mget(m, "url_youtube")),
            estado_verificacion=_str(_mget(m, "estado_verificacion")),
            created_at=_str(_mget(m, "created_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Cliente:
    id: int | None = None
    nombre: str | None = None
    email: str | None = None
    telefono: str | None = None
    departamento: str | None = None
    ciudad: str | None = None
    genero: str | None = None
    edad: int | None = None
    altura: float | None = None
    peso: float | None = None
    patologia_familiar: str | None = None
    metodologia: str | None = None
    created_at: str | None = None

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "Cliente":
        return cls(
            id=_int(_mget(m, "id")),
            nombre=_str(_mget(m, "nombre")),
            email=_str(_mget(m, "email")),
            telefono=_str(_mget(m, "telefono")),
            departamento=_str(_mget(m, "departamento")),
            ciudad=_str(_mget(m, "ciudad")),
            genero=_str(_mget(m, "genero")),
            edad=_int(_mget(m, "edad")),
            altura=_float(_mget(m, "altura")),
            peso=_float(_mget(m, "peso")),
            patologia_familiar=_str(_mget(m, "patologia_familiar")),
            metodologia=_str(_mget(m, "metodologia")),
            created_at=_str(_mget(m, "created_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Contrato:
    id: int | None = None
    id_profesional: int | None = None
    id_cliente: int | None = None
    monto: float | None = None
    fecha: str | None = None
    estado: str | None = None

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "Contrato":
        return cls(
            id=_int(_mget(m, "id")),
            id_profesional=_int(_mget(m, "id_profesional")),
            id_cliente=_int(_mget(m, "id_cliente")),
            monto=_float(_mget(m, "monto")),
            fecha=_str(_mget(m, "fecha")),
            estado=_str(_mget(m, "estado")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Sesion:
    token: str | None = None
    rol: str | None = None
    user_id: int | None = None
    created_at: str | None = None
    expires_at: str | None = None

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "Sesion":
        return cls(
            token=_str(_mget(m, "token")),
            rol=_str(_mget(m, "rol")),
            user_id=_int(_mget(m, "user_id")),
            created_at=_str(_mget(m, "created_at")),
            expires_at=_str(_mget(m, "expires_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mensaje:
    id: int | None = None
    conv_id: str | None = None
    cliente_id: int | None = None
    profesional_id: int | None = None
    sender_rol: str | None = None
    sender_id: int | None = None
    texto: str | None = None
    created_at: str | None = None

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "Mensaje":
        return cls(
            id=_int(_mget(m, "id")),
            conv_id=_str(_mget(m, "conv_id")),
            cliente_id=_int(_mget(m, "cliente_id")),
            profesional_id=_int(_mget(m, "profesional_id")),
            sender_rol=_str(_mget(m, "sender_rol")),
            sender_id=_int(_mget(m, "sender_id")),
            texto=_str(_mget(m, "texto")),
            created_at=_str(_mget(m, "created_at")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)