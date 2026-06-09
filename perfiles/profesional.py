import base64
import html
import re
from urllib.parse import quote, urlparse, parse_qs, urlencode

from api_cliente import backend_get_json as _backend_get_json, backend_post_json as _backend_post_json

import streamlit as st
import streamlit.components.v1 as components
from chat.realtime import render_inbox_listener, render_realtime_chat, render_tab_badge_listener
from shared.catalogos import DEPARTAMENTOS_COLOMBIA, GENEROS
from shared.catalogos_profesionales import TARIFA_UNIDADES
from shared.formatters import format_cop_input, format_datetime_short, initials, shorten_text
from shared.media import bytes_to_b64
from shared.validators import validate_cert_file, validate_image_file


def _h(value) -> str:
    return html.escape("" if value is None else str(value))


_INBOX_CSS = """
<style>
.axon-inbox {max-width: 780px; margin: 0 auto;}
.axon-inbox a,
.axon-inbox a:visited,
.axon-inbox a:hover,
.axon-inbox a:active,
.axon-inbox-item,
.axon-inbox-item:hover,
.axon-inbox-item:visited,
.axon-inbox-item:active,
.axon-inbox-item *,
.axon-inbox-item *:hover,
.axon-inbox-item *:visited,
.axon-inbox-item *:active{ color: inherit !important; text-decoration: none !important; }
.axon-inbox-item{display:flex; align-items:center; gap:14px; padding:12px 10px; border-radius:16px; border:1px solid rgba(15,23,42,.06); background:rgba(255,255,255,.92); box-shadow:0 10px 24px rgba(15,23,42,.06);}
.axon-inbox-item:hover{ background: rgba(248,250,252,1); }
.axon-inbox-avatar{width:56px; height:56px; border-radius:999px; overflow:hidden; display:flex; align-items:center; justify-content:center; background:#e2e8f0; border:3px solid rgba(148,163,184,.55); flex:0 0 56px;}
.axon-inbox-item.unread .axon-inbox-avatar{ border-color: rgba(239,68,68,.75); }
.axon-inbox-avatar img{ width:100%; height:100%; object-fit:cover; display:block; }
.axon-inbox-avatar .ini{ font-weight:900; color:#0f172a; font-size:18px; }
.axon-inbox-body{ flex:1 1 auto; min-width:0; }
.axon-inbox-title{ font-weight:900; color:#0f172a; font-size:16px; line-height:1.1; }
.axon-inbox-sub{ color:#64748b; font-size:13px; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.axon-inbox-meta{ flex:0 0 auto; text-align:right; min-width:72px; }
.axon-inbox-time{ color:#64748b; font-size:12px; }
.axon-inbox-badge{display:inline-flex; min-width:22px; height:22px; padding:0 7px; border-radius:999px; background:#ef4444; color:#fff; align-items:center; justify-content:center; font-weight:900; font-size:12px; margin-top:6px;}
.axon-inbox-sep{ height:10px; }
</style>
"""


def _ensure_inbox_css():
    st.markdown(_INBOX_CSS, unsafe_allow_html=True)


