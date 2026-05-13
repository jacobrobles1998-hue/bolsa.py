import streamlit as st

def mostrar_interfaz_login():
    st.subheader("Iniciar Sesión")
    
    email = st.text_input("Correo electrónico", key="login_email")
    password = st.text_input("Contraseña", type="password", key="login_pass")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Entrar"):
            # Lógica para verificar credenciales (se conectará con la DB)
            if email == "test@test.com" and password == "1234":
                st.session_state['autenticado'] = True
                st.success("Ingreso exitoso")
            else:
                st.error("Usuario o contraseña incorrectos")
                
    with col2:
        if st.button("Olvidé mi contraseña"):
            st.info("Función en desarrollo. Contacta al administrador de AXON.")