import os
import sys
import streamlit as st
import streamlit.components.v1 as components


print("==========================================")
print("DIAGNÓSTICO DE RUTAS:")
print("Tu terminal está ejecutando desde:", os.getcwd())
print("El archivo app.py está físicamente en:", os.path.dirname(os.path.abspath(__file__)))
print("Carpetas reales dentro de este proyecto:", os.listdir(os.path.dirname(os.path.abspath(__file__))))
print("==========================================")

import streamlit as st
#st.title("Probando rutas")
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

def mostrar_login_neumorfico():
    """
      Busca los archivos visuales usando rutas relativas directas 
    e inyecta el diseño neumórfico en la app.
    """
    # Cambiamos las rutas viejas por estas rutas directas simplificadas
    html_path = "estilo/panel.html"
    css_path = "estilo/neumorfico.css"
    
    try:
        # Abrir y leer el archivo CSS de las sombras
        with open(css_path, "r", encoding="utf-8") as f:
            css_codigo = f.read()
            
        # Abrir y leer la estructura HTML de la tarjeta
        with open(html_path, "r", encoding="utf-8") as f:
            html_codigo = f.read()
            
        # Fusionamos ambos códigos
        diseno_final = f"<style>{css_codigo}</style>\n{html_codigo}"
        
        # Renderizamos usando la nueva importación 'components' que agregaste
        components.html(diseno_final, height=850, scrolling=False)
        
    except FileNotFoundError as e:
        # Si algo sale mal, este aviso en rojo te dirá exactamente qué nombre falló
        st.error(f"⚠️ Alerta visual: No se pudo cargar la plantilla. Verifica que existan en la carpeta estilo. Detalles: {e}")
# ==========================================
# 1. INICIALIZAR EL ESTADO (¡ESTO ES LO QUE FALTA!)
# ==========================================
# Esto le enseña a Python qué es "pantalla" antes de usarla abajo
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "login"


# ==========================================
# 3. LÓGICA DE CONTROL (Tu línea 37 ahora sí va a funcionar)
# ==========================================
if st.session_state.pantalla == "login":
    # cambiado: ahora usamos el diseño neumórfico en el login
    mostrar_login_neumorfico()
    
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