import streamlit as st

def mostrar_busqueda():
    st.title("Encuentra tu Especialista")
    
    # Filtros de Negocio
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ciudad = st.selectbox("Ciudad", ["Barranquilla", "Soledad", "Puerto Colombia"])
    with col2:
        especialidad = st.selectbox("Especialidad", ["Entrenador", "Nutricionista", "Fisioterapeuta"])
    with col3:
        presupuesto = st.slider("Presupuesto máximo (COP)", 0, 200000, 80000)

    # Simulación de resultados de búsqueda
    st.write(f"### Profesionales disponibles en {ciudad}")
    
    # Aquí es donde el código buscaría en la Carpeta 5 (database)
    # Por ahora, mostramos una tarjeta de ejemplo
    c1, c2 = st.columns(2)
    with c1:
        with st.container():
            st.markdown("#### Coach Carlos")
            st.write("Especialista en Hipertrofia")
            st.write("💰 $70,000 / sesión")
            if st.button("Ver Perfil Completo", key="btn1"):
                st.session_state['view'] = 'professional_profile'