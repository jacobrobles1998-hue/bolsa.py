import streamlit as st

def perfil_profesional_view(datos):
    """Muestra la vista detallada del profesional para los clientes"""
    nombre = datos.get("nombre") or "Profesional"
    st.title(nombre)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(datos.get("foto", "https://via.placeholder.com/150"), use_column_width=True)
        experiencia = datos.get("experiencia")
        if experiencia is not None:
            st.metric("Experiencia", f"{int(experiencia)} años")
        ubicacion = datos.get("ciudad") or datos.get("departamento")
        if ubicacion:
            st.write(f"Ubicación: {ubicacion}")
        especialidad = datos.get("especialidad")
        if especialidad:
            st.write(f"Especialidad: {especialidad}")
        tarifa = datos.get("tarifa")
        if tarifa is not None:
            st.success(f"Precio por sesión: ${float(tarifa):,.0f} COP")
        email = datos.get("email")
        if email:
            st.write(f"Correo: {email}")
        telefono = datos.get("telefono")
        if telefono:
            st.write(f"Teléfono: {telefono}")

    with col2:
        st.subheader("Metodología y Especialidad")
        metodologia = datos.get("metodologia")
        if metodologia:
            st.write(metodologia)
        else:
            st.write("Sin descripción aún.")

        certificacion = datos.get("certificacion")
        if certificacion:
            st.write(f"Certificación: {certificacion}")

        col_a, col_b, col_c = st.columns(3)
        edad = datos.get("edad")
        if edad is not None:
            col_a.metric("Edad", f"{int(edad)}")
        altura = datos.get("altura")
        if altura is not None:
            col_b.metric("Altura", f"{float(altura):.2f} m")
        peso = datos.get("peso")
        if peso is not None:
            col_c.metric("Peso", f"{float(peso):.1f} kg")
        
        if st.button("Reservar Cita Ahora"):
            st.session_state["interes_en"] = datos.get("id")
            st.info("Conectando con el calendario...")
