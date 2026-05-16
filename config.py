import os

class Config:
    # Nombre de la aplicación
    APP_NAME = "BOLSA: Red de Trabajo y Salud"
    
    # Configuración de Seguridad (No compartas estas claves)
    # En un entorno real, usa variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-para-axon-2026'
    
    # Base de Datos
    # Por ahora usamos SQLite por ser sencilla para empezar
    DB_PATH = 'basededatos/bolsa_data.db'
    
    # Configuración de Negocio
    COMISION_APP = 0.10  # 10% de comisión por cada contrato
    MONEDA = "COP"       # Pesos Colombianos
    
    # Ubicaciones principales (Para tus filtros iniciales)
    ZONAS_COBERTURA = ["Barranquilla", "Soledad", "Puerto Colombia"]