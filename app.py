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
from autenticacion.registro import formulario_registro
from autenticacion.ingresos import mostrar_interfaz_login
from perfiles.profesional import perfil_profesional_view    
from perfiles.cliente import perfil_cliente_view
from nucleo.citas import mostrar_busqueda
from nucleo.agendamiento import gestionar_agenda
from finanzas.pagos import procesar_pago
from basededatos.manejarbasededatos import crear_tablas_iniciales
from estilo.estilocss import css__styles #importas la variable ue acabas de crear
from config import Config

st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) # inyectas el css en la app


# 3. CONFIGURACIÓN DE LA INTERFAZ (Tu menú de navegación)
st.title("Red de Profesionales AXON")
st.caption("Conectamos entrenadores, nutricionistas y fisioterapeutas con personas que buscan resultados reales.")

# Creamos un menú en la barra lateral para movernos por la app
opcion_principal = st.sidebar.selectbox(
    "¿Qué quieres hacer?",
    ["Iniciar Sesión", "Registrarse"]
)

# 4. LÓGICA DE CONTROL: Mostramos una pantalla según lo que elija el usuario
if opcion_principal == "Iniciar Sesión":
    mostrar_interfaz_login()  # Llamamos a la función de tu archivo ingreso.py
# caso 2: EL USUARIO SE VA A REGISTRAR 
elif opcion_principal == "Registrarse":
    st.subheader("unete a nuestra comunidad")

# aui aparece la segunda barra condicional
tipo_usuario = st.selectbox(
    "¿Qué tipo de usuario eres?",
    ["Profesional", "Cliente"]
)
# dependiendo de lo ue elija la persona se mostrara un formulario diferente
if tipo_usuario == "Profesional":
    st.subheader("Ofrezco mis servicio")
    formulario_registro()
    # Llamamos a la función de tu archivo registro.py (con tarifas, experiencia,etc)
elif tipo_usuario == "Cliente":
    st.subheader("Busco un servicio")
    formulario_registro()
    # Llamamos a la función de tu archivo registro.py (con tarifas, experiencia,etc)
else:
    st.error("Por favor, selecciona un tipo de usuario.")    # Llamamos a la función de tu archivo registro.py (sin tarifas, experiencia,etc)



    



    
