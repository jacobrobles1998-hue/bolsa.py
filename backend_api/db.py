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

CREATE TABLE IF NOT EXISTS conversaciones (
    conv_id TEXT PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    profesional_id INTEGER NOT NULL,
    last_at TEXT NOT NULL,
    last_read_cli_at TEXT,
    last_read_pro_at TEXT
);

CREATE TABLE IF NOT EXISTS sesiones (
    token TEXT PRIMARY KEY,
    rol TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conv_id_created ON mensajes(conv_id, created_at);
CREATE INDEX IF NOT EXISTS idx_convs_cliente ON conversaciones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_convs_profesional ON conversaciones(profesional_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_expires ON sesiones(expires_at);
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
        await db.execute(
            """
            INSERT OR IGNORE INTO conversaciones (conv_id, cliente_id, profesional_id, last_at)
            VALUES (?, ?, ?, ?)
            """,
            (conv_id, int(cliente_id), int(profesional_id), str(created_at)),
        )
        await db.execute(
            """
            UPDATE conversaciones
            SET last_at = ?
            WHERE conv_id = ?
            """,
            (str(created_at), conv_id),
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
                m.conv_id AS conv_id,
                m.cliente_id AS cliente_id,
                COALESCE(c.nombre, 'Cliente') AS nombre,
                MAX(m.created_at) AS last_at,
                (
                    SELECT m2.texto
                    FROM mensajes m2
                    WHERE m2.conv_id = m.conv_id
                    ORDER BY m2.created_at DESC
                    LIMIT 1
                ) AS last_texto,
                SUM(
                    CASE
                        WHEN m.sender_rol = 'cliente'
                         AND m.created_at > COALESCE(v.last_read_pro_at, '')
                        THEN 1
                        ELSE 0
                    END
                ) AS unread
            FROM mensajes m
            LEFT JOIN clientes c ON c.id = m.cliente_id
            LEFT JOIN conversaciones v ON v.conv_id = m.conv_id
            WHERE m.profesional_id = ?
            GROUP BY m.conv_id
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(profesional_id), limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def mark_read(*, cliente_id: int, profesional_id: int, rol: str, at: str):
    conv_id = _conv_id(cliente_id, profesional_id)
    rol = (rol or "").strip().lower()
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO conversaciones (conv_id, cliente_id, profesional_id, last_at)
            VALUES (?, ?, ?, ?)
            """,
            (conv_id, int(cliente_id), int(profesional_id), str(at)),
        )
        if rol == "cliente":
            await db.execute(
                """
                UPDATE conversaciones
                SET last_read_cli_at = ?
                WHERE conv_id = ?
                """,
                (str(at), conv_id),
            )
        elif rol == "profesional":
            await db.execute(
                """
                UPDATE conversaciones
                SET last_read_pro_at = ?
                WHERE conv_id = ?
                """,
                (str(at), conv_id),
            )
        await db.commit()


async def unread_total(*, rol: str, user_id: int) -> int:
    rol = (rol or "").strip().lower()
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        if rol == "cliente":
            q = """
            SELECT COALESCE(SUM(
                CASE
                    WHEN m.sender_rol = 'profesional'
                     AND m.created_at > COALESCE(v.last_read_cli_at, '')
                    THEN 1
                    ELSE 0
                END
            ), 0) AS unread
            FROM mensajes m
            LEFT JOIN conversaciones v ON v.conv_id = m.conv_id
            WHERE m.cliente_id = ?
            """
            async with db.execute(q, (int(user_id),)) as cur:
                row = await cur.fetchone()
                return int(row[0] or 0)

        if rol == "profesional":
            q = """
            SELECT COALESCE(SUM(
                CASE
                    WHEN m.sender_rol = 'cliente'
                     AND m.created_at > COALESCE(v.last_read_pro_at, '')
                    THEN 1
                    ELSE 0
                END
            ), 0) AS unread
            FROM mensajes m
            LEFT JOIN conversaciones v ON v.conv_id = m.conv_id
            WHERE m.profesional_id = ?
            """
            async with db.execute(q, (int(user_id),)) as cur:
                row = await cur.fetchone()
                return int(row[0] or 0)

    return 0


async def inbox_cliente(*, cliente_id: int, limit: int = 30):
    limit = max(1, min(int(limit or 30), 200))
    async with aiosqlite.connect(DB_PATH.as_posix()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT
                m.conv_id AS conv_id,
                m.profesional_id AS profesional_id,
                COALESCE(p.nombre, 'Profesional') AS nombre,
                MAX(m.created_at) AS last_at,
                (
                    SELECT m2.texto
                    FROM mensajes m2
                    WHERE m2.conv_id = m.conv_id
                    ORDER BY m2.created_at DESC
                    LIMIT 1
                ) AS last_texto,
                SUM(
                    CASE
                        WHEN m.sender_rol = 'profesional'
                         AND m.created_at > COALESCE(v.last_read_cli_at, '')
                        THEN 1
                        ELSE 0
                    END
                ) AS unread
            FROM mensajes m
            LEFT JOIN profesionales p ON p.id = m.profesional_id
            LEFT JOIN conversaciones v ON v.conv_id = m.conv_id
            WHERE m.cliente_id = ?
            GROUP BY m.conv_id, m.profesional_id
            ORDER BY last_at DESC
            LIMIT ?
            """,
            (int(cliente_id), limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]