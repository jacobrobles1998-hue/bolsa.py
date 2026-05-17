import streamlit as st

def formulario_registro_profesional():
    """
    Formulario de registro para Entrenadores, Nutricionistas y Fisioterapeutas.
    Optimizado sin botones de incremento (+/-) para mejorar la visualización.
    """
    st.markdown("### Datos del Profesional")
    
    # 1. Campos de texto y selección estilizados
    nombre = st.text_input("Nombre completo", placeholder="Ej: Javid Martínez", key="prof_nombre")
    edad_input = st.number_input("Edad", value=25, key="prof_edad")
    
    especialidad = st.selectbox(
        "¿Cuál es tu especialidad?",
        ["Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"],
        key="prof_especialidad"
    )
    
    ciudad = st.text_input("Ciudad de residencia", placeholder="Ej: Bogotá, Colombia", key="prof_ciudad")
     # EXPERIENCIA (¡AQUI CAMBIAMOS LA MAGIA, PERMITIMOS DECIMALES COMO 1.5 O 2.5)
    experiencia_input = st.number_input("Años de experiencia", value=5, key="prof_experiencia")
    
    modalidad = st.selectbox(
        "¿Cuál es tu modalidad de cobro?",
        ["Pago por sesión", "Pago por mes"],
        key="prof_modalidad"
    )
    
    tarifa_input = st.number_input("Tarifa base por sesión (COP)", min_value=0.0, max_value=1000000.0, step=5000.0 , value=150000.0, format="%.2f", key="prof_tarifa")
    
    # Credenciales
    st.markdown("---")
   
    correo = st.text_input("Correo electrónico", placeholder="ejemplo@axon.com", key="prof_correo")
    contrasena = st.text_input("Contraseña", type="password", placeholder="Crea una contraseña segura", key="prof_pass")
    
    
   # ... (Aquí arriba tienes tus inputs: tarifa_input, correo, contrasena)

    st.write("") # Espacio en blanco visual

    # 🏢 EL BOTÓN COMPLETAMENTE LIBRE AL FINAL DEL FORMULARIO
    if st.button("Registrarme en la Bolsa", use_container_width=True, key="btn_prof_registro"):
        # 1. Validamos que los campos de texto no estén vacíos
        if not nombre.strip() or not correo.strip():
            st.error("⚠️ Por favor, llena los campos de Nombre y Correo Electrónico.")
        
        # 2. Validamos que los números tengan sentido lógico
        elif edad_input < 15 or experiencia_input < 0 or tarifa_input <= 0:
            st.error("⚠️ Por favor, ingresa una edad, experiencia o tarifa válidas.")
            
        else:
            # 🌟 SE GIRA LA LLAVE EN LA MEMORIA GLOBAL
            st.session_state.logeado = True
            st.session_state.rol = "profesional"
            st.session_state.nombre_usuario = nombre
            st.session_state.pantalla = "dashboard"
            
            st.success(f"¡Excelente, {nombre}! Tu perfil de profesional ha sido registrado con éxito.")
            st.rerun()

def formulario_registro_cliente():
    """
    Formulario de registro para Clientes con historial de salud obligatorio y dinámico.
    Optimizado sin presupuesto y adaptado para entrenadores profesionales.
    """
    st.markdown("## Datos del Cliente")
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