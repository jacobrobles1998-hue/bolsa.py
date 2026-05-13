import sqlite3
from config import Config

def conectar_db():
    """Crea la conexión con el archivo de base de datos definido en config.py"""
    conn = sqlite3.connect(Config.DB_PATH)
    return conn

def crear_tablas_iniciales():
    """Crea las carpetas internas de la base de datos si no existen"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabla de Usuarios Profesionales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profesionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            especialidad TEXT,
            ciudad TEXT,
            tarifa REAL
        )
    ''')
    
    # Tabla de Pagos/Contratos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_profesional INTEGER,
            monto REAL,
            fecha TEXT,
            FOREIGN KEY(id_profesional) REFERENCES profesionales(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def guardar_profesional(datos):
    """Guarda un nuevo entrenador en la bolsa de trabajo"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO profesionales (nombre, especialidad, ciudad, tarifa) VALUES (?, ?, ?, ?)",
        (datos['nombre'], datos['especialidad'], datos['ciudad'], datos['tarifa'])
    )
    conn.commit()
    conn.close()