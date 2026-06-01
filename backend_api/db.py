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
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conv_id_created ON mensajes(conv_id, created_at);
"""

def _conv_id(cliente_id: int, profesional_id: int) -> str:
    return f"c{int(cliente_id)}_p{int(profesional_id)}"

async def init_db():
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        await db.executescript(_SCHEMA)
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
            SELECT id, conv_id, cliente_id, profesional_id, sender_rol, sender_id, texto, created_at
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
                ) AS last_texto
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
                ) AS last_texto
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