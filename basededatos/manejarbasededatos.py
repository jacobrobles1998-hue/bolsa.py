import sqlite3
from pathlib import Path
import hashlib
import hmac
import os
import time
from datetime import datetime
import secrets
from datetime import timedelta
import base64
import unicodedata
from difflib import SequenceMatcher

from basededatos.modelos import (
    CERTIFICACION_PROFESIONAL_COLUMNS,
    CLIENT_COLUMNS,
    CONTRATO_COLUMNS,
    PROFESIONAL_COLUMNS,
    SESION_COLUMNS,
)

DB_PATH = Path(__file__).resolve().parent / "bolsa_data.db"
_SCHEMA_ENSURED = False
_ENSURING_SCHEMA = False


def _asegurar_schema(conn: sqlite3.Connection):
    global _SCHEMA_ENSURED, _ENSURING_SCHEMA
    if _SCHEMA_ENSURED or _ENSURING_SCHEMA:
        return
    _ENSURING_SCHEMA = True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name IN ('clientes', 'profesionales', 'sesiones')
            """
        )
        existentes = {r[0] for r in cursor.fetchall()}
        if {"clientes", "profesionales", "sesiones"}.issubset(existentes):
            _SCHEMA_ENSURED = True
            return

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profesionales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telefono TEXT,
                password_hash TEXT NOT NULL,
                foto BLOB,
                foto_mime TEXT,
                departamento TEXT,
                ciudad TEXT,
                genero TEXT,
                edad INTEGER,
                altura REAL,
                peso REAL,
                especialidad TEXT,
                universidad TEXT,
                certificacion TEXT,
                experiencia INTEGER,
                tarifa REAL,
                metodologia TEXT,
                url_tiktok TEXT,
                url_instagram TEXT,
                url_facebook TEXT,
                url_youtube TEXT,
                estado_verificacion TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telefono TEXT,
                password_hash TEXT NOT NULL,
                foto BLOB,
                foto_mime TEXT,
                departamento TEXT,
                ciudad TEXT,
                genero TEXT,
                edad INTEGER,
                altura REAL,
                peso REAL,
                patologia_familiar TEXT,
                metodologia TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_profesional INTEGER NOT NULL,
                id_cliente INTEGER NOT NULL,
                monto REAL,
                fecha TEXT,
                estado TEXT NOT NULL DEFAULT 'activo',
                FOREIGN KEY(id_profesional) REFERENCES profesionales(id),
                FOREIGN KEY(id_cliente) REFERENCES clientes(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sesiones (
                token TEXT PRIMARY KEY,
                rol TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS certificaciones_profesional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_profesional INTEGER NOT NULL,
                titulo TEXT,
                archivo BLOB,
                archivo_mime TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(id_profesional) REFERENCES profesionales(id) ON DELETE CASCADE
            )
            """
        )

        _ensure_columns(cursor, "profesionales", PROFESIONAL_COLUMNS)
        _ensure_columns(cursor, "clientes", CLIENT_COLUMNS)
        _ensure_columns(cursor, "contratos", CONTRATO_COLUMNS)
        _ensure_columns(cursor, "certificaciones_profesional", CERTIFICACION_PROFESIONAL_COLUMNS)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profesionales_especialidad ON profesionales(especialidad)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profesionales_departamento ON profesionales(departamento)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_profesional ON contratos(id_profesional)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_cliente ON contratos(id_cliente)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_certificaciones_profesional_prof ON certificaciones_profesional(id_profesional)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_profesionales_email ON profesionales(email) WHERE email IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_email ON clientes(email) WHERE email IS NOT NULL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_expires ON sesiones(expires_at)")

        conn.commit()
        _SCHEMA_ENSURED = True
    finally:
        _ENSURING_SCHEMA = False

