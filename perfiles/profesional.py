import base64
import html
import json
import re
from urllib.parse import quote, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import streamlit as st
import streamlit.components.v1 as components
from chat.realtime import render_realtime_chat
from basededatos.manejarbasededatos import (
    DEPARTAMENTOS_COLOMBIA,
    actualizar_profesional,
    guardar_foto_profesional,
    listar_certificaciones_profesional,
    listar_clientes_de_profesional,
)


BACKEND_API_BASE = "http://localhost:8001"


def _h(value) -> str:
    return html.escape("" if value is None else str(value))


def _qp_get(key: str):
    try:
        v = st.query_params.get(key)
        if isinstance(v, (list, tuple)):
            return v[0] if v else None
        return v
    except Exception:
        v = st.experimental_get_query_params().get(key)
        return v[0] if isinstance(v, list) and v else None


def _backend_url(path: str, params: dict | None = None) -> str:
    base = (BACKEND_API_BASE or "").strip().rstrip("/")
    url = base + (path or "")
    if params:
        qs = urlencode({k: v for k, v in params.items() if v is not None})
        if qs:
            url += "?" + qs
    return url


def _backend_get_json(path: str, params: dict | None = None):
    url = _backend_url(path, params)
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=12) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        raise RuntimeError(body or f"HTTP {getattr(e, 'code', 'error')}")
    except URLError as e:
        reason = getattr(e, "reason", None)
        raise RuntimeError(str(reason) if reason else str(e))


def _backend_post_json(path: str, params: dict | None, payload: dict):
    url = _backend_url(path, params)
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(req, timeout=12) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        raise RuntimeError(body or f"HTTP {getattr(e, 'code', 'error')}")
    except URLError as e:
        reason = getattr(e, "reason", None)
        raise RuntimeError(str(reason) if reason else str(e))


def _responsive_iframe(src: str, *, title: str = "Multimedia", aspect_ratio: float = 9 / 16):
    src_safe = html.escape(src or "")
    title_safe = html.escape(title or "Multimedia")
    ratio = max(0.35, min(0.8, float(aspect_ratio)))
    pad = ratio * 100.0
    return f"""
    <style>
    .synapse-embed-wrap{{
        width: 100%;
        max-width: 760px;
        margin: 12px auto 0;
        border-radius: 18px;
        overflow: hidden;
        background: #0B1220;
        box-shadow: 0 16px 40px rgba(15,23,42,.12);
        border: 1px solid rgba(255,255,255,.08);
    }}
    .synapse-embed{{
        position: relative;
        width: 100%;
        padding-top: {pad:.4f}%;
        background: #0B1220;
    }}
    .synapse-embed iframe{{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }}
    </style>
    <div class="synapse-embed-wrap">
        <div class="synapse-embed">
            <iframe
                src="{src_safe}"
                title="{title_safe}"
                loading="lazy"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowfullscreen
            ></iframe>
        </div>
    </div>
    """


def _extract_tiktok_id(url: str) -> str | None:
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def _extract_instagram_code(url: str) -> tuple[str, str] | None:
    m = re.search(r"instagram\.com/(p|reel|tv)/([^/?#]+)/?", url)
    if not m:
        return None
    return m.group(1), m.group(2)


def _extract_youtube_id(url: str) -> str | None:
    u = urlparse(url)
    host = (u.netloc or "").lower()
    path = (u.path or "").strip("/")

    if "youtu.be" in host:
        return path.split("/")[0] if path else None

    if "youtube.com" in host:
        if path.startswith("shorts/"):
            parts = path.split("/")
            return parts[1] if len(parts) > 1 else None
        if path.startswith("watch"):
            q = parse_qs(u.query or "")
            v = q.get("v")
            return v[0] if v else None
        if path.startswith("embed/"):
            parts = path.split("/")
            return parts[1] if len(parts) > 1 else None

    return None


