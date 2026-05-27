import streamlit as st
from basededatos.manejarbasededatos import listar_certificaciones_profesional

def perfil_profesional_view(datos):
    """Muestra la vista detallada del profesional para los clientes"""
    prof_id = datos.get("id")
    nombre = datos.get("nombre") or "Profesional"
    st.title(nombre)

    col1, col2 = st.columns([1, 2])

    with col1:
        foto = datos.get("foto") or "https://via.placeholder.com/240"
        st.image(foto, use_container_width=True)

        estado = (datos.get("estado_verificacion") or "").strip().lower()
        if estado:
            st.caption(f"Estado: {estado}")

        especialidad = datos.get("especialidad")
        if especialidad:
            st.write(f"🎯 {especialidad}")

        universidad = datos.get("universidad")
        if universidad:
            st.write(f"🎓 {universidad}")

        ubicacion = ", ".join([x for x in [(datos.get("ciudad") or "").strip(), (datos.get("departamento") or "").strip()] if x])
        if ubicacion:
            st.write(f"📍 {ubicacion}")

        experiencia = datos.get("experiencia")
        if experiencia is not None:
            st.metric("Experiencia", f"{int(experiencia)} años")

        tarifa = datos.get("tarifa")
        if tarifa is not None:
            st.success(f"Precio por sesión: ${float(tarifa):,.0f} COP")

        telefono = datos.get("telefono")
        if telefono:
            st.write(f"📱 {telefono}")

        email = datos.get("email")
        if email:
            st.write(f"📧 {email}")

    with col2:
        st.subheader("Descripción / Metodología")
        metodologia = (datos.get("metodologia") or "").strip()
        st.write(metodologia if metodologia else "Sin descripción aún.")

        st.subheader("Datos del formulario")
        col_a, col_b, col_c = st.columns(3)
        genero = datos.get("genero")
        if genero:
            col_a.metric("Género", str(genero))

        edad = datos.get("edad")
        if edad is not None:
            col_b.metric("Edad", f"{int(edad)}")

        created_at = datos.get("created_at")
        if created_at:
            col_c.metric("Registro", str(created_at)[:10])

        col_d, col_e, col_f = st.columns(3)
        altura = datos.get("altura")
        if altura is not None:
            col_d.metric("Altura", f"{float(altura):.2f} m")
        peso = datos.get("peso")
        if peso is not None:
            col_e.metric("Peso", f"{float(peso):.1f} kg")
        departamento = datos.get("departamento")
        if departamento:
            col_f.metric("Departamento", str(departamento))

        certificacion_texto = (datos.get("certificacion") or "").strip()
        if certificacion_texto:
            st.write(f"🏅 {certificacion_texto}")

        if prof_id is not None:
            certs = listar_certificaciones_profesional(int(prof_id))
        else:
            certs = []

        st.subheader("Certificados / Diplomas")
        if certs:
            for c in certs:
                archivo = c.get("archivo")
                mime = c.get("archivo_mime") or "application/octet-stream"
                titulo = c.get("titulo") or "Certificado"
                if archivo and str(mime).startswith("image/"):
                    st.image(archivo, caption=titulo, use_container_width=True)
                elif archivo:
                    st.download_button(
                        f"Descargar: {titulo}",
                        data=archivo,
                        file_name=f"cert_{int(c.get('id') or 0)}",
                        mime=mime,
                        use_container_width=True,
                    )
        else:
            st.info("Este profesional no tiene certificados cargados.")

        if st.button("Reservar Cita Ahora", use_container_width=True, key=f"btn_reservar_{prof_id or 'x'}"):
            st.session_state["interes_en"] = prof_id
            st.info("Conectando con el calendario...")