def _render_hidden_rerun_button(button_key: str):
    st.markdown(
        f"""
        <style>
        .st-key-{button_key}{{position:fixed !important;left:-9999px !important;top:0 !important;width:1px !important;height:1px !important;opacity:0 !important;pointer-events:none !important;}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.button("↻", key=button_key)


@st.cache_data(ttl=20, show_spinner=False)
def _api_get_prof_certs(token: str, prof_id: int, include_archivo: bool) -> list[dict]:
    res = _backend_get_json(
        f"/profesionales/{int(prof_id)}/certificaciones",
        {"token": str(token), "include_archivo": "true" if include_archivo else "false"},
    )
    return (res or {}).get("items") or []


def _qp_get(key: str):
    try:
        v = st.query_params.get(key)
        if isinstance(v, (list, tuple)):
            return v[0] if v else None
        return v
    except Exception:
        v = st.experimental_get_query_params().get(key)
        return v[0] if isinstance(v, list) and v else None


def _qp_all() -> dict:
    try:
        raw = dict(st.query_params)
    except Exception:
        raw = st.experimental_get_query_params()
    out = {}
    for k, v in raw.items():
        if isinstance(v, list):
            if v:
                out[k] = v[0]
        elif v is not None:
            out[k] = str(v)
    return out


def _qp_set(updates: dict):
    params = _qp_all()
    for k, v in (updates or {}).items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = str(v)

    try:
        for k in list(st.query_params.keys()):
            del st.query_params[k]
        for k, v in params.items():
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**params)


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


def _avatar_profesional(
    nombre: str,
    foto,
    mime: str | None,
    *,
    size_px: int = 140,
    verificado: bool = False,
    show_foto: bool = True,
):
    nombre_safe = html.escape(nombre or "Profesional")

    src = None
    if show_foto:
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

def _mostrar_campo(etiqueta: str, valor, *, uid: int = 0):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return
    safe = "".join(c if c.isalnum() else "_" for c in etiqueta)
    st.text_input(f"{etiqueta}:", value=str(valor), disabled=True, key=f"pro_ro_{uid}_{safe}")


def _render_profesional_edit_form(*, datos: dict, uid: int):
    st.markdown("#### Foto de perfil")
    foto_file = st.file_uploader(
        "Subir foto",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"pro_edit_up_{uid}",
        label_visibility="collapsed",
    )

    if st.button(
        "Guardar foto",
        use_container_width=True,
        disabled=(foto_file is None),
        key=f"pro_edit_save_foto_{uid}",
    ):
        try:
            foto_bytes, foto_mime = validate_image_file(foto_file)
        except ValueError as e:
            st.error(str(e))
        else:
            try:
                token = st.session_state.get("auth_token") or _qp_get("s")
                if not token:
                    raise RuntimeError("Sesión no encontrada. Vuelve a iniciar sesión.")
                _backend_post_json(
                    "/me/foto",
                    {"token": str(token)},
                    {
                        "foto_b64": bytes_to_b64(foto_bytes),
                        "foto_mime": foto_mime,
                    },
                )
            except Exception as e:
                st.error(str(e))
                st.stop()

            st.success("Foto de perfil actualizada.")
            st.rerun()

    st.markdown("#### Subir diplomas / certificados")

    token = st.session_state.get("auth_token") or _qp_get("s")
    current = []
    if token:
        try:
            current = _api_get_prof_certs(str(token), int(uid), True)
        except Exception:
            current = []

    if current:
        st.caption("Certificados ya cargados")
        for c in current:
            titulo = c.get("titulo") or "Certificado"
            mime = c.get("archivo_mime") or "application/octet-stream"
            archivo_b64 = c.get("archivo_b64")
            archivo = None
            if archivo_b64:
                try:
                    archivo = base64.b64decode(str(archivo_b64))
                except Exception:
                    archivo = None

            if archivo and str(mime).startswith("image/"):
                st.image(archivo, caption=titulo, use_container_width=True)
            elif archivo:
                st.download_button(
                    f"Descargar: {titulo}",
                    data=archivo,
                    file_name=f"cert_{int(c.get('id') or 0)}",
                    mime=mime,
                    use_container_width=True,
                    key=f"pro_cert_dl_{uid}_{int(c.get('id') or 0)}",
                )

    cert_files = st.file_uploader(
        "Subir diplomas / certificados",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"pro_cert_upload_{uid}",
        label_visibility="collapsed",
    )

    if st.button(
        "Guardar certificados",
        use_container_width=True,
        disabled=not bool(cert_files),
        key=f"pro_cert_save_{uid}",
    ):
        try:
            saved = 0
            token = st.session_state.get("auth_token") or _qp_get("s")
            if not token:
                raise RuntimeError("Sesión no encontrada. Vuelve a iniciar sesión.")
            for f in (cert_files or []):
                b, m = validate_cert_file(f)
                _backend_post_json(
                    "/me/certificaciones",
                    {"token": str(token)},
                    {
                        "titulo": None,
                        "archivo_b64": bytes_to_b64(b),
                        "archivo_mime": m,
                    },
                )
                saved += 1
        except ValueError as e:
            st.error(str(e))
        else:
            st.success(f"Certificados guardados: {int(saved)}")
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
        st.session_state[tarifa_key] = format_cop_input(datos.get("tarifa") or 0)
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
            ["", *GENEROS],
            index=["", *GENEROS].index(
                st.session_state.get(gen_key) if st.session_state.get(gen_key) in ["", *GENEROS] else ""
            ),
            key=gen_key,
        )
        especialidad_new = st.text_input("Especialidad", key=esp_key)
        universidad_new = st.text_input("Universidad", key=uni_key)

    with col_e2:
        experiencia_new = st.number_input("Años de Experiencia", min_value=0, max_value=60, step=1, key=exp_key)
        tarifa_txt = st.text_input("Precio (COP)", placeholder="Ej: 300.000", key=tarifa_key)
        tarifa_unidad_ui = st.selectbox(
            "Periodicidad",
            TARIFA_UNIDADES,
            index=TARIFA_UNIDADES.index(
                st.session_state.get(tunit_key) if st.session_state.get(tunit_key) in TARIFA_UNIDADES else "sesion"
            ),
            key=tunit_key,
        )

    metodologia_new = st.text_area("Descripción / Metodología", height=140, key=metodo_key)

    if st.button("Guardar cambios", use_container_width=True, key=f"pro_edit_save_{uid}"):
        tarifa_val = None
        digits = "".join(ch for ch in str(tarifa_txt or "") if ch.isdigit())
        if digits:
            try:
                tarifa_val = float(int(digits))
            except Exception:
                tarifa_val = None

        cambios = {
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
        }
        try:
            token = st.session_state.get("auth_token") or _qp_get("s")
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



def configuraciones_profesional_view(datos: dict):
    uid = int((datos or {}).get("id") or 0)
    if not uid:
        st.info("No se pudo cargar el perfil profesional.")
        return
    _render_profesional_edit_form(datos=dict(datos), uid=uid)


def perfil_profesional_view(datos, *, editable: bool = False, owner: bool = False):
    """Muestra la vista detallada del profesional para los clientes"""
    prof_id = datos.get("id")
    nombre = datos.get("nombre") or "Profesional"

    estado = (datos.get("estado_verificacion") or "").strip().lower()
    verificado = estado in {"verificado", "aprobado", "verified", "validado"} or ("verif" in estado)

    foto = datos.get("foto")
    mime = datos.get("foto_mime")
    st.markdown(
        _avatar_profesional(
            nombre,
            foto,
            mime,
            size_px=170,
            verificado=verificado,
            show_foto=True,
        ),
        unsafe_allow_html=True,
    )

    uid = int(prof_id or 0)
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

        .st-key-pro_more_toggle button{
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            border-radius: 14px !important;
            background: #F1F5F9 !important;
            border: 1px solid rgba(15,23,42,.10) !important;
            box-shadow: 3px 3px 6px #CBD5E1, -2px -2px 5px #FFFFFF !important;
            padding: 0 !important;
            color: #0F172A !important;
            font-size: 22px !important;
            font-weight: 800 !important;
            line-height: 1 !important;
        }

        .st-key-pro_more_settings button,
        .st-key-pro_more_profile button{
            border-radius: 12px !important;
            background: #0B1220 !important;
            border: 1px solid rgba(255,255,255,.08) !important;
            color: #E2E8F0 !important;
            box-shadow: 0 16px 40px rgba(2,6,23,.28) !important;
            padding: 10px 12px !important;
            font-weight: 700 !important;
        }

        .st-key-pro_more_settings button{margin-bottom: 6px !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "pro_more_open" not in st.session_state:
        st.session_state.pro_more_open = False

    _, col_more = st.columns([0.86, 0.14])
    with col_more:
        if st.button("⋮", key="pro_more_toggle"):
            st.session_state.pro_more_open = not bool(st.session_state.pro_more_open)

        if st.session_state.pro_more_open:
            if st.button("Configuraciones", use_container_width=True, key="pro_more_settings"):
                st.session_state.submenu_actual = "Configuraciones"
                st.session_state.pro_more_open = False
                if "selected_profesional_id" in st.session_state:
                    st.session_state.selected_profesional_id = None
                if "selected_cliente_chat_id" in st.session_state:
                    st.session_state.selected_cliente_chat_id = None
                _qp_set({"tab": "Configuraciones", "prof": None, "cli": None})
                st.rerun()

            if st.button("Perfil", use_container_width=True, key="pro_more_profile"):
                st.session_state.submenu_actual = "perfil"
                st.session_state.pro_more_open = False
                if "selected_profesional_id" in st.session_state:
                    st.session_state.selected_profesional_id = None
                if "selected_cliente_chat_id" in st.session_state:
                    st.session_state.selected_cliente_chat_id = None
                _qp_set({"tab": "perfil", "prof": None, "cli": None})
                st.rerun()

    if (owner or editable) and uid:
        open_cid = _qp_get("open_cli")
        if open_cid:
            try:
                st.session_state.selected_cliente_chat_id = int(open_cid)
            except Exception:
                pass

        abrir_chat_directo = bool(open_cid or st.session_state.get("selected_cliente_chat_id"))
        tab_labels = ["Mensaje", "Información", "Multimedia"] if abrir_chat_directo else ["Información", "Multimedia", "Mensaje"]
        tabs = st.tabs(tab_labels)
        tab_map = dict(zip(tab_labels, tabs))
        tab_info = tab_map["Información"]
        tab_media = tab_map["Multimedia"]
        tab_msg = tab_map["Mensaje"]

        token_badge = st.session_state.get("auth_token") or _qp_get("s")
        if token_badge:
            render_tab_badge_listener(token=str(token_badge), tab_text="Mensaje")
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

        token_sesion = st.session_state.get("auth_token") or _qp_get("s")
        if prof_id is not None and token_sesion:
            try:
                certs = _api_get_prof_certs(str(token_sesion), int(prof_id), True)
            except Exception:
                certs = []
        else:
            certs = []

        st.subheader("Certificados / Diplomas")
        if certs:
            for c in certs:
                archivo_b64 = c.get("archivo_b64")
                archivo = None
                if archivo_b64:
                    try:
                        archivo = base64.b64decode(str(archivo_b64))
                    except Exception:
                        archivo = None
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

        if not (owner or editable):
            st.markdown("---")
            if st.button("Hablar con este profesional", use_container_width=True, key=f"cli_hablar_prof_{uid}"):
                st.session_state.selected_profesional_id = int(uid)
                st.session_state.submenu_actual = "Mensajes"
                _qp_set({"tab": "Mensajes", "prof": None})
                st.rerun()

    with tab_media:
        uid = int(prof_id or 0)
        if not uid:
            st.empty()
        elif not (owner or editable):
            urls = [
                ("TikTok", (datos.get("url_tiktok") or "").strip()),
                ("Instagram", (datos.get("url_instagram") or "").strip()),
                ("Facebook", (datos.get("url_facebook") or "").strip()),
                ("YouTube", (datos.get("url_youtube") or "").strip()),
            ]

            any_ok = False
            for nombre, url in urls:
                if not url:
                    continue
                html_embed = _multimedia_embed_html(url)
                if not html_embed:
                    continue
                any_ok = True
                st.markdown(f"### {nombre}")
                components.html(html_embed, height=640, scrolling=False)

            if not any_ok:
                st.info("Este profesional no tiene videos públicos cargados.")
        else:
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
                cambios = {
                    "url_tiktok": (st.session_state.get(k_tt) or "").strip() or None,
                    "url_instagram": (st.session_state.get(k_ig) or "").strip() or None,
                    "url_facebook": (st.session_state.get(k_fb) or "").strip() or None,
                    "url_youtube": (st.session_state.get(k_yt) or "").strip() or None,
                }
                try:
                    token = st.session_state.get("auth_token") or _qp_get("s")
                    if not token:
                        raise RuntimeError("Sesión no encontrada. Vuelve a iniciar sesión.")
                    res = _backend_post_json("/me/profile", {"token": str(token)}, {"cambios": cambios})
                except Exception as e:
                    st.error(str(e))
                else:
                    if (res or {}).get("ok"):
                        st.success("Enlaces guardados.")
                        st.rerun()
                    else:
                        st.warning("No se pudieron guardar los enlaces.")

    if tab_msg is not None:
        with tab_msg:
            token_chat = st.session_state.get("auth_token") or _qp_get("s")
            if not token_chat:
                st.info("Inicia sesión para ver tus mensajes.")
            else:


                def _href_open_cli(cliente_id: int) -> str:
                    params = _qp_all()
                    params["tab"] = params.get("tab") or "perfil"
                    params["open_cli"] = str(int(cliente_id))
                    qs = urlencode({k: v for k, v in params.items() if v is not None})
                    return "?" + qs

                _ensure_inbox_css()

                try:
                    inbox = _backend_get_json(
                        "/inbox",
                        {"token": str(token_chat), "limit": 60, "include_foto": "false"},
                    )
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tus conversaciones: {e}")
                    convs = []

                open_cid = _qp_get("open_cli")
                if open_cid:
                    try:
                        st.session_state.selected_cliente_chat_id = int(open_cid)
                    except Exception:
                        pass

                cid = st.session_state.get("selected_cliente_chat_id")

                if cid is None:
                    refresh_key = f"inbox_refresh_properfil_{int(uid)}"
                    _render_hidden_rerun_button(refresh_key)
                    render_inbox_listener(token=str(token_chat), rol="profesional", user_id=int(uid), rerun_button_key=refresh_key)
                    st.markdown("<div class='axon-inbox'>", unsafe_allow_html=True)
                    if not convs:
                        st.info("Aún no tienes conversaciones.")
                    else:
                        for it in convs:
                            cli_id = int(it.get("cliente_id") or 0)
                            nombre = (it.get("nombre") or "Cliente").strip() or "Cliente"
                            last_texto = shorten_text(it.get("last_texto"), 56)
                            last_at = format_datetime_short(it.get("last_at"))
                            unread = int(it.get("unread") or 0)

                            foto_b64 = it.get("foto_b64")
                            mime = it.get("foto_mime")
                            src = None
                            if foto_b64:
                                mt = (mime or "image/jpeg").strip() or "image/jpeg"
                                src = f"data:{mt};base64,{foto_b64}"

                            avatar_html = (
                                f"<img src='{_h(src)}' alt='{_h(nombre)}' />" if src else f"<div class='ini'>{_h(initials(nombre))}</div>"
                            )
                            badge_html = f"<div class='axon-inbox-badge'>{unread}</div>" if unread > 0 else ""
                            item_cls = "axon-inbox-item unread" if unread > 0 else "axon-inbox-item"

                            st.markdown(
                                f"""
                                <a class="{item_cls}" href="{_h(_href_open_cli(cli_id))}" target="_self" onclick="event.preventDefault(); window.parent.location.href=this.href;">
                                  <div class="axon-inbox-avatar">{avatar_html}</div>
                                  <div class="axon-inbox-body">
                                    <div class="axon-inbox-title">{_h(nombre)}</div>
                                    <div class="axon-inbox-sub">{_h(last_texto or '—')}</div>
                                  </div>
                                  <div class="axon-inbox-meta">
                                    <div class="axon-inbox-time">{_h(last_at)}</div>
                                    {badge_html}
                                  </div>
                                </a>
                                <div class="axon-inbox-sep"></div>
                                """,
                                unsafe_allow_html=True,
                            )

                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    cid = int(cid)

                    if st.button("← Volver", key=f"chat_back_inbox_properfil_{uid}_{cid}"):
                        st.session_state.selected_cliente_chat_id = None
                        _qp_set({"open_cli": None})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="profesional",
                        cliente_id=int(cid),
                        profesional_id=int(uid),
                        height=640,
                    )
