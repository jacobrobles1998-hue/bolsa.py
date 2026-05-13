import sys
import os

# Esto le dice a Python que mire dentro de la carpeta donde está este archivo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
# ... aquí siguen tus otros imports (from auth.registration import ...)

# 1. IMPORTACIÓN DE TUS MÓDULOS (Las 6 carpetas)
from auth.registration import formulario_registro
from auth.login import mostrar_interfaz_login
from perfiles.professional import perfil_profesional_view
from perfiles.client import perfil_cliente_view
from core.matching import mostrar_busqueda
from core.appointments import gestionar_agenda
from finance.payments import procesar_pago
from database.db_handler import crear_tablas_iniciales
from assets.stylecss import css__styles #importas la variable ue acabas de crear
st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) # inyectas el css en la app


# 2. CONFIGURACIÓN INICIAL
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass # Si aún no creas el CSS, la app no se rompe

# Inicializamos la base de datos al abrir la app
crear_tablas_iniciales()
local_css("assets/style.css")

# 3. INTERFAZ DE NAVEGACIÓN
st.sidebar.title(f"🚀 {Config.APP_NAME}")
opcion = st.sidebar.selectbox("Menú Principal", 
    ["Inicio", "Buscar Especialista", "Mi Perfil/Agenda", "Registro", "Pagos"]
)

# 4. LÓGICA DE CONTROL (Aquí es donde llamas a cada carpeta)
if opcion == "Inicio":
    st.header("Bienvenido a la red de profesionales AXON")
    st.write("Conectamos entrenadores, nutricionistas y fisios con personas que buscan resultados reales.")
    st.image("https://via.placeholder.com/800x400?text=Publicidad+AXON") # O una de tu carpeta assets

elif opcion == "Buscar Especialista":
    # Llama a la carpeta 'core'
    mostrar_busqueda()

elif opcion == "Registro":
    # Llama a la carpeta 'auth'
    formulario_registro()

elif opcion == "Mi Perfil/Agenda":
    # Aquí puedes decidir qué mostrar según el tipo de usuario
    col1, col2 = st.columns(2)
    with col1:
        gestionar_agenda() # Carpeta core
    with col2:
        mostrar_interfaz_login() # Carpeta auth

elif opcion == "Pagos":
    # Llama a la carpeta 'finance'
    procesar_pago(50000, "Profesional de Prueba")