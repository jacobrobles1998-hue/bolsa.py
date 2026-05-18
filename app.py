from perfiles import profesional
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
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA

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
# 
if "logeado" not in st.session_state:
    st.session_state.logeado = False

if "rol" not in st.session_state:
    st.session_state.rol = None

# ==========================================
# 3. LÓGICA DE CONTROL (Tu línea 37 ahora sí va a funcionar)
# ==========================================
# --- PANTALLA A: LOGIN ---
if st.session_state.pantalla == "login" and not st.session_state.logeado:

    # cambiado: ahora usamos el diseño neumórfico en el login
    mostrar_login_neumorfico()
    # Creamos columnas para centrar el botón nativo perfectamente abajo de la tarjeta
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<p style='text-align: center; color: #5bc0de; margin-bottom: 5px;'>¿No tienes una cuenta aún?</p>", unsafe_allow_html=True)
        # Este botón es nativo, por lo que responderá al instante sin trabas de navegador
        if st.button("Regístrate aquí", use_container_width=True):
            st.session_state.pantalla = "registro"
            st.rerun()

# ==========================================
# PANTALLA B: REGISTRO (Totalmente aislada)
# ==========================================
elif st.session_state.pantalla == "registro":
    
    
# aqui nacen las pestañas interactivas d lado a lado
    st.write("") # un espacio elegante de separación
    formulario_registro_profesional()
    
    # ---CONTENIDO DE LA PESTAÑA CLIENTE
    st.write("") # un espacio elegante de separación
    formulario_registro_cliente()

    # BOTON ELEGANTE Y PLANO PARA REGRESAR AL LOGIN (FUUERA DEL BLOQUE DE PESTAÑAS)
    st.markdown("---")
    if st.button("← Volver al Inicio de Sesión", use_container_width=True):
        st.session_state.pantalla = "login"
        st.rerun()

        # ---PNATALLA C: VISTA PRINCIPAL (AQUI VA EL NUEVO CODIGO PARA VER DESPUES DE CARGAR EL LOGIN
