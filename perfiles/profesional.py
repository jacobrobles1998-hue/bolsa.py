import base64
import html

import streamlit as st
from basededatos.manejarbasededatos import (
    DEPARTAMENTOS_COLOMBIA,
    actualizar_profesional,
    guardar_foto_profesional,
    listar_certificaciones_profesional,
)


def _avatar_profesional(nombre: str, foto, mime: str | None, *, size_px: int = 140, verificado: bool = False):
    nombre_safe = html.escape(nombre or "Profesional")

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
        f"<img class=\"axon-pro-avatar-img\" src=\"{html.escape(src)}\" alt=\"{nombre_safe}\" />"
        if src
        else f"<div class=\"axon-pro-avatar-fallback\">{html.escape(iniciales)}</div>"
    )

    verificado_html = ""
    if verificado:
        verificado_html = """
        <span class=\"axon-pro-verified\" title=\"Verificado\" aria-label=\"Verificado\">
            <svg width=\"18\" height=\"18\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">
                <path d=\"M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2Z\" fill=\"#1D9BF0\"/>
                <path d=\"M10.0 13.6 7.9 11.5 6.8 12.6 10.0 15.8 17.2 8.6 16.1 7.5 10.0 13.6Z\" fill=\"white\"/>
            </svg>
        </span>
        """

    return f"""
    <style>
    .axon-pro-avatar {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        padding-top: 6px;
        padding-bottom: 6px;
    }}
    .axon-pro-avatar-circle {{
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
    .axon-pro-avatar-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}
    .axon-pro-avatar-fallback {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: {max(28, int(size_px * 0.28))}px;
        color: #334155;
    }}
    .axon-pro-avatar-name {{
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
    .axon-pro-verified {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transform: translateY(1px);
    }}
    </style>
    <div class="axon-pro-avatar">
        <div class="axon-pro-avatar-circle">{img_html}</div>
        <div class="axon-pro-avatar-name">{nombre_safe}{verificado_html}</div>
    </div>
    """


def _format_cop(value) -> str:
    try:
        return f"{int(float(value)):,.0f}".replace(",", ".")
    except Exception:
        return str(value)


def _mostrar_campo(etiqueta: str, valor, *, uid: int = 0):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return
    safe = "".join(c if c.isalnum() else "_" for c in etiqueta)
    st.text_input(f"{etiqueta}:", value=str(valor), disabled=True, key=f"pro_ro_{uid}_{safe}")


