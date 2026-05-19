import streamlit as st

def perfil_cliente_view(datos_usuario):
    """Panel de control para el cliente (atleta)"""
    nombre = datos_usuario.get("nombre") or "Cliente"
    st.header(nombre)

    foto = datos_usuario.get("foto")
    if foto:
        st.image(foto, use_container_width=False, width=160)
    
    tab1, tab2 = st.tabs(["Mi Perfil", "Citas"])

    with tab1:
        st.subheader("Mis Datos")
        col_m1, col_m2, col_m3 = st.columns(3)
        edad = datos_usuario.get("edad")
        if edad is not None:
            col_m1.metric("Edad", f"{int(edad)}")
        altura = datos_usuario.get("altura")
        if altura is not None:
            col_m2.metric("Altura", f"{float(altura):.2f} m")
        peso = datos_usuario.get("peso")
        if peso is not None:
            col_m3.metric("Peso", f"{float(peso):.1f} kg")

        col1, col2 = st.columns(2)
        with col1:
            email = datos_usuario.get("email")
            if email:
                st.write(f"Correo: {email}")
            telefono = datos_usuario.get("telefono")
            if telefono:
                st.write(f"Teléfono: {telefono}")
        with col2:
            depto = datos_usuario.get("departamento")
            if depto:
                st.write(f"Departamento: {depto}")
            genero = datos_usuario.get("genero")
            if genero:
                st.write(f"Género: {genero}")

        patologia = datos_usuario.get("patologia_familiar")
        if patologia:
            st.write(f"Patología familiar: {patologia}")
        metodologia = datos_usuario.get("metodologia")
        if metodologia:
            st.write(metodologia)

    with tab2:
        st.subheader("Próximas Sesiones")
        st.write("📅 Mañana 8:00 AM con Entrenador Carlos")
