import streamlit as st


def _mostrar_campo(etiqueta: str, valor, unidad: str = "", *, uid: int = 0):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return
    texto = valor
    if unidad and valor is not None:
        if unidad == "m" and isinstance(valor, (int, float)):
            texto = f"{float(valor):.2f} {unidad}"
        elif unidad == "kg" and isinstance(valor, (int, float)):
            texto = f"{float(valor):.1f} {unidad}"
        elif unidad == "años" and isinstance(valor, (int, float)):
            texto = f"{int(valor)} {unidad}"
        else:
            texto = f"{valor} {unidad}".strip()
    safe = "".join(c if c.isalnum() else "_" for c in etiqueta)
    st.text_input(etiqueta, value=str(texto), disabled=True, key=f"cli_ro_{uid}_{safe}")


def perfil_cliente_view(datos_usuario, *, mostrar_foto: bool = True):
    """Muestra el formulario de registro del cliente en modo solo lectura."""
    nombre = datos_usuario.get("nombre") or "Cliente"
    uid = int(datos_usuario.get("id") or 0)
    st.markdown(f"### {nombre}")
    st.caption("Estos son los datos que registraste. Solo lectura.")

    if mostrar_foto:
        foto = datos_usuario.get("foto")
        if foto:
            mime = datos_usuario.get("foto_mime") or "image/jpeg"
            st.image(foto, caption="Tu foto de perfil", width=160)

    st.markdown("#### Datos de cuenta y contacto")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        _mostrar_campo("Nombre completo", datos_usuario.get("nombre"), uid=uid)
        _mostrar_campo("Departamento de residencia", datos_usuario.get("departamento"), uid=uid)
        _mostrar_campo("Patología familiar", datos_usuario.get("patologia_familiar"), uid=uid)
    with col_c2:
        _mostrar_campo("Teléfono", datos_usuario.get("telefono"), uid=uid)
        _mostrar_campo("Género", datos_usuario.get("genero"), uid=uid)

    st.markdown("---")
    st.markdown("#### Datos básicos")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        _mostrar_campo("Edad (Años)", datos_usuario.get("edad"), "años", uid=uid)
    with col_b2:
        _mostrar_campo("Altura (Metros)", datos_usuario.get("altura"), "m", uid=uid)
    with col_b3:
        _mostrar_campo("Peso actual (Kg)", datos_usuario.get("peso"), "kg", uid=uid)

    metodologia = datos_usuario.get("metodologia")
    if metodologia and str(metodologia).strip():
        st.markdown("#### Información para tus profesionales")
        st.text_area(
            "Condiciones o notas",
            value=str(metodologia).strip(),
            disabled=True,
            height=120,
            key=f"cli_ro_{uid}_metodologia",
        )