def conectar_db():
    """Crea la conexión con el archivo de base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _asegurar_schema(conn)
    return conn

_ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "image/webp"}
_MAX_PHOTO_BYTES = 3 * 1024 * 1024
_MAX_CERT_BYTES = 6 * 1024 * 1024

_LOGIN_WINDOW_S = 60.0
_LOGIN_MAX_FAILS = 8
_login_fails: dict[str, list[float]] = {}


def _sniff_image_mime(data: bytes) -> str | None:
    if not data:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _validate_image_blob(raw: bytes, mime: str | None, *, max_bytes: int) -> tuple[bytes, str]:
    if not raw:
        raise ValueError("Archivo vacío")
    if len(raw) > int(max_bytes):
        raise ValueError("Archivo demasiado grande")

    declared = (mime or "").strip().lower()
    sniffed = _sniff_image_mime(raw)
    final_mime = sniffed or declared

    if not final_mime or final_mime not in _ALLOWED_IMAGE_MIME:
        raise ValueError("Formato de imagen no permitido")

    if sniffed and declared and sniffed != declared:
        raise ValueError("Tipo de archivo no coincide con el contenido")

    return raw, final_mime


def _check_login_rate_limit(email: str):
    now = time.monotonic()
    key = (email or "").strip().lower()
    if not key:
        return

    arr = _login_fails.get(key)
    if arr is None:
        arr = []
        _login_fails[key] = arr

    cutoff = now - _LOGIN_WINDOW_S
    i = 0
    while i < len(arr) and arr[i] < cutoff:
        i += 1
    if i:
        del arr[:i]

    if len(arr) >= _LOGIN_MAX_FAILS:
        raise RuntimeError("Demasiados intentos. Espera 1 minuto y vuelve a intentar.")


def _note_login_fail(email: str):
    key = (email or "").strip().lower()
    if not key:
        return
    now = time.monotonic()
    arr = _login_fails.get(key)
    if arr is None:
        arr = []
        _login_fails[key] = arr
    arr.append(now)


def _clear_login_fails(email: str):
    key = (email or "").strip().lower()
    if not key:
        return
    _login_fails.pop(key, None)


def hash_password(password: str) -> str:
    password = password or ""
    salt = os.urandom(16)
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"

def asegurar_profesional_demo() -> int:
    conn = conectar_db()
    cursor = conn.cursor()
    demo_tel = "3000000000"
    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute("SELECT id FROM profesionales WHERE telefono = ? LIMIT 1", (demo_tel,))
    row = cursor.fetchone()
    if row:
        prof_id = int(row["id"])
        cursor.execute(
            """
            UPDATE profesionales
            SET nombre = ?,
                telefono = ?,
                departamento = ?,
                ciudad = ?,
                genero = ?,
                edad = ?,
                altura = ?,
                peso = ?,
                especialidad = ?,
                universidad = ?,
                experiencia = ?,
                tarifa = ?,
                metodologia = ?,
                estado_verificacion = ?
            WHERE id = ?
            """,
            (
                "Andres Torres",
                demo_tel,
                "Bogotá D.C.",
                "Bogota",
                "Masculino",
                29,
                1.78,
                80.0,
                "Entrenador Personal",
                "Servicio Nacional de Aprendizaje (SENA)",
                5,
                70000.0,
                "Hipertrofia, fuerza y recomposición corporal con programación progresiva y seguimiento semanal.",
                "verificado",
                prof_id,
            ),
        )
        cursor.execute("SELECT 1 FROM certificaciones_profesional WHERE id_profesional = ? LIMIT 1", (prof_id,))
        if cursor.fetchone() is None:
            png_1x1 = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+tmxQAAAAASUVORK5CYII="
            )
            cursor.execute(
                """
                INSERT INTO certificaciones_profesional (id_profesional, titulo, archivo, archivo_mime, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (prof_id, "Certificado demo", png_1x1, "image/png", now),
            )
        conn.commit()
        conn.close()
        return prof_id

    cursor.execute(
        """
        INSERT INTO profesionales
        (nombre, email, telefono, password_hash, foto, foto_mime, departamento, ciudad, genero, edad, altura, peso, especialidad, universidad, certificacion, experiencia, tarifa, metodologia, estado_verificacion, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Andres Torres",
            f"demo_{secrets.token_hex(6)}@axon.local",
            demo_tel,
            hash_password("12345678"),
            None,
            None,
            "Bogotá D.C.",
            "Bogota",
            "Masculino",
            29,
            1.78,
            80.0,
            "Entrenador Personal",
            "Servicio Nacional de Aprendizaje (SENA)",
            None,
            5,
            70000.0,
            "Hipertrofia, fuerza y recomposición corporal con programación progresiva y seguimiento semanal.",
            "verificado",
            now,
        ),
    )
    prof_id = int(cursor.lastrowid)
    png_1x1 = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+tmxQAAAAASUVORK5CYII="
    )
    cursor.execute(
        """
        INSERT INTO certificaciones_profesional (id_profesional, titulo, archivo, archivo_mime, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (prof_id, "Certificado demo", png_1x1, "image/png", now),
    )
    conn.commit()
    conn.close()
    return prof_id

def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    try:
        algo, iterations_str, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except Exception:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations)
    return hmac.compare_digest(dk, expected)

