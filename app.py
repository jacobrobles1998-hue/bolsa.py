import os
import sys
import streamlit as st

print("==========================================")
print("DIAGNÓSTICO DE RUTAS:")
print("Tu terminal está ejecutando desde:", os.getcwd())
print("El archivo app.py está físicamente en:", os.path.dirname(os.path.abspath(__file__)))
print("Carpetas reales dentro de este proyecto:", os.listdir(os.path.dirname(os.path.abspath(__file__))))
print("==========================================")

import streamlit as st
st.title("Probando rutas")
# 1. IMPORTACIÓN DE TUS MÓDULOS (Las 6 carpetas)
from autenticacion.registro import formulario_registro_profesional
from autenticacion.ingresos import mostrar_interfaz_login
from autenticacion.registro import formulario_registro_cliente
from perfiles.profesional import perfil_profesional_view    
from perfiles.cliente import perfil_cliente_view
from nucleo.citas import mostrar_busqueda
from nucleo.agendamiento import gestionar_agenda
from finanzas.pagos import procesar_pago
from basededatos.manejarbasededatos import crear_tablas_iniciales
from estilo.estilocss import css__styles #importas la variable ue acabas de crear
from config import Config

st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) # inyectas el css en la app

# ==========================================
# 1. INICIALIZAR EL ESTADO (¡ESTO ES LO QUE FALTA!)
# ==========================================
# Esto le enseña a Python qué es "pantalla" antes de usarla abajo
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "login"

# 3. CONFIGURACIÓN DE LA INTERFAZ (Tu menú de navegación)
st.title("Red de Profesionales AXON")
st.caption("Conectamos entrenadores, nutricionistas y fisioterapeutas con personas que buscan resultados reales.")

# ==========================================
# 3. LÓGICA DE CONTROL (Tu línea 37 ahora sí va a funcionar)
# ==========================================
if st.session_state.pantalla == "login":
    # Llama a tu interfaz de ingresos.py
    mostrar_interfaz_login()
    
    # Botón abajo del login para cambiar a modo registro
    st.markdown("---")
    if st.button("¿No tienes cuenta aún? Regístrate aquí"):
        st.session_state.pantalla = "registro"
        st.rerun()

# ==========================================
# PANTALLA B: REGISTRO (Totalmente aislada)
# ==========================================
elif st.session_state.pantalla == "registro":
    st.subheader("Crea tu cuenta en nuestra comunidad")
    
    tipo_usuario = st.radio("¿Qué tipo de usuario eres?", ["Profesional", "Cliente"])
    
    st.markdown("---")
    
    if tipo_usuario == "Profesional":
        formulario_registro_profesional()
    else:
        formulario_registro_cliente()
        
    st.markdown("---")
    if st.button("← Volver al Inicio de Sesión"):
        st.session_state.pantalla = "login"
        st.rerun()