def _multimedia_embed_html(url: str):
    raw = (url or "").strip()
    if not raw:
        return None

    u = urlparse(raw)
    host = (u.netloc or "").lower()
    full = raw

    if "tiktok.com" in host:
        vid = _extract_tiktok_id(full)
        if not vid:
            return None
        src = f"https://www.tiktok.com/embed/v2/{vid}"
        return _responsive_iframe(src, title="TikTok", aspect_ratio=9 / 16)

    if "instagram.com" in host:
        code = _extract_instagram_code(full)
        if not code:
            return None
        kind, shortcode = code
        src = f"https://www.instagram.com/{kind}/{shortcode}/embed"
        return _responsive_iframe(src, title="Instagram", aspect_ratio=1)

    if "facebook.com" in host or "fb.watch" in host:
        src = f"https://www.facebook.com/plugins/video.php?href={quote(full, safe='')}&show_text=false"
        return _responsive_iframe(src, title="Facebook", aspect_ratio=9 / 16)

    if "youtube.com" in host or "youtu.be" in host:
        vid = _extract_youtube_id(full)
        if not vid:
            return None
        src = f"https://www.youtube.com/embed/{quote(vid)}"
        return _responsive_iframe(src, title="YouTube", aspect_ratio=9 / 16)

    return None


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

    if editable and uid:
        tab_info, tab_media, tab_msg = st.tabs(["Información", "Multimedia", "Mensaje"])
    else:
        tab_info, tab_media = st.tabs(["Información", "Multimedia"])
        tab_msg = None

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
        if not (editable and int(prof_id or 0)):
            st.empty()
        else:
            uid = int(prof_id or 0)

            st.warning(
                "Aviso Importante: Para garantizar una visualización correcta, asegúrate de que tus videos (TikTok, Instagram, Facebook o YouTube) estén configurados como PÚBLICOS. Los enlaces a contenido privado no se visualizarán."
            )

            st.markdown(
                """
                <style>
                .synapse-media-row{max-width:760px;margin:0 auto}
                .synapse-media-icon{
                    width:40px;height:40px;border-radius:14px;
                    display:flex;align-items:center;justify-content:center;
                    background:#F1F5F9;border:1px solid rgba(15,23,42,.08);
                    font-size:18px;
                    box-shadow: 4px 4px 10px rgba(15,23,42,.08);
                    margin-top: 20px;
                }
                .synapse-media-label{font-weight:800;color:#0F172A;margin-top:14px;margin-bottom:6px}
                </style>
                """,
                unsafe_allow_html=True,
            )

            def _init_key(key: str, value: str | None):
                if key not in st.session_state:
                    st.session_state[key] = (value or "")

            k_tt = f"pro_media_tiktok_{uid}"
            k_ig = f"pro_media_instagram_{uid}"
            k_fb = f"pro_media_facebook_{uid}"
            k_yt = f"pro_media_youtube_{uid}"

            _init_key(k_tt, datos.get("url_tiktok"))
            _init_key(k_ig, datos.get("url_instagram"))
            _init_key(k_fb, datos.get("url_facebook"))
            _init_key(k_yt, datos.get("url_youtube"))

            def _render_row(nombre: str, key: str, placeholder: str, dominio: str | None):
                st.markdown("<div class='synapse-media-row'>", unsafe_allow_html=True)
                st.markdown(f"<div class='synapse-media-label'>{nombre}</div>", unsafe_allow_html=True)
                url = st.text_input(nombre, placeholder=placeholder, key=key, label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)

                url = (url or "").strip()
                if not url:
                    return
                host = (urlparse(url).netloc or "").lower()
                if dominio and dominio not in host:
                    st.info(f"Pega un enlace de {nombre}.")
                    return
                html_embed = _multimedia_embed_html(url)
                if not html_embed:
                    st.info(f"Enlace de {nombre} inválido.")
                    return
                components.html(html_embed, height=640, scrolling=False)

            _render_row(
                "TikTok",
                k_tt,
                "Ej: https://www.tiktok.com/@usuario/video/123...",
                "tiktok.com",
            )
            _render_row(
                "Instagram",
                k_ig,
                "Ej: https://www.instagram.com/reel/ABC...",
                "instagram.com",
            )
            _render_row(
                "Facebook",
                k_fb,
                "Ej: https://www.facebook.com/...",
                "facebook.com",
            )
            _render_row(
                "YouTube",
                k_yt,
                "Ej: https://youtu.be/ID o https://www.youtube.com/watch?v=ID",
                "youtube.com",
            )

            if st.button("Guardar enlaces", use_container_width=True, key=f"pro_media_save_{uid}"):
                ok = actualizar_profesional(
                    uid,
                    {
                        "url_tiktok": (st.session_state.get(k_tt) or "").strip() or None,
                        "url_instagram": (st.session_state.get(k_ig) or "").strip() or None,
                        "url_facebook": (st.session_state.get(k_fb) or "").strip() or None,
                        "url_youtube": (st.session_state.get(k_yt) or "").strip() or None,
                    },
                )
                if ok:
                    st.success("Enlaces guardados.")
                    st.rerun()
                else:
                    st.warning("No se pudieron guardar los enlaces.")

    if tab_msg is not None:
        with tab_msg:
            st.subheader("Mensajes")
            st.caption("Aquí te llegarán los mensajes que te escriban los clientes.")

            token_chat = st.session_state.get("auth_token") or _qp_get("s")
            if not token_chat:
                st.info("Inicia sesión para ver tus mensajes.")
            else:
                try:
                    inbox = _backend_get_json(
                        "/inbox",
                        {"token": str(token_chat), "limit": 50},
                    )
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tu bandeja: {e}")
                    convs = []

                if not convs:
                    st.info("Aún no tienes mensajes de clientes.")
                else:
                    options = []
                    id_map = {}
                    name_map = {}
                    for r in convs:
                        cid = int(r.get("cliente_id") or 0)
                        nombre_cli = (r.get("nombre") or "Cliente").strip() or "Cliente"
                        last_at = (r.get("last_at") or "")
                        last_at = last_at.replace("T", " ")[:19] if last_at else ""
                        label = f"{nombre_cli} (ID {cid})"
                        if last_at:
                            label = f"{label} • {last_at}"
                        options.append(label)
                        id_map[label] = cid
                        name_map[label] = nombre_cli

                    sel = st.selectbox("Selecciona un cliente", options, key=f"pro_msg_sel_{uid}")
                    cid = int(id_map.get(sel) or 0)
                    cliente_nombre = name_map.get(sel) or "Cliente"

                    st.markdown(f"### {cliente_nombre}")

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="profesional",
                        cliente_id=int(cid),
                        profesional_id=int(uid),
                        height=640,
                    )
