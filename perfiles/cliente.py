import streamlit as st
import base64
import html


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


def _avatar_cliente(nombre: str, foto, mime: str | None, *, size_px: int = 140):
    nombre_safe = html.escape(nombre or "Cliente")

    src = None
    if isinstance(foto, (bytes, bytearray)) and foto:
        mime_final = (mime or "image/jpeg").strip() or "image/jpeg"
        b64 = base64.b64encode(bytes(foto)).decode("ascii")
        src = f"data:{mime_final};base64,{b64}"
    elif isinstance(foto, str) and foto.strip():
        src = foto.strip()

    iniciales = "?"
    if nombre and str(nombre).strip():
        partes = [p for p in str(nombre).strip().split() if p]
        iniciales = ("".join([p[0] for p in partes[:2]]) or "?").upper()

    img_html = (
        f"<img class=\"axon-cli-avatar-img\" src=\"{html.escape(src)}\" alt=\"{nombre_safe}\" />"
        if src
        else f"<div class=\"axon-cli-avatar-fallback\">{html.escape(iniciales)}</div>"
    )

    return f"""
    <style>
    .axon-cli-avatar {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding-top: 6px;
        padding-bottom: 6px;
    }}
    .axon-cli-avatar-circle {{
        width: {int(size_px)}px;
        height: {int(size_px)}px;
        border-radius: 999px;
        overflow: hidden;
        background: #F0F2F5;
        border: 2px solid rgba(255,255,255,0.9);
        box-shadow: 6px 6px 14px #CBD5E1, -6px -6px 14px #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .axon-cli-avatar-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}
    .axon-cli-avatar-fallback {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: {max(28, int(size_px * 0.28))}px;
        color: #334155;
    }}
    .axon-cli-avatar-name {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        justify-content: center;
        text-align: center;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #0F172A;
        font-size: 18px;
        line-height: 1.1;
    }}
    </style>
    <div class=\"axon-cli-avatar\">
        <div class=\"axon-cli-avatar-circle\">{img_html}</div>
        <div class=\"axon-cli-avatar-name\">{nombre_safe}</div>
    </div>
    """


def perfil_cliente_view(datos_usuario, *, mostrar_foto: bool = True):
    """Muestra el formulario de registro del cliente en modo solo lectura."""
    nombre = datos_usuario.get("nombre") or "Cliente"
    uid = int(datos_usuario.get("id") or 0)

    if mostrar_foto:
        st.markdown(
            _avatar_cliente(
                nombre,
                datos_usuario.get("foto"),
                datos_usuario.get("foto_mime"),
                size_px=170,
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"### {nombre}")

    st.caption("Estos son los datos que registraste. Solo lectura.")

    st.markdown(
        """
        <style>
        div[data-testid="stTextInput"] input[disabled] {
            color: #111 !important;
            -webkit-text-fill-color: #111 !important;
            opacity: 1 !important;
        }
        div[data-testid="stTextArea"] textarea[disabled] {
            color: #111 !important;
            -webkit-text-fill-color: #111 !important;
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