def _ensure_columns(cursor: sqlite3.Cursor, table: str, columns: list[tuple[str, str]]):
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {r["name"] for r in cursor.fetchall()}
    for name, definition in columns:
        if name not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def crear_tablas_iniciales():
    """Crea las carpetas internas de la base de datos si no existen"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profesionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefono TEXT,
            password_hash TEXT NOT NULL,
            foto BLOB,
            foto_mime TEXT,
            departamento TEXT,
            ciudad TEXT,
            genero TEXT,
            edad INTEGER,
            altura REAL,
            peso REAL,
            especialidad TEXT,
            universidad TEXT,
            certificacion TEXT,
            experiencia INTEGER,
            tarifa REAL,
            metodologia TEXT,
            url_tiktok TEXT,
            url_instagram TEXT,
            url_facebook TEXT,
            url_youtube TEXT,
            estado_verificacion TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefono TEXT,
            password_hash TEXT NOT NULL,
            foto BLOB,
            foto_mime TEXT,
            departamento TEXT,
            ciudad TEXT,
            genero TEXT,
            edad INTEGER,
            altura REAL,
            peso REAL,
            patologia_familiar TEXT,
            metodologia TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_profesional INTEGER NOT NULL,
            id_cliente INTEGER NOT NULL,
            monto REAL,
            fecha TEXT,
            estado TEXT NOT NULL DEFAULT 'activo',
            FOREIGN KEY(id_profesional) REFERENCES profesionales(id),
            FOREIGN KEY(id_cliente) REFERENCES clientes(id)
        )
    ''')

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sesiones (
            token TEXT PRIMARY KEY,
            rol TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS certificaciones_profesional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_profesional INTEGER NOT NULL,
            titulo TEXT,
            archivo BLOB,
            archivo_mime TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(id_profesional) REFERENCES profesionales(id) ON DELETE CASCADE
        )
        """
    )

    _ensure_columns(
        cursor,
        "profesionales",
        [
            ("nombre", "TEXT"),
            ("email", "TEXT"),
            ("telefono", "TEXT"),
            ("password_hash", "TEXT"),
            ("foto", "BLOB"),
            ("foto_mime", "TEXT"),
            ("departamento", "TEXT"),
            ("ciudad", "TEXT"),
            ("genero", "TEXT"),
            ("edad", "INTEGER"),
            ("altura", "REAL"),
            ("peso", "REAL"),
            ("especialidad", "TEXT"),
            ("universidad", "TEXT"),
            ("certificacion", "TEXT"),
            ("experiencia", "INTEGER"),
            ("tarifa", "REAL"),
            ("metodologia", "TEXT"),
            ("url_tiktok", "TEXT"),
            ("url_instagram", "TEXT"),
            ("url_facebook", "TEXT"),
            ("url_youtube", "TEXT"),
            ("estado_verificacion", "TEXT"),
            ("created_at", "TEXT"),
        ],
    )
    _ensure_columns(
        cursor,
        "clientes",
        [
            ("nombre", "TEXT"),
            ("email", "TEXT"),
            ("telefono", "TEXT"),
            ("password_hash", "TEXT"),
            ("foto", "BLOB"),
            ("foto_mime", "TEXT"),
            ("departamento", "TEXT"),
            ("ciudad", "TEXT"),
            ("genero", "TEXT"),
            ("edad", "INTEGER"),
            ("altura", "REAL"),
            ("peso", "REAL"),
            ("patologia_familiar", "TEXT"),
            ("metodologia", "TEXT"),
            ("created_at", "TEXT"),
        ],
    )
    _ensure_columns(
        cursor,
        "contratos",
        [
            ("id_profesional", "INTEGER"),
            ("id_cliente", "INTEGER"),
            ("monto", "REAL"),
            ("fecha", "TEXT"),
            ("estado", "TEXT NOT NULL DEFAULT 'activo'"),
        ],
    )
    _ensure_columns(
        cursor,
        "certificaciones_profesional",
        [
            ("id_profesional", "INTEGER"),
            ("titulo", "TEXT"),
            ("archivo", "BLOB"),
            ("archivo_mime", "TEXT"),
            ("created_at", "TEXT"),
        ],
    )

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profesionales_especialidad ON profesionales(especialidad)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profesionales_departamento ON profesionales(departamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contratos_profesional ON contratos(id_profesional)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contratos_cliente ON contratos(id_cliente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_certificaciones_profesional_prof ON certificaciones_profesional(id_profesional)')
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_profesionales_email ON profesionales(email) WHERE email IS NOT NULL")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_email ON clientes(email) WHERE email IS NOT NULL")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_expires ON sesiones(expires_at)")
    
    conn.commit()
    conn.close()

    try:
        anonimizar_correos_existentes()
    except Exception:
        pass

def anonimizar_correos_existentes():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE profesionales
        SET email = 'prof_' || id || '@axon.local'
        WHERE email IS NOT NULL AND email NOT LIKE 'prof_%@axon.local'
        """
    )
    cursor.execute(
        """
        UPDATE clientes
        SET email = 'cli_' || id || '@axon.local'
        WHERE email IS NOT NULL AND email NOT LIKE 'cli_%@axon.local'
        """
    )
    conn.commit()
    conn.close()

def crear_profesional(datos: dict) -> int:
    conn = conectar_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO profesionales
        (nombre, email, telefono, password_hash, foto, foto_mime, departamento, ciudad, genero, edad, altura, peso, especialidad, universidad, certificacion, experiencia, tarifa, metodologia, estado_verificacion, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("nombre"),
            (datos.get("email") or "").strip().lower() or f"prof_{secrets.token_hex(8)}@axon.local",
            datos.get("telefono"),
            hash_password(datos.get("password") or ""),
            None,
            None,
            datos.get("departamento"),
            datos.get("ciudad"),
            datos.get("genero"),
            datos.get("edad"),
            datos.get("altura"),
            datos.get("peso"),
            datos.get("especialidad"),
            datos.get("universidad"),
            datos.get("certificacion"),
            datos.get("experiencia"),
            datos.get("tarifa"),
            datos.get("metodologia"),
            datos.get("estado_verificacion") or "pendiente",
            now,
        ),
    )
    profesional_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return profesional_id

def crear_cliente(datos: dict) -> int:
    conn = conectar_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO clientes
        (nombre, email, telefono, password_hash, foto, foto_mime, departamento, ciudad, genero, edad, altura, peso, patologia_familiar, metodologia, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("nombre"),
            (datos.get("email") or "").strip().lower() or f"cli_{secrets.token_hex(8)}@axon.local",
            datos.get("telefono"),
            hash_password(datos.get("password") or ""),
            None,
            None,
            datos.get("departamento"),
            datos.get("ciudad"),
            datos.get("genero"),
            datos.get("edad"),
            datos.get("altura"),
            datos.get("peso"),
            datos.get("patologia_familiar"),
            datos.get("metodologia"),
            now,
        ),
    )
    cliente_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return cliente_id

def autenticar_usuario(email: str, password: str):
    email = (email or "").strip().lower()
    if not email or not password:
        return None

    _check_login_rate_limit(email)

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profesionales WHERE lower(email) = ?", (email,))
    row = cursor.fetchone()
    if row and verify_password(password, row["password_hash"]):
        try:
            estado_verificacion = row["estado_verificacion"]
        except Exception:
            estado_verificacion = None
        conn.close()
        _clear_login_fails(email)
        return {
            "rol": "profesional",
            "id": int(row["id"]),
            "nombre": row["nombre"],
            "estado_verificacion": estado_verificacion,
        }

    cursor.execute("SELECT * FROM clientes WHERE lower(email) = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        _clear_login_fails(email)
        return {"rol": "cliente", "id": int(row["id"]), "nombre": row["nombre"]}

    _note_login_fail(email)
    return None

def crear_sesion(rol: str, user_id: int, dias: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires = now + timedelta(days=int(dias))
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sesiones (token, rol, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            token,
            rol,
            int(user_id),
            now.isoformat(timespec="seconds"),
            expires.isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()
    return token

def obtener_sesion(token: str):
    token = (token or "").strip()
    if not token:
        return None
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sesiones WHERE token = ?", (token,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except Exception:
        expires_at = None
    if expires_at and expires_at < datetime.utcnow():
        cursor.execute("DELETE FROM sesiones WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None
    conn.close()
    return {"token": row["token"], "rol": row["rol"], "user_id": int(row["user_id"])}

def eliminar_sesion(token: str):
    token = (token or "").strip()
    if not token:
        return
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sesiones WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def obtener_profesional_por_id(profesional_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profesionales WHERE id = ?", (int(profesional_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_profesional(profesional_id: int, cambios: dict) -> bool:
    if not cambios:
        return False

    allowed = {
        "nombre",
        "telefono",
        "departamento",
        "ciudad",
        "correo",
        "genero",
        "especialidad",
        "universidad",
        "experiencia",
        "tarifa",
        "tarifa_unidad",
        "metodologia",
        "url_tiktok",
        "url_instagram",
        "url_facebook",
        "url_youtube",
    }

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(profesionales)")
    cols = {r[1] for r in cursor.fetchall()}

    update_items = []
    params = []
    for k, v in (cambios or {}).items():
        if k not in allowed:
            continue
        if k not in cols:
            continue
        update_items.append(f"{k} = ?")
        params.append(v)

    if not update_items:
        conn.close()
        return False

    params.append(int(profesional_id))
    cursor.execute(
        f"UPDATE profesionales SET {', '.join(update_items)} WHERE id = ?",
        tuple(params),
    )
    conn.commit()
    conn.close()
    return True


def actualizar_cliente(cliente_id: int, cambios: dict) -> bool:
    if not cambios:
        return False

    allowed = {
        "nombre",
        "telefono",
        "departamento",
        "ciudad",
        "genero",
        "edad",
        "altura",
        "peso",
        "patologia_familiar",
        "metodologia",
    }

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(clientes)")
    cols = {r[1] for r in cursor.fetchall()}

    update_items = []
    params = []
    for k, v in (cambios or {}).items():
        if k not in allowed:
            continue
        if k not in cols:
            continue
        update_items.append(f"{k} = ?")
        params.append(v)

    if not update_items:
        conn.close()
        return False

    params.append(int(cliente_id))
    cursor.execute(
        f"UPDATE clientes SET {', '.join(update_items)} WHERE id = ?",
        tuple(params),
    )
    conn.commit()
    conn.close()
    return True


def obtener_cliente_por_id(cliente_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (int(cliente_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def guardar_foto_profesional(profesional_id: int, foto_bytes: bytes, foto_mime: str | None = None):
    foto_bytes, foto_mime = _validate_image_blob(bytes(foto_bytes or b""), foto_mime, max_bytes=_MAX_PHOTO_BYTES)
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE profesionales SET foto = ?, foto_mime = ? WHERE id = ?",
        (foto_bytes, foto_mime, int(profesional_id)),
    )
    conn.commit()
    conn.close()

def guardar_foto_cliente(cliente_id: int, foto_bytes: bytes, foto_mime: str | None = None):
    foto_bytes, foto_mime = _validate_image_blob(bytes(foto_bytes or b""), foto_mime, max_bytes=_MAX_PHOTO_BYTES)
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clientes SET foto = ?, foto_mime = ? WHERE id = ?",
        (foto_bytes, foto_mime, int(cliente_id)),
    )
    conn.commit()
    conn.close()

def agregar_certificacion_profesional(profesional_id: int, titulo: str | None = None, archivo_bytes: bytes | None = None, archivo_mime: str | None = None) -> int:
    if not archivo_bytes:
        raise ValueError("El archivo del certificado es obligatorio")
    archivo_bytes, archivo_mime = _validate_image_blob(bytes(archivo_bytes or b""), archivo_mime, max_bytes=_MAX_CERT_BYTES)

    conn = conectar_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO certificaciones_profesional (id_profesional, titulo, archivo, archivo_mime, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (int(profesional_id), (titulo or "").strip() or None, archivo_bytes, archivo_mime, now),
    )
    cert_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return cert_id

def listar_certificaciones_profesional(profesional_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, id_profesional, titulo, archivo, archivo_mime, created_at
        FROM certificaciones_profesional
        WHERE id_profesional = ?
        ORDER BY created_at DESC, id DESC
        """,
        (int(profesional_id),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def eliminar_profesional(profesional_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contratos WHERE id_profesional = ?", (int(profesional_id),))
    cursor.execute("DELETE FROM profesionales WHERE id = ?", (int(profesional_id),))
    conn.commit()
    conn.close()

def eliminar_cliente(cliente_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contratos WHERE id_cliente = ?", (int(cliente_id),))
    cursor.execute("DELETE FROM clientes WHERE id = ?", (int(cliente_id),))
    conn.commit()
    conn.close()

def eliminar_usuario_por_email(email: str):
    email = (email or "").strip().lower()
    if not email:
        return False
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profesionales WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        profesional_id = int(row["id"])
        cursor.execute("DELETE FROM contratos WHERE id_profesional = ?", (profesional_id,))
        cursor.execute("DELETE FROM profesionales WHERE id = ?", (profesional_id,))
        conn.commit()
        conn.close()
        return True

    cursor.execute("SELECT id FROM clientes WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        cliente_id = int(row["id"])
        cursor.execute("DELETE FROM contratos WHERE id_cliente = ?", (cliente_id,))
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False

def buscar_profesionales(departamento: str | None = None, especialidad: str | None = None, presupuesto_max: float | None = None, texto: str | None = None, solo_verificados: bool = True):
    def _norm(s: str) -> str:
        s = (s or "").strip().lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        return " ".join(s.split())

    where_base = []
    params_base = []
    if solo_verificados:
        where_base.append("lower(COALESCE(estado_verificacion, 'pendiente')) = 'verificado'")
    if departamento and departamento != "Todos":
        where_base.append("departamento = ?")
        params_base.append(departamento)
    if especialidad and especialidad != "Todos":
        where_base.append("especialidad = ?")
        params_base.append(especialidad)
    if presupuesto_max is not None:
        where_base.append("(tarifa IS NULL OR tarifa <= ?)")
        params_base.append(float(presupuesto_max))

    where = list(where_base)
    params = list(params_base)
    texto = (texto or "").strip()
    if texto:
        tokens = [t.strip().lower() for t in texto.split() if len(t.strip()) >= 3][:6]
        for t in tokens:
            where.append(
                "("
                "lower(nombre) LIKE ? OR "
                "lower(especialidad) LIKE ? OR "
                "lower(metodologia) LIKE ? OR "
                "lower(certificacion) LIKE ?"
                ")"
            )
            like = f"%{t}%"
            params.extend([like, like, like, like])
    sql = "SELECT * FROM profesionales"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    resultados = [dict(r) for r in rows]
    if resultados or not texto:
        return resultados

    sql_base = "SELECT * FROM profesionales"
    if where_base:
        sql_base += " WHERE " + " AND ".join(where_base)
    sql_base += " ORDER BY created_at DESC"
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(sql_base, tuple(params_base))
    candidatos = [dict(r) for r in cursor.fetchall()]
    conn.close()

    q = _norm(texto)
    if not q:
        return []
    scores = []
    for r in candidatos:
        hay = " ".join(
            [
                _norm(r.get("nombre")),
                _norm(r.get("especialidad")),
                _norm(r.get("metodologia")),
                _norm(r.get("certificacion")),
                _norm(r.get("departamento")),
                _norm(r.get("ciudad")),
            ]
        ).strip()
        if not hay:
            continue
        score = SequenceMatcher(None, q, hay).ratio()
        scores.append((score, r))
    scores.sort(key=lambda x: x[0], reverse=True)
    filtrados = [r for s, r in scores if s >= 0.35][:30]
    return filtrados

def crear_contrato(id_cliente: int, id_profesional: int, monto: float | None = None):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM contratos
        WHERE id_cliente = ? AND id_profesional = ? AND estado = 'activo'
        """,
        (int(id_cliente), int(id_profesional)),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return int(existing["id"])

    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO contratos (id_profesional, id_cliente, monto, fecha, estado)
        VALUES (?, ?, ?, ?, 'activo')
        """,
        (int(id_profesional), int(id_cliente), monto, now),
    )
    contrato_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()
    return contrato_id

def listar_clientes_de_profesional(id_profesional: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.*, ct.id AS contrato_id, ct.monto, ct.fecha, ct.estado
        FROM contratos ct
        JOIN clientes c ON c.id = ct.id_cliente
        WHERE ct.id_profesional = ? AND ct.estado = 'activo'
        ORDER BY ct.fecha DESC
        """,
        (int(id_profesional),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_profesionales_de_cliente(id_cliente: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, ct.id AS contrato_id, ct.monto, ct.fecha, ct.estado
        FROM contratos ct
        JOIN profesionales p ON p.id = ct.id_profesional
        WHERE ct.id_cliente = ? AND ct.estado = 'activo'
        ORDER BY ct.fecha DESC
        """,
        (int(id_cliente),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_profesionales_de_cliente(id_cliente: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.*, ct.id AS contrato_id, ct.monto, ct.fecha, ct.estado
        FROM contratos ct
        JOIN profesionales p ON p.id = ct.id_profesional
        WHERE ct.id_cliente = ? AND ct.estado = 'activo'
        ORDER BY ct.fecha DESC
        """,
        (int(id_cliente),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_todos_los_profesionales(*, solo_verificados: bool = True):
    """Profesionales visibles en el directorio de Inicio."""
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        if solo_verificados:
            cursor.execute(
                """
                SELECT id, nombre, especialidad, departamento, ciudad, tarifa, metodologia, experiencia,
                       telefono, foto, foto_mime, estado_verificacion
                FROM profesionales
                WHERE lower(COALESCE(estado_verificacion, 'pendiente')) = 'verificado'
                ORDER BY created_at DESC
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, nombre, especialidad, departamento, ciudad, tarifa, metodologia, experiencia,
                       telefono, foto, foto_mime, estado_verificacion
                FROM profesionales
                ORDER BY created_at DESC
                """
            )
        return [dict(r) for r in cursor.fetchall()]
    except Exception as e:
        print(f"Error en obtener_todos_los_profesionales: {e}")
        return []
    finally:
        conn.close()

DEPARTAMENTOS_COLOMBIA = {
    "Atlántico": [
        "Barranquilla", "Soledad", "Puerto Colombia", "Malambo", 
        "Sabanalarga", "Baranoa", "Galapa"
    ],
    "Antioquia": [
        "Medellín", "Envigado", "Bello", "Itagüí", "Rionegro", 
        "Sabaneta", "Apartadó", "Turbo", "Caucasia"
    ],
    "Bogotá D.C.": [
        "Bogotá"
    ],
    "Valle del Cauca": [
        "Cali", "Palmira", "Tuluá", "Buenaventura", "Buga", 
        "Cartago", "Jamundí", "Yumbo"
    ],
    "Santander": [
        "Bucaramanga", "Floridablanca", "Girón", "Piedecuesta", 
        "Barrancabermeja", "San Gil"
    ],
    "Bolívar": [
        "Cartagena", "Turbaco", "Magangué", "Arjona", "Carmen de Bolívar"
    ],
    "Magdalena": [
        "Santa Marta", "Ciénaga", "Fundación", "El Banco"
    ],
    "Cundinamarca": [
        "Soacha", "Chía", "Zipaquirá", "Facatativá", "Fusagasugá", 
        "Mosquera", "Madrid", "Funza", "Girardot"
    ],
    "Norte de Santander": [
        "Cúcuta", "Ocaña", "Villa del Rosario", "Los Patios", "Pamplona"
    ],
    "Risaralda": [
        "Pereira", "Dosquebradas", "Santa Rosa de Cabal"
    ],
    "Caldas": [
        "Manizales", "La Dorada", "Riosucio", "Chinchiná"
    ],
    "Quindío": [
        "Armenia", "Calarcá", "Tebaida", "Montenegro"
    ],
    "Córdoba": [
        "Montería", "Cereté", "Lorica", "Sahagún", "Montelíbano"
    ],
    "Cesar": [
        "Valledupar", "Aguachica", "Agustín Codazzi", "Bosconia"
    ]
} 
