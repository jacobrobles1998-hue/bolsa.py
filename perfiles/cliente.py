import base64
import html

import streamlit as st

from api_cliente import backend_post_json as _backend_post_json
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA


ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "image/webp"}
MAX_IMAGE_BYTES = 3 * 1024 * 1024


def _sniff_image_mime(data: bytes) -> str | None:
    if not data:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:12].startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _read_validated_image(uploaded) -> tuple[bytes, str]:
    raw = uploaded.getvalue() if uploaded is not None else b""
    if not raw:
        raise ValueError("La imagen está vacía.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen es demasiado grande. Máximo 3MB.")

    declared = (getattr(uploaded, "type", None) or "").strip().lower()
    sniffed = _sniff_image_mime(raw)
    mime = sniffed or declared

    if not mime or mime not in ALLOWED_IMAGE_MIME:
        raise ValueError("Formato de imagen no permitido. Usa PNG, JPG/JPEG o WEBP.")

    if sniffed and declared and sniffed != declared:
        raise ValueError("El tipo de archivo no coincide con el contenido de la imagen.")

    return raw, mime


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

    st.caption("Perfil del cliente")

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


def configuraciones_cliente_view(datos_usuario):
    uid = int(datos_usuario.get("id") or 0)

    st.subheader("Foto de perfil")
    up = st.file_uploader(
        "Subir foto",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"cli_cfg_foto_{uid}",
        label_visibility="collapsed",
    )
    if st.button(
        "Guardar foto",
        use_container_width=True,
        disabled=(up is None),
        key=f"cli_cfg_foto_save_{uid}",
    ):
        try:
            foto_bytes, foto_mime = _read_validated_image(up)
            token = st.session_state.get("auth_token")
            if not token:
                raise RuntimeError("Sesión no encontrada. Vuelve a iniciar sesión.")
            _backend_post_json(
                "/me/foto",
                {"token": str(token)},
                {
                    "foto_b64": base64.b64encode(foto_bytes).decode("ascii"),
                    "foto_mime": foto_mime,
                },
            )
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(str(e))
        else:
            st.success("Foto de perfil actualizada.")
            st.rerun()

    st.markdown("---")
    st.subheader("Datos del perfil")

    nombre_new = st.text_input(
        "Nombre completo",
        value=str(datos_usuario.get("nombre") or ""),
        key=f"cli_cfg_nombre_{uid}",
    )
    telefono_new = st.text_input(
        "Teléfono",
        value=str(datos_usuario.get("telefono") or ""),
        key=f"cli_cfg_tel_{uid}",
    )

    depto_vals = list(DEPARTAMENTOS_COLOMBIA) if DEPARTAMENTOS_COLOMBIA else []
    depto_curr = (datos_usuario.get("departamento") or "").strip()
    depto_idx = depto_vals.index(depto_curr) if depto_curr in depto_vals else 0
    depto_sel = st.selectbox(
        "Departamento de residencia",
        options=depto_vals if depto_vals else [depto_curr or ""],
        index=depto_idx if depto_vals else 0,
        key=f"cli_cfg_depto_{uid}",
    )

    ciudad_new = st.text_input(
        "Ciudad",
        value=str(datos_usuario.get("ciudad") or ""),
        key=f"cli_cfg_ciudad_{uid}",
    )

    genero_new = st.text_input(
        "Género",
        value=str(datos_usuario.get("genero") or ""),
        key=f"cli_cfg_genero_{uid}",
    )

    edad_new = st.number_input(
        "Edad (Años)",
        min_value=0,
        max_value=120,
        value=int(datos_usuario.get("edad") or 0),
        step=1,
        key=f"cli_cfg_edad_{uid}",
    )

    altura_new = st.number_input(
        "Altura (Metros)",
        min_value=0.0,
        max_value=3.0,
        value=float(datos_usuario.get("altura") or 0.0),
        step=0.01,
        format="%.2f",
        key=f"cli_cfg_altura_{uid}",
    )

    peso_new = st.number_input(
        "Peso actual (Kg)",
        min_value=0.0,
        max_value=400.0,
        value=float(datos_usuario.get("peso") or 0.0),
        step=0.1,
        format="%.1f",
        key=f"cli_cfg_peso_{uid}",
    )

    patologia_new = st.text_input(
        "Patología familiar",
        value=str(datos_usuario.get("patologia_familiar") or ""),
        key=f"cli_cfg_pat_{uid}",
    )

    metodologia_new = st.text_area(
        "Condiciones o notas",
        value=str(datos_usuario.get("metodologia") or ""),
        height=120,
        key=f"cli_cfg_met_{uid}",
    )

    if st.button("Guardar cambios", use_container_width=True, key=f"cli_cfg_save_{uid}"):
        cambios = {
            "nombre": (nombre_new or "").strip() or None,
            "telefono": (telefono_new or "").strip() or None,
            "departamento": (depto_sel or "").strip() or None,
            "ciudad": (ciudad_new or "").strip() or None,
            "genero": (genero_new or "").strip() or None,
            "edad": int(edad_new) if edad_new is not None else None,
            "altura": float(altura_new) if altura_new is not None else None,
            "peso": float(peso_new) if peso_new is not None else None,
            "patologia_familiar": (patologia_new or "").strip() or None,
            "metodologia": (metodologia_new or "").strip() or None,
        }
        try:
            token = st.session_state.get("auth_token")
            if not token:
                raise RuntimeError("Sesión no encontrada. Vuelve a iniciar sesión.")
            res = _backend_post_json("/me/profile", {"token": str(token)}, {"cambios": cambios})
        except Exception as e:
            st.error(str(e))
        else:
            if (res or {}).get("ok"):
                st.success("Perfil actualizado.")
                st.rerun()
            else:
                st.warning("No se pudieron aplicar cambios.")
