# database/models.py

# Definimos los campos para los profesionales (Entrenadores, Nutris, Fisios)
PROFESIONAL_FIELDS = {
    "id": "INTEGER PRIMARY KEY",
    "nombre": "TEXT NOT NULL",
    "especialidad": "TEXT", # Ej: Hipertrofia, Nutrición Deportiva
    "ciudad": "TEXT",       # Barranquilla, Soledad, etc.
    "tarifa": "REAL",      # Precio por sesión
    "experiencia": "INT",   # Años de trabajo
    "bio": "TEXT"          # Descripción para venderse
}

# Definimos los campos para los Clientes (Atletas)
CLIENT_FIELDS = {
    "id": "INTEGER PRIMARY KEY",
    "nombre": "TEXT NOT NULL",
    "peso_actual": "REAL",  # Ej: 73.70 kg
    "altura": "INT",       # Ej: 171 cm
    "objetivo": "TEXT"     # Ej: Llegar a 80 kg estéticos
}