import streamlit as st

def formulario_registro_profesional():
    with st.form("registro_form"):
        nombre = st.text_input("Nombre completo")
        edad = st.number_input("Edad", min_value=0, step=1)
        tipo_profesional = st.selectbox(
            "¿Cuál es tu especialidad?",
            ["Entrenador Personal", "Nutricionista al deporte", "Fisioterapeuta"]
        )
        ciudad = st.selectbox(
            "Ciudad de residencia", 
            ["Barranquilla", "Soledad", "Puerto Colombia"]
        )
        experiencia = st.number_input("Años de experiencia", min_value=0, step=1)
        
        modalidad_pago = st.selectbox(
            "¿Cuál es tu modalidad de cobro?",
            ["Por sesión", "Pago por mes"]  
        )
        tarifa = st.number_input("Tarifa base por sesión (COP)", min_value=0) 
        
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        
        enviar = st.form_submit_button("Registrarme en la Bolsa")
        
        if enviar:
            if nombre and email and password:
                # Modificamos el estado global al registrarse con éxito
                st.session_state.logeado = True
                st.session_state.rol = "profesional"
                st.session_state.nombre_usuario = nombre
                st.success(f"¡Bienvenido, {nombre}! Tu perfil como {tipo_profesional} ha sido creado.")
                st.rerun()
            else:
                st.error("Por favor, llena todos los campos obligatorios.")

# --- FORMULARIO DE REGISTRO PARA CLIENTES (CORREGIDO) ---
def formulario_registro_cliente():
    # Todo lo que está dentro de la función lleva 4 espacios de sangría
    with st.form("registo_cliente_form"):
        # Todo lo que va DENTRO del formulario lleva 8 espacios de sangría
        st.subheader("Crea tu perfil cliente")
        
        nombre = st.text_input("Nombre completo", key="cliente_nombre")
        edad = st.number_input("Edad", min_value=0, step=1, key="cliente_edad")
        ciudad = st.selectbox(
            "Ciudad de residencia", 
            ["Barranquilla", "Soledad", "Puerto Colombia"],
            key="cliente_ciudad"
        )
        
        # Agregamos los campos de salud que tenías sueltos DENTRO del formulario
        st.markdown("---")
        st.markdown("### Historias de salud y condición física")
        st.caption("Esta información es crucial para que el profesional diseñe un plan seguro.")
        
        # Checkbox de patologías (puedes agregar más campos aquí)
        tiene_patologia = st.checkbox("¿Sufres de alguna patología o lesión diagnosticada?")
        detalles_salud = st.text_area("Si marcaste la casilla, detalla brevemente tu condición:")
        
        email = st.text_input("Correo electrónico", key="cliente_email")
        password = st.text_input("Contraseña", type="password", key="cliente_password")
        
        # ⚠️ EL BOTÓN DE GUARDADO CORREGIDO: Debe estar indentado aquí adentro
        enviar_cliente = st.form_submit_button("Registrarme como Cliente")
        
        if enviar_cliente:
            if nombre and email and password:
                # Modificamos el estado global al registrarse con éxito
                st.session_state.logeado = True
                st.session_state.rol = "cliente"
                st.session_state.nombre_usuario = nombre
                st.success(f"¡Bienvenido, {nombre}! Tus datos han sido guardados.")
                st.rerun()
            else:
                st.error("Por favor, llena todos los campos obligatorios.")


# --- CONTROL DE FLUJO PRINCIPAL (Al final del archivo, pegado al margen izquierdo) ---

if "logeado" not in st.session_state:
    st.session_state.logeado = False
if "rol" not in st.session_state:
    st.session_state.rol = None

if not st.session_state.logeado:
    # Selector inicial limpio para alternar entre ambos formularios sin que se mezclen
    tipo_registro = st.radio("¿Cómo deseas registrarte?", ["Como Profesional", "Como Cliente"])
    
    if tipo_registro == "Como Profesional":
        formulario_registro_profesional()
    else:
        formulario_registro_cliente()
else:
    # Vista una vez logeado
    st.title(f"Panel Principal - AXON")
    st.write(f"Hola *{st.session_state.get('nombre_usuario', '')}, has ingresado como *{st.session_state.rol}**.")
    
    if st.button("Cerrar Sesión"):
        st.session_state.logeado = False
        st.session_state.rol = None
        st.rerun()
                