else:
    st.title("Panel Principal - AXON")
    
    # Tarjeta de diagnóstico para ver los datos capturados en tiempo real
    st.subheader(f"¡Bienvenido de vuelta, {st.session_state.get('nombre_usuario', 'Usuario')}!")
    
    st.info(f"🔑 *Rol de cuenta detectado:* {st.session_state.get('rol', 'No definido').upper()}")
    
    # Mensaje dinámico dependiendo de quién entra
    if st.session_state.rol == "profesional":
        st.success("💪 Vista de Entrenador/Nutricionista: Aquí se cargará tu Dashboard de ingresos, agenda y clientes.")
    elif st.session_state.rol == "cliente":
        st.success("👤 Vista de Cliente: Aquí verás tus historias de salud y los profesionales disponibles para contratar.")
        st.title("🔍 Vitrina de Especialistas AXON")
        st.subheader(f"¡hola, {st.session_state.nombre_usuario.title()}! explorar los profesionales disponibles para contratar.")
        st.markdown("---")
        
        # selector de especialidad 
        filtro_esp = st.selectbox(
            "¿ que tipo de especialista esta buscando?", 
            ["todos", "Entrenador personal", "Nutricionista al deporte ", "fisioterapeuta"],
            key="esp_filtro"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        #  base de datos de perfiles de profesionales
        perfiles = [
            {  
                "nombre": "Javid Martinez",
                "especialidad": "Entrenador personal",
                "edad": 30,
                "altura": "1.75 m",
                "peso": "70.0 kg",
                "genero": "Masculino",
                "telefono": "3123456789",
                "email": "javidmartinez@example.com",
                "ciudad": "barranquilla",
                "experiencia": "5 años",
                "tarifa": 100000.0,
                "certificacion": "certificado en biomecanica y entrenamiento de alta intensidad",
                "calificacion": "⭐ 4.9 (38 opiniones)",
            "cupos": "🚨 ¡Solo 3 cupos disponibles!",
            "metodologia": "Enfoque estricto en ganancias de masa muscular mediante hipertrofia con tempos controlados (3s excéntrico).",
            "emoji": "🏋️‍♂️"
        },
        {
                "nombre": "arya stark",
                "especialidad": "nutrisionista al deporte",
                "edad": 30,
                "altura": "1.60 m",
                "peso": "55.0 kg",  
                "genero": "femenino",
                "telefono": "3123456789",
                "email": "aryastark@example.com",
                "ciudad": "barranquilla",
                "experiencia": "5 años",
                "tarifa": 100000.0,
                "certificacion":"diploma posgrado, certificado en nutricion y alimentacion",
                "calificacion": "⭐ 5.0 (52 opiniones)",
            "cupos": "🚨 ¡Solo 3 cupos disponibles!",
            "metodologia": "Enfoque estricto en la alimentacion y la nutricion para mejorar la salud y la performance",
            "emoji": "🥑"
        },
        {
                 "nombre": "Dante sparta",
                 "especialidad": "fisioterapeuta",
                 "edad": 30,
                 "altura": "1.80 m",
                 "peso": "80.0 kg",
                 "genero": "Masculino",
                 "telefono": "3123456789",
                 "email": "dantespparta@example.com",
                 "ciudad": "barranquilla",
                 "experiencia": "5 años",
                 "tarifa": 100000.0,
                 "certificacion":"diploma posgrado, certificado en fisioterapia y rehabilitacion",
                 "calificacion": "⭐ 5.0 (52 opiniones)",
            "cupos": "🚨 ¡Solo 3 cupos disponibles!",
            "metodologia": "Enfoque estricto en la fisioterapia para mejorar la salud y la performance",
            "emoji": "🏋️‍♂️"
        }
    ]
    # renderizado de la tarjetas dentro del bloque del cliente
    # 🔄 201. Ciclo FOR para recorrer los entrenadores
    for i, prof in enumerate(perfiles):
        # 202. Corregido: "Todos" con la T mayúscula para que coincida con tu selectbox
        if filtro_esp != "Todos" and prof["especialidad"] != filtro_esp:
            continue
            
        # 205. El contenedor principal
        with st.container(border=True):
            # 206. Corregido: st.columns en inglés y con un Tab de sangría hacia la derecha
            col_foto_datos, col_detalles = st.columns([1, 2])
            
            # 208. Bloque izquierdo (va alineado con la línea de arriba)
            with col_foto_datos:
                st.markdown(f"## {prof['emoji']} {prof['nombre']}")
                st.caption(f"📍 {prof['ciudad']}")
                st.markdown(f"**{prof['calificacion']}**")
                st.markdown("---")
                st.markdown("**📊 Ficha Física:**")
                st.markdown(f"* **Edad:** {prof['edad']} años")
                st.markdown(f"* **Altura:** {prof['altura']}")
                st.markdown(f"* **Peso:** {prof['peso']}")
                st.markdown("---")
                st.caption(prof["cupos"])
            
            # 220. Bloque derecho (va alineado a la misma altura de col_foto_datos)
            with col_detalles:
                st.markdown(f"### 💼 {prof['especialidad']}")
                st.markdown(f"🏅 **Título:** *{prof['certificacion']}*")
                st.markdown(f"⭐ **Experiencia:** {prof['experiencia']}")
                st.markdown(f"💰 **Tarifa:** ${prof['tarifa']:.2f} COP / sesión")
                st.markdown("---")
                st.markdown("**🎯 Metodología y Enfoque:**")
                st.write(prof["metodologia"])
                st.markdown("---")
                
                # Botón de contacto
                if st.button(f"🤝 Solicitar Asesoría con {prof['nombre'].split()[0]}", key=f"btn_conectar_{i}", use_container_width=True):
                    st.success(f"🚀 ¡Solicitud enviada! Nos comunicaremos con {prof['nombre']} para agendar tu cupo.")
                st.write(prof["metodologia"])
                st.markdown("---")
                
                if st.button(f"🤝 Solicitar Asesoría con {prof['nombre'].split()[0]}", key=f"btn_conectar_{i}", use_container_width=True):
                    st.success(f"🚀 ¡Solicitud enviada! Nos comunicaremos con {prof['nombre']} para agendar tu cupo.")
    # ⬆️ HASTA AQUÍ LLEGA EL CÓDIGO NUEVO ⬆️

# 🚨 TU BOTÓN ACTUAL SE QUEDA ABAJO ASÍ DE INTACTO:
st.markdown("---")  # (Esta era tu línea 132)
if st.button("Cerrar Sesión", use_container_width=True):  # (Tu línea 134)
    st.session_state.logeado = False
    st.session_state.rol = None
    st.session_state.pantalla = "login"
    st.rerun()

                            


            

        




           
            
        
        


               
    
    
