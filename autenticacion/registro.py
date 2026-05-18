import streamlit as st
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA



def formulario_registro_profesional():
   
    st.markdown("crea tu cuenta para ingresar a la plataforma.")
    # aqui conservamos las pestañas actuales intactas
    tab_profesional, tab_cliente = st.tabs(["Profesional", "Cliente"])

    # ---1. pestaña del profesional---
    with tab_profesional:
        st.markdown("registro de nuevo profesional")
        st.caption("completa para perfil para poder ofrecer tus servivios en axon")

        # inyectamos el formulario si tocar las pestañas
        with st.form("form_registro_largo_profesional"):
            
            # ---seccion A: DATOS DE CUENTA Y CONTACTOS---
            st.markdown(" Datos de cuenta y contacto")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nombre_completo = st.text_input("Nombre completo", placeholder="Ej: Javid Martínez")
                correo_electronico = st.text_input("Correo electrónico", placeholder="Ej: javid.martinez@example.com")
        # ---selector de departamentos (jala las llaves del diccionario: atlantico, antiquia...)
                depto_sel = st.selectbox(
                "Departamento de residencia",
                list(DEPARTAMENTOS_COLOMBIA.keys())
        )
         # --- selector de ciudades (magicamente solo muestra las ciudades del departamento seleccionado)
                ciudad_sel = st.selectbox(
                "Ciudad/municipio",
                DEPARTAMENTOS_COLOMBIA[depto_sel]
            )

            with col_c2:
                telefono = st.text_input("Teléfono", placeholder="Ej: 31012345678")
                contrasena = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres")
                confirmar_contrasena = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña"    )
                genero = st.selectbox(
                    "Género",
                    ["Masculino", "Femenino", "otro"]
                )
                st.markdown("---")
            
            # --- SECCIÓN B: FICHA FÍSICA ---
            st.markdown("Ficha Física del Especialista")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                edad = st.number_input("Edad (Años)", min_value=18, max_value=90, value=24, step=1)
            with col_f2:
                altura = st.number_input("Altura (Metros)", min_value=1.20, max_value=2.30, value=1.75, step=0.01, format="%.2f")
            with col_f3:
                peso = st.number_input("Peso Actual (Kg)", min_value=40.0, max_value=150.0, value=74.0, step=0.1, format="%.1f")
                
            st.markdown("---")
            
            # --- SECCIÓN C: PERFIL PROFESIONAL ---
            st.markdown(" Información Profesional y Tarifas")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                especialidad = st.selectbox(
                    "Tu Especialidad Principal", 
                    ["Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"]
                )
                certificacion = st.text_input("Título o Certificación Destacada", placeholder="Ej: Certificado en Biomecánica")
            with col_p2:
                experiencia = st.number_input("Años de Experiencia", min_value=0, max_value=50, value=5, step=1)
                tarifa = st.number_input("Tarifa por Sesión (COP)", min_value=10000.0, value=60000.0, step=5000.0, format="%.2f")
                
            st.markdown("<br>", unsafe_allow_html=True)
            metodologia = st.text_area(
                "Describe tu Metodología y Enfoque (Esto lo verán tus clientes)", 
                placeholder="Ej: Enfoque estricto en ganancias de masa muscular mediante hipertrofia con tempos controlados (3s excéntrico)..."
            )
            
            # Botón de envío exclusivo para el formulario del profesional
            boton_enviar_prof = st.form_submit_button("🚀 Crear Perfil Profesional", use_container_width=True)
            
            if boton_enviar_prof:
                if not nombre_completo.strip() or not correo_electronico.strip() or not contrasena.strip():
                    st.error("⚠️ Por favor, llena los campos obligatorios.")
                else:
                    st.success(f"💪 ¡Perfil de {nombre_completo} creado con éxito!")

    # --- 2. PESTAÑA DEL CLIENTE (SE QUEDA COMO LA TIENES ACABADA) ---
    with tab_cliente:
        st.markdown("## 👤 Registro de Nuevo Cliente")
        st.caption("Regístrate como cliente para buscar y contratar a los mejores profesionales.")
        
        # Aquí adentro dejas el código corto que ya tienes hecho para el cliente
        # (Nombre, Correo, Contraseña, Botón de registrar cliente, etc.)
                
def formulario_registro_cliente():
    """
    Formulario de registro para Clientes con historial de salud obligatorio y dinámico.
    Optimizado sin presupuesto y adaptado para entrenadores profesionales.
    """
    st.markdown("Datos del Cliente")
    # st.subheader("Crea tu perfil cliente")
    
    # 1. Información Básica
    nombre_cliente = st.text_input("Nombre completo", placeholder="Ej: Carlos Gómez", key="cli_nombre")
    edad_input = st.number_input("Edad", value=25, key="cli_edad")
    
    ciudad = st.selectbox(
        "Ciudad de residencia", 
        ["Barranquilla", "Soledad", "Puerto Colombia"],
        key="cli_ciudad"
    )
        
    st.markdown("---")
    st.markdown("### Historial de Salud y Condición Física")
    st.caption("Esta información es crucial para que el profesional diseñe un plan seguro y eficiente.")
        
    # 2. Bloque de Patologías Inteligente
    tiene_patologia = st.checkbox("¿Sufres de alguna patología, enfermedad o lesión diagnosticada?", key="cli_patologia")
    
    detalles_salud = ""
    if tiene_patologia:
        # Si marca la casilla, aparece este cuadro de texto grande de forma obligatoria
        detalles_salud = st.text_area(
            "⚠️ DETALLE OBLIGATORIO: Describe brevemente tu condición (Ej: Hernia discal L4-L5, Hipertensión, Esguince de rodilla):", 
            placeholder="Escribe aquí los detalles médicos para tu entrenador...",
            key="cli_detalles"
        )
    
    st.markdown("---")
    st.markdown("### Credenciales de Cuenta")
    email = st.text_input("Correo electrónico", placeholder="Ej: carlos.gomez@example.com", key="cli_email")
    password = st.text_input("Contraseña", type="password", key="cli_password")
        
   # ... (Aquí arriba tienes tus inputs de cliente: nombre_cliente, correo_cliente, etc.)

    st.write("") # Espacio en blanco visual

    # 👥 EL BOTÓN COMPLETAMENTE LIBRE AL FINAL DEL FORMULARIO CLIENTE
    if st.button("Registrarme en la Bolsa", use_container_width=True, key="btn_cliente_registro"):
        # 1. Validamos que los campos de texto no estén vacíos
        if not nombre_cliente.strip() or not email.strip():
            st.error("⚠️ Por favor, llena los campos de Nombre y Correo Electrónico.")
            
        else:
            # 🌟 SE GIRA LA LLAVE EN LA MEMORIA GLOBAL
            st.session_state.logeado = True
            st.session_state.rol = "cliente"
            st.session_state.nombre_usuario = nombre_cliente
            st.session_state.pantalla = "dashboard"
            
            st.success(f"¡Excelente, {nombre_cliente}! Tu perfil de Cliente ha sido registrado con éxito.")
            st.rerun()