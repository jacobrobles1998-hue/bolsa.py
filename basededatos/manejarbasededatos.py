import sqlite3
from pathlib import Path
import hashlib
import hmac
import os
from datetime import datetime
import secrets
from datetime import timedelta


DB_PATH = Path(__file__).resolve().parent / "bolsa_data.db"

def conectar_db():
    """Crea la conexión con el archivo de base de datos"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    password = password or ""
    salt = os.urandom(16)
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"

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
            certificacion TEXT,
            experiencia INTEGER,
            tarifa REAL,
            metodologia TEXT,
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
            ("certificacion", "TEXT"),
            ("experiencia", "INTEGER"),
            ("tarifa", "REAL"),
            ("metodologia", "TEXT"),
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

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profesionales_especialidad ON profesionales(especialidad)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profesionales_departamento ON profesionales(departamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contratos_profesional ON contratos(id_profesional)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contratos_cliente ON contratos(id_cliente)')
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_profesionales_email ON profesionales(email) WHERE email IS NOT NULL")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clientes_email ON clientes(email) WHERE email IS NOT NULL")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_expires ON sesiones(expires_at)")
    
    conn.commit()
    conn.close()

def crear_profesional(datos: dict) -> int:
    conn = conectar_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO profesionales
        (nombre, email, telefono, password_hash, foto, foto_mime, departamento, ciudad, genero, edad, altura, peso, especialidad, certificacion, experiencia, tarifa, metodologia, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datos.get("nombre"),
            (datos.get("email") or "").strip().lower(),
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
            datos.get("certificacion"),
            datos.get("experiencia"),
            datos.get("tarifa"),
            datos.get("metodologia"),
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
            (datos.get("email") or "").strip().lower(),
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
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profesionales WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and verify_password(password, row["password_hash"]):
        conn.close()
        return {"rol": "profesional", "id": int(row["id"]), "nombre": row["nombre"], "email": row["email"]}

    cursor.execute("SELECT * FROM clientes WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return {"rol": "cliente", "id": int(row["id"]), "nombre": row["nombre"], "email": row["email"]}
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

def obtener_cliente_por_id(cliente_id: int):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (int(cliente_id),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def guardar_foto_profesional(profesional_id: int, foto_bytes: bytes, foto_mime: str | None = None):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE profesionales SET foto = ?, foto_mime = ? WHERE id = ?",
        (foto_bytes, foto_mime, int(profesional_id)),
    )
    conn.commit()
    conn.close()

def guardar_foto_cliente(cliente_id: int, foto_bytes: bytes, foto_mime: str | None = None):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clientes SET foto = ?, foto_mime = ? WHERE id = ?",
        (foto_bytes, foto_mime, int(cliente_id)),
    )
    conn.commit()
    conn.close()

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

def buscar_profesionales(departamento: str | None = None, especialidad: str | None = None, presupuesto_max: float | None = None):
    where = []
    params = []
    if departamento and departamento != "Todos":
        where.append("departamento = ?")
        params.append(departamento)
    if especialidad and especialidad != "Todos":
        where.append("especialidad = ?")
        params.append(especialidad)
    if presupuesto_max is not None:
        where.append("(tarifa IS NULL OR tarifa <= ?)")
        params.append(float(presupuesto_max))
    sql = "SELECT * FROM profesionales"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC"
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

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