def perfil_profesional_view(datos, *, editable: bool = False):
    """Muestra la vista detallada del profesional para los clientes"""
    prof_id = datos.get("id")
    nombre = datos.get("nombre") or "Profesional"

    estado = (datos.get("estado_verificacion") or "").strip().lower()
    verificado = estado in {"verificado", "aprobado", "verified", "validado"} or ("verif" in estado)

    foto = datos.get("foto")
    mime = datos.get("foto_mime")
    st.markdown(_avatar_profesional(nombre, foto, mime, size_px=170, verificado=verificado), unsafe_allow_html=True)

    uid = int(prof_id or 0)

    if editable and uid:
        edit_key = f"pro_edit_open_{uid}"
        col_btn_l, col_btn, col_btn_r = st.columns([1, 1.2, 1])
        with col_btn:
            if st.button(
                "Editar perfil",
                use_container_width=True,
                key=f"btn_edit_prof_{uid}",
            ):
                st.session_state[edit_key] = not bool(st.session_state.get(edit_key))

        if st.session_state.get(edit_key):
            st.markdown("#### Foto de perfil")
            tab_f = st.tabs(["Subir foto"])[0]
            foto_file = None
            with tab_f:
                up = st.file_uploader(
                    "Subir foto",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"pro_edit_up_{uid}",
                )
                if up is not None:
                    foto_file = up

            if st.button("Guardar foto", use_container_width=True, disabled=(foto_file is None), key=f"pro_edit_save_foto_{uid}"):
                foto_bytes = foto_file.getvalue() if foto_file is not None else None
                foto_mime = getattr(foto_file, "type", None)
                if foto_bytes:
                    guardar_foto_profesional(uid, foto_bytes, foto_mime)
                    st.success("Foto de perfil actualizada.")
                    st.rerun()

            st.markdown("---")

            deptos = list(DEPARTAMENTOS_COLOMBIA.keys())
            depto_key = f"pro_edit_depto_{uid}"
            ciudad_key = f"pro_edit_ciudad_{uid}"

            current_depto = (datos.get("departamento") or "").strip()
            if depto_key not in st.session_state:
                st.session_state[depto_key] = current_depto if current_depto in deptos else (deptos[0] if deptos else "")

            depto_sel = st.selectbox(
                "Departamento de residencia",
                deptos,
                index=(deptos.index(st.session_state[depto_key]) if st.session_state[depto_key] in deptos else 0),
                key=depto_key,
            )

            ciudades = DEPARTAMENTOS_COLOMBIA.get(depto_sel, [])
            current_ciudad = (datos.get("ciudad") or "").strip()
            if ciudad_key not in st.session_state:
                st.session_state[ciudad_key] = current_ciudad if current_ciudad in ciudades else (ciudades[0] if ciudades else "")
            if ciudades and st.session_state.get(ciudad_key) not in ciudades:
                st.session_state[ciudad_key] = ciudades[0]

            ciudad_sel = st.selectbox(
                "Barrio / Ciudad",
                ciudades,
                key=ciudad_key,
            )

            nombre_key = f"pro_edit_nombre_{uid}"
            tel_key = f"pro_edit_tel_{uid}"
            gen_key = f"pro_edit_gen_{uid}"
            esp_key = f"pro_edit_esp_{uid}"
            uni_key = f"pro_edit_uni_{uid}"
            exp_key = f"pro_edit_exp_{uid}"
            tarifa_key = f"pro_edit_tarifa_{uid}"
            tunit_key = f"pro_edit_tunit_{uid}"
            metodo_key = f"pro_edit_metodo_{uid}"

            if nombre_key not in st.session_state:
                st.session_state[nombre_key] = datos.get("nombre") or ""
            if tel_key not in st.session_state:
                st.session_state[tel_key] = datos.get("telefono") or ""
            if gen_key not in st.session_state:
                st.session_state[gen_key] = (datos.get("genero") or "")
            if esp_key not in st.session_state:
                st.session_state[esp_key] = (datos.get("especialidad") or "")
            if uni_key not in st.session_state:
                st.session_state[uni_key] = (datos.get("universidad") or "")
            if exp_key not in st.session_state:
                st.session_state[exp_key] = int(datos.get("experiencia") or 0)
            if tarifa_key not in st.session_state:
                st.session_state[tarifa_key] = _format_cop(datos.get("tarifa") or 0)
            if tunit_key not in st.session_state:
                st.session_state[tunit_key] = (datos.get("tarifa_unidad") or "sesion")
            if metodo_key not in st.session_state:
                st.session_state[metodo_key] = (datos.get("metodologia") or "")

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                nombre_new = st.text_input("Nombre completo", key=nombre_key)
                telefono_new = st.text_input("Teléfono", key=tel_key)
                genero_new = st.selectbox(
                    "Género",
                    ["", "Masculino", "Femenino", "Otro"],
                    index=["", "Masculino", "Femenino", "Otro"].index(st.session_state.get(gen_key) if st.session_state.get(gen_key) in ["", "Masculino", "Femenino", "Otro"] else ""),
                    key=gen_key,
                )
                especialidad_new = st.text_input("Especialidad", key=esp_key)
                universidad_new = st.text_input("Universidad", key=uni_key)

            with col_e2:
                experiencia_new = st.number_input("Años de Experiencia", min_value=0, max_value=60, step=1, key=exp_key)
                tarifa_txt = st.text_input("Precio (COP)", placeholder="Ej: 300.000", key=tarifa_key)
                tarifa_unidad_ui = st.selectbox(
                    "Periodicidad",
                    ["sesion", "semana", "mes"],
                    index=["sesion", "semana", "mes"].index(
                        st.session_state.get(tunit_key) if st.session_state.get(tunit_key) in ["sesion", "semana", "mes"] else "sesion"
                    ),
                    key=tunit_key,
                )

            metodologia_new = st.text_area("Descripción / Metodología", height=140, key=metodo_key)

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Guardar cambios", use_container_width=True, key=f"pro_edit_save_{uid}"):
                    tarifa_val = None
                    digits = "".join(ch for ch in str(tarifa_txt or "") if ch.isdigit())
                    if digits:
                        try:
                            tarifa_val = float(int(digits))
                        except Exception:
                            tarifa_val = None

                    ok = actualizar_profesional(
                        uid,
                        {
                            "nombre": (nombre_new or "").strip() or None,
                            "telefono": (telefono_new or "").strip() or None,
                            "departamento": depto_sel,
                            "ciudad": ciudad_sel,
                            "genero": (genero_new or "").strip() or None,
                            "especialidad": (especialidad_new or "").strip() or None,
                            "universidad": (universidad_new or "").strip() or None,
                            "experiencia": int(experiencia_new) if experiencia_new is not None else None,
                            "tarifa": tarifa_val,
                            "tarifa_unidad": (tarifa_unidad_ui or "sesion").strip().lower(),
                            "metodologia": (metodologia_new or "").strip() or None,
                        },
                    )
                    if ok:
                        st.session_state[edit_key] = False
                        st.success("Perfil actualizado.")
                        st.rerun()
                    else:
                        st.warning("No se pudieron aplicar cambios.")

            with col_cancel:
                if st.button("Cancelar", use_container_width=True, key=f"pro_edit_cancel_{uid}"):
                    st.session_state[edit_key] = False
                    st.rerun()

    st.markdown(
        """
        <style>
        div[data-testid="stTabs"]{
            max-width: 760px;
            margin: 0 auto;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-list"]{
            gap: 8px;
            padding: 6px 4px;
            border-bottom: 1px solid rgba(15,23,42,.08);
            flex-wrap: wrap;
        }
        div[data-testid="stTabs"] [data-baseweb="tab"]{
            background: transparent !important;
            color: #64748B !important;
            border-radius: 999px !important;
            padding: 10px 14px !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            border: 1px solid rgba(15,23,42,.08) !important;
        }
        div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]{
            background: #0EA5A4 !important;
            color: #FFFFFF !important;
            border-color: rgba(14,165,164,.2) !important;
            box-shadow: 0 10px 22px rgba(14,165,164,.22) !important;
        }
        div[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]){
            background: rgba(15,23,42,.04) !important;
            color: #0F172A !important;
        }
        div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"]{display:none !important;}
        div[data-testid="stTabs"] [role="tabpanel"]{
            animation: synapseFade .18s ease-in-out;
        }
        @keyframes synapseFade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab_info, tab_media = st.tabs(["Información", "Multimedia"])

    with tab_info:
        st.subheader("Descripción / Metodología")
        metodologia = (datos.get("metodologia") or "").strip()
        st.write(metodologia if metodologia else "Sin descripción aún.")

        st.markdown("---")
        st.subheader("Datos del profesional")

        uid = int(prof_id or 0)

        ubicacion = ", ".join(
            [x for x in [(datos.get("ciudad") or "").strip(), (datos.get("departamento") or "").strip()] if x]
        )

        col_a, col_b = st.columns(2)

        with col_a:
            _mostrar_campo("Especialidad", datos.get("especialidad"), uid=uid)
            _mostrar_campo("Universidad", datos.get("universidad"), uid=uid)
            _mostrar_campo("Ubicación", ubicacion, uid=uid)
            experiencia = datos.get("experiencia")
            if experiencia is not None:
                _mostrar_campo("Experiencia", f"{int(experiencia)} años", uid=uid)
            _mostrar_campo("Departamento", datos.get("departamento"), uid=uid)

        with col_b:
            tarifa = datos.get("tarifa")
            if tarifa is not None:
                _mostrar_campo("Precio por sesión", f"${float(tarifa):,.0f} COP", uid=uid)
            _mostrar_campo("Teléfono", datos.get("telefono"), uid=uid)
            _mostrar_campo("Correo", datos.get("email"), uid=uid)
            _mostrar_campo("Género", datos.get("genero"), uid=uid)
            edad = datos.get("edad")
            if edad is not None:
                _mostrar_campo("Edad", int(edad), uid=uid)
            created_at = datos.get("created_at")
            if created_at:
                _mostrar_campo("Registro", str(created_at)[:10], uid=uid)

        certificacion_texto = (datos.get("certificacion") or "").strip()
        if certificacion_texto:
            _mostrar_campo("Certificación", certificacion_texto, uid=uid)

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

    with tab_media:
        st.empty()

   