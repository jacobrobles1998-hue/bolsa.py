import streamlit as st

def formulario_registro():
    st.subheader("Crea tu perfil profesional")
    
    with st.form("registro_form"):
        nombre = st.text_input("Nombre completo")
        tipo_profesional = st.selectbox(
            "¿Cuál es tu especialidad?",
            ["Entrenador Personal", "Nutricionista al deporte", "Fisioterapeuta", "nutricinista clinico"]
        )
        ciudad = st.selectbox(
            "Ciudad de residencia", 
            ["Barranquilla", "Soledad", "Puerto Colombia"] # Basado en tu zona de operación
        )
        experiencia = st.number_input("Años de experiencia", min_value=0, step=1)
        tarifa = st.number_input("Tarifa base por sesión (COP)", min_value=0)
        
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        
        enviar = st.form_submit_with_button("Registrarme en la Bolsa")
        
        if enviar:
            if nombre and email and password:
                # Aquí es donde luego conectaremos con la carpeta 'datos'
                st.success(f"¡Bienvenido, {nombre}! Tu perfil como {tipo_profesional} ha sido creado.")
            else:
                st.error("Por favor, llena todos los campos obligatorios.")