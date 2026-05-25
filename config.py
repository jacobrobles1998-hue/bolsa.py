import os
import streamlit as st

# 1. Configuración de la página (Siempre debe ser lo primero)
st.set_page_config(
    page_title="BOLSA AXON",
    page_icon="🚀",
    layout="wide"
)

# 2. INYECTAR FUENTE POPPINS EN TODA LA APP
st.html(
    """
    <style>
        /* Importamos la fuente Poppins directamente desde Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* Aplicamos la fuente a todos los elementos de la interfaz de Streamlit */
        html, body, [class*="st-"], p, h1, h2, h3, h4, h5, h6, span, button, input, select, textarea {
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Aseguramos que los títulos y textos de los formularios también la hereden */
        .stMarkdown, .stButton, .stSelectbox, .stTextInput, .stTextArea, .stNumberInput {
            font-family: 'Poppins', sans-serif !important;
        }
    </style>
    """,
)
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
