import aiosqlite
from .settings import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conv_id TEXT NOT NULL,
    cliente_id INTEGER NOT NULL,
    profesional_id INTEGER NOT NULL,
    sender_rol TEXT NOT NULL,
    sender_id INTEGER NOT NULL,
    texto TEXT NOT NULL,
    # aqui comienza las notificaciones
    created_at TEXT NOT NULL,
    read_by_cliente_at TEXT,
    read_by_profesional_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conv_id_created ON mensajes(conv_id, created_at);
"""

def _conv_id(cliente_id: int, profesional_id: int) -> str:
    return f"c{int(cliente_id)}_p{int(profesional_id)}"
# aqui comienza los codigos de las notificaciones de mensajes
async def _ensure_column(db: aiosqlite.Connection, table: str, column: str, definition: str):
    async with db.execute(f"PRAGMA table_info({table})") as cur:
        rows = await cur.fetchall()
    existing = {r[1] for r in rows}
    if column in existing:
        return
    await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

async def init_db():
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        await db.executescript(_SCHEMA)
        # parte del codigo de notificaciones
        await _ensure_column(db, "mensajes", "read_by_cliente_at", "TEXT")
        await _ensure_column(db, "mensajes", "read_by_profesional_at", "TEXT")
        await db.commit()

async def get_session(token: str):
    token = (token or "").strip()
    if not token:
        return None
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sesiones WHERE token = ? LIMIT 1", (token,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def insert_message(*, cliente_id: int, profesional_id: int, sender_rol: str, sender_id: int, texto: str, created_at: str):
    conv_id = _conv_id(cliente_id, profesional_id)
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        await db.execute(
            """
            INSERT INTO mensajes (conv_id, cliente_id, profesional_id, sender_rol, sender_id, texto, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (conv_id, int(cliente_id), int(profesional_id), str(sender_rol), int(sender_id), str(texto), str(created_at)),
        )
        await db.commit()

async def list_messages(*, cliente_id: int, profesional_id: int, limit: int = 50):
    conv_id = _conv_id(cliente_id, profesional_id)
    limit = max(1, min(int(limit or 50), 200))
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, conv_id, cliente_id, profesional_id, sender_rol, sender_id, texto, created_at, read_by_cliente_at, read_by_profesional_at
            FROM mensajes
            WHERE conv_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (conv_id, limit),
        ) as cur:
            rows = await cur.fetchall()
            out = [dict(r) for r in rows]
            out.reverse()
            return out

# parte del codigo de notificaciones
async def mark_conversation_read(*, cliente_id: int, profesional_id: int, reader_rol: str, read_at: str):
    conv_id = _conv_id(cliente_id, profesional_id)
    rol = (reader_rol or "").strip().lower()
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        if rol == "cliente":
            await db.execute(
                """
                UPDATE mensajes
                SET read_by_cliente_at = ?
                WHERE conv_id = ?
                  AND sender_rol = 'profesional'
                  AND (read_by_cliente_at IS NULL OR read_by_cliente_at = '')
                """,
                (str(read_at), conv_id),
            )
        elif rol == "profesional":
            await db.execute(
                """
                UPDATE mensajes
                SET read_by_profesional_at = ?
                WHERE conv_id = ?
                  AND sender_rol = 'cliente'
                  AND (read_by_profesional_at IS NULL OR read_by_profesional_at = '')
                """,
                (str(read_at), conv_id),
            )
        await db.commit()


async def inbox_profesional(*, profesional_id: int, limit: int = 30):
    limit = max(1, min(int(limit or 30), 200))
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                m.cliente_id AS cliente_id,
                COALESCE(c.nombre, 'Cliente') AS nombre,
                MAX(m.created_at) AS last_at,
                (
                    SELECT m2.texto
                    FROM mensajes m2
                    WHERE m2.cliente_id = m.cliente_id AND m2.profesional_id = m.profesional_id
                    ORDER BY m2.created_at DESC
                    LIMIT 1
                    # codigo de notificaciones
                ) AS last_texto,
                (
                    SELECT COUNT(1)
                    FROM mensajes mu
                    WHERE mu.cliente_id = m.cliente_id
                      AND mu.profesional_id = m.profesional_id
                      AND mu.sender_rol = 'cliente'
                      AND (mu.read_by_profesional_at IS NULL OR mu.read_by_profesional_at = '')
                ) AS unread_count
            FROM mensajes m
            LEFT JOIN clientes c ON c.id = m.cliente_id
            WHERE m.profesional_id = ?
            GROUP BY m.cliente_id
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(profesional_id), limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def inbox_cliente(*, cliente_id: int, limit: int = 30):
    limit = max(1, min(int(limit or 30), 200))
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                m.profesional_id AS profesional_id,
                COALESCE(p.nombre, 'Profesional') AS nombre,
                MAX(m.created_at) AS last_at,
                (
                    SELECT m2.texto
                    FROM mensajes m2
                    WHERE m2.cliente_id = m.cliente_id AND m2.profesional_id = m.profesional_id
                    ORDER BY m2.created_at DESC
                    LIMIT 1
                    # codigo de notificaciones
                ) AS last_texto,
                (
                    SELECT COUNT(1)
                    FROM mensajes mu
                    WHERE mu.cliente_id = m.cliente_id
                      AND mu.profesional_id = m.profesional_id
                      AND mu.sender_rol = 'profesional'
                      AND (mu.read_by_cliente_at IS NULL OR mu.read_by_cliente_at = '')
                ) AS unread_count
            FROM mensajes m
            LEFT JOIN profesionales p ON p.id = m.profesional_id
            WHERE m.cliente_id = ?
            GROUP BY m.profesional_id
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(cliente_id), limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]