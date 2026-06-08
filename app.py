import streamlit as st
import streamlit.components.v1 as components
import base64
import html as _html
import random
from urllib.parse import quote, urlencode

from api_cliente import backend_get_json as _backend_get_json, backend_post_json as _backend_post_json
from chat.realtime import render_inbox_listener, render_realtime_chat

# 1. Configuración de la página
st.set_page_config(
    page_title="AXON - Optimización Humana",
    page_icon="🚀",
    layout="wide"
)

st.html(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        html, body, p, h1, h2, h3, h4, h5, h6, button, input, select, textarea {
            font-family: 'Poppins', sans-serif !important;
        }

        [data-testid="stIconMaterial"] span,
        span.material-symbols-outlined,
        span.material-symbols-rounded,
        span.material-symbols-sharp {
            font-family: 'Material Symbols Rounded' !important;
            font-weight: normal !important;
            font-style: normal !important;
            letter-spacing: normal !important;
            text-transform: none !important;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
    </style>
    """,
)

# IMPORTACIONES
from autenticacion.ingresos import mostrar_interfaz_login
from autenticacion.registro import formulario_registro_profesional_ui, formulario_registro_cliente_ui
from perfiles.profesional import configuraciones_profesional_view, perfil_profesional_view    
from perfiles.cliente import configuraciones_cliente_view, perfil_cliente_view
from basededatos.manejarbasededatos import (
    asegurar_profesional_demo,
    buscar_profesionales,
    crear_contrato,
    crear_sesion,
    crear_tablas_iniciales,
    eliminar_cliente,
    eliminar_profesional,
    guardar_foto_cliente,
    guardar_foto_profesional,
    listar_clientes_de_profesional,
    obtener_cliente_por_id,
    obtener_profesional_por_id,
    obtener_todos_los_profesionales,
)
from estilo.estilocss import css__styles
from interfaz_base import barra_navegacion_glass

st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) 

MAX_IMAGE_BYTES = 3 * 1024 * 1024
ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "image/webp"}


def _read_image_upload(file_obj):
    if file_obj is None:
        raise ValueError("No se recibió archivo.")
    mime = getattr(file_obj, "type", None) or ""
    if mime not in ALLOWED_IMAGE_MIME:
        raise ValueError("Formato de imagen no permitido.")
    data = file_obj.getvalue()
    if not data:
        raise ValueError("La imagen está vacía.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen es demasiado pesada. Usa una imagen más liviana.")
    return data, mime


def _h(value) -> str:
    return _html.escape("" if value is None else str(value))

def _img_src(foto_bytes, mime: str | None):
    if not foto_bytes:
        return "https://via.placeholder.com/96"
    try:
        b64 = base64.b64encode(foto_bytes).decode("ascii")
        mt = (mime or "image/jpeg").strip() or "image/jpeg"
        return f"data:{mt};base64,{b64}"
    except Exception:
        return "https://via.placeholder.com/96"


def _api_decode_foto(item: dict | None) -> dict:
    out = dict(item or {})
    fb = out.pop("foto_b64", None)
    if fb:
        try:
            out["foto"] = base64.b64decode(str(fb))
        except Exception:
            out["foto"] = None
    return out


def _api_get_me_profile(token: str | None) -> dict | None:
    if not token:
        return None
    me = _backend_get_json("/me", {"token": str(token)})
    profile = _api_decode_foto((me or {}).get("profile") or {})
    return profile or None


def _api_get_profesional(token: str | None, prof_id: int, *, include_foto: bool = True) -> dict | None:
    if not token:
        return None
    res = _backend_get_json(
        f"/profesionales/{int(prof_id)}",
        {"token": str(token), "include_foto": "true" if include_foto else "false"},
    )
    item = (res or {}).get("item") or {}
    return _api_decode_foto(item) if include_foto else dict(item)


def _api_list_profesionales(token: str | None, *, texto: str | None, solo_verificados: bool, include_foto: bool) -> list[dict]:
    if not token:
        return []
    params = {
        "token": str(token),
        "solo_verificados": "true" if bool(solo_verificados) else "false",
        "include_foto": "true" if bool(include_foto) else "false",
    }
    if texto:
        params["texto"] = str(texto)
    res = _backend_get_json("/profesionales", params)
    items = (res or {}).get("items") or []
    if not include_foto:
        return [dict(x) for x in items]
    return [_api_decode_foto(dict(x)) for x in items]


def _api_get_contratos(token: str | None, *, include_foto: bool = False) -> list[dict]:
    if not token:
        return []
    res = _backend_get_json(
        "/contratos",
        {"token": str(token), "include_foto": "true" if bool(include_foto) else "false"},
    )
    items = (res or {}).get("items") or []
    if not include_foto:
        return [dict(x) for x in items]
    return [_api_decode_foto(dict(x)) for x in items]


def _href_inicio_prof(prof_id: int, token: str | None, q_buscar: str | None):
    parts = []
    if token:
        parts.append(f"s={quote(str(token))}")
    parts.append("tab=Inicio")
    parts.append(f"prof={quote(str(prof_id))}")
    if q_buscar:
        parts.append(f"q={quote(str(q_buscar))}")
    return "?" + "&".join(parts) + "#detalle-prof"

def _qp_all() -> dict:
    try: return dict(st.query_params)
    except Exception: return st.experimental_get_query_params()

def _qp_get(key: str):
    v = _qp_all().get(key)
    if isinstance(v, (list, tuple)):
        return v[0] if v else None
    return v

def _qp_set(updates: dict):
    params = _qp_all()
    for k, v in updates.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = str(v)
    if updates.get("s"):
        st.session_state.auth_token = str(updates["s"])
    if updates.get("s") is None and "s" in updates:
        st.session_state.auth_token = None
    token = st.session_state.get("auth_token")
    if token and st.session_state.get("logeado") and params.get("s") is None:
        params["s"] = str(token)
    try:
        for k in list(st.query_params.keys()):
            del st.query_params[k]
        for k, v in params.items():
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**params)

def _sync_user_foto(rol: str, usuario_id: int, token: str | None):
    if token:
        try:
            me = _backend_get_json("/me", {"token": str(token)})
            profile = (me or {}).get("profile") or {}
            if profile.get("nombre"):
                st.session_state.nombre_usuario = profile.get("nombre")
            foto_b64 = profile.get("foto_b64")
            if foto_b64:
                st.session_state.foto_usuario = base64.b64decode(foto_b64)
                st.session_state.foto_usuario_mime = profile.get("foto_mime")
            return
        except Exception:
            pass

    if rol == "cliente":
        user = obtener_cliente_por_id(int(usuario_id))
    else:
        user = obtener_profesional_por_id(int(usuario_id))
    if not user:
        return
    if user.get("nombre"):
        st.session_state.nombre_usuario = user.get("nombre")
    st.session_state.foto_usuario = user.get("foto")
    st.session_state.foto_usuario_mime = user.get("foto_mime")

if "db_inicializada" not in st.session_state:
    try:
        crear_tablas_iniciales()
        st.session_state.db_inicializada = True
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")

if "demo_prof_ready" not in st.session_state:
    st.session_state.demo_prof_ready = False

# INICIALIZACIÓN COMPLETA DEL STATE
if "pantalla" not in st.session_state: st.session_state.pantalla = "login"  
if "logeado" not in st.session_state: st.session_state.logeado = False
if "rol" not in st.session_state: st.session_state.rol = None
if "usuario_id" not in st.session_state: st.session_state.usuario_id = None
if "submenu_actual" not in st.session_state: st.session_state.submenu_actual = "Inicio"
if "selected_profesional_id" not in st.session_state: st.session_state.selected_profesional_id = None
if "selected_cliente_chat_id" not in st.session_state: st.session_state.selected_cliente_chat_id = None

tab_q = _qp_get("tab")
if tab_q == "Progreso":
    tab_q = "Mensajes"
elif tab_q == "Configuracion":
    tab_q = "Configuraciones"
if tab_q in {"Inicio", "Mensajes", "Contratos", "Configuraciones", "perfil"}:
    st.session_state.submenu_actual = tab_q

prof_q = _qp_get("prof")
if st.session_state.submenu_actual == "Inicio" and prof_q and str(prof_q).isdigit():
    st.session_state.selected_profesional_id = int(prof_q)

if not st.session_state.logeado:
    token_q = _qp_get("s") or st.session_state.get("auth_token")
    if token_q:
        try:
            me = _backend_get_json("/me", {"token": str(token_q)})
            rol_me = str((me or {}).get("rol") or "")
            user_id_me = int((me or {}).get("user_id") or 0)
            profile = (me or {}).get("profile") or {}

            if rol_me in {"cliente", "profesional"} and user_id_me > 0:
                st.session_state.auth_token = str(token_q)
                st.session_state.logeado = True
                st.session_state.rol = rol_me
                st.session_state.usuario_id = int(user_id_me)
                st.session_state.nombre_usuario = profile.get("nombre")

                foto_b64 = profile.get("foto_b64")
                if foto_b64:
                    try:
                        st.session_state.foto_usuario = base64.b64decode(str(foto_b64))
                    except Exception:
                        st.session_state.foto_usuario = None
                st.session_state.foto_usuario_mime = profile.get("foto_mime")

                if rol_me == "profesional":
                    estado = (profile.get("estado_verificacion") or "pendiente").strip().lower()
                    st.session_state.prof_en_verificacion = estado != "verificado"
                else:
                    st.session_state.prof_en_verificacion = False
        except Exception:
            st.session_state.auth_token = None
            _qp_set({"s": None})


# ==========================================
# USUARIO LOGEADO EN LA APP
# ==========================================
if st.session_state.logeado:
    # Mantener token en la URL para no perder sesión al navegar
    token_sesion = st.session_state.get("auth_token")
    if token_sesion and not _qp_get("s"):
        _qp_set({"s": token_sesion, "tab": st.session_state.submenu_actual or "Inicio"})

    rol = st.session_state.get("rol")
    usuario_id = st.session_state.get("usuario_id")
    nombre_usuario = st.session_state.get("nombre_usuario")

    if usuario_id is None or rol not in {"cliente", "profesional"}:
        st.session_state.logeado = False
        st.session_state.pantalla = "login"
        st.rerun()

    _sync_user_foto(rol, int(usuario_id), st.session_state.get("auth_token"))
    vista = st.session_state.submenu_actual
    en_detalle_prof = (
        vista == "Inicio"
        and rol == "cliente"
        and st.session_state.get("selected_profesional_id") is not None
    )

    en_chat_activo = (
        vista == "Mensajes"
        and (
            (rol == "cliente" and st.session_state.get("selected_profesional_id") is not None)
            or (rol == "profesional" and st.session_state.get("selected_cliente_chat_id") is not None)
        )
    )

    ocultar_nav = (vista in {"perfil", "Configuraciones"}) or bool(en_detalle_prof) or bool(en_chat_activo)
    if not ocultar_nav:
        barra_navegacion_glass()
    else:
        if vista == "perfil" and rol == "profesional":
            st.markdown(
                """
                <style>
                .st-key-mini_settings button{
                    position: fixed !important;
                    top: 26px !important;
                    right: 26px !important;
                    z-index: 100000 !important;
                    width: 52px !important;
                    height: 52px !important;
                    min-width: 52px !important;
                    border-radius: 16px !important;
                    background: #F8FAFC !important;
                    border: 1px solid rgba(15,23,42,.08) !important;
                    box-shadow: 3px 3px 6px #CBD5E1, -2px -2px 5px #FFFFFF !important;
                    font-weight: 900 !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            if st.button("⚙", key="mini_settings", help="Configuraciones"):
                st.session_state.submenu_actual = "Configuraciones"
                _qp_set({"tab": "Configuraciones"})
                st.rerun()

    if vista == "Inicio":
        if rol == "cliente":
            token_sesion = st.session_state.get("auth_token") or _qp_get("s")

            profesional_id = st.session_state.get("selected_profesional_id")
            if profesional_id and token_sesion:
                profesional = _api_get_profesional(token_sesion, int(profesional_id), include_foto=True)
                if profesional:
                    col_back, _ = st.columns([0.25, 0.75])
                    with col_back:
                        if st.button("← Volver", key="volver_listado_prof", use_container_width=True):
                            st.session_state.selected_profesional_id = None
                            _qp_set({"prof": None, "tab": "Inicio"})
                            st.rerun()

                    st.write("---")
                    perfil_profesional_view(profesional)
                    st.stop()

            st.markdown(
                "<h2 style='color: #0F172A; margin-bottom: 0;'>Profesionales disponibles</h2>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Aquí verás los perfiles de profesionales creados. "
                "Los que estén en verificación aparecerán marcados como 'En verificación'."
            )
            
            q_buscar = (_qp_get("q") or st.session_state.get("nav_search") or "").strip()
            try:
                todos_los_profesionales = _api_list_profesionales(
                    token_sesion,
                    texto=(q_buscar or None),
                    solo_verificados=False,
                    include_foto=True,
                )
            except Exception:
                todos_los_profesionales = []

            profs = []
            for p in (todos_los_profesionales or []):
                nombre_p = (p.get("nombre") or "").strip().lower()
                if nombre_p == "andres torres":
                    continue

                if p.get("id") is None:
                    continue
                profs.append(p)

            if profs:
                random.shuffle(profs)
                token_sesion = st.session_state.get("auth_token")

                st.markdown(
                    """
                    <style>
                        .axon-prof-carousel{max-width:980px;margin:10px auto 0;position:relative;overflow:hidden;padding:12px 8px;height:560px}
                        .axon-prof-track{display:flex;flex-direction:column;gap:16px;will-change:transform}
                        .axon-prof-carousel.axon-anim .axon-prof-track{animation:axon-prof-scroll 48s linear infinite}
                        .axon-prof-carousel.axon-anim:hover .axon-prof-track{animation-play-state:paused}
                        @keyframes axon-prof-scroll{0%{transform:translateY(0)}100%{transform:translateY(-50%)}}
                            .axon-prof-card{background:#fff;border-radius:22px;box-shadow:0 16px 40px rgba(15,23,42,.16);display:grid;grid-template-columns:1fr 190px;gap:14px;padding:16px;align-items:center;cursor:pointer;border:1px solid rgba(15,23,42,.08);position:relative}
                            .axon-card-overlay{position:absolute;inset:0;z-index:2;border-radius:22px;display:block}
                        .axon-prof-name{font-weight:800;letter-spacing:.2px;color:#0B1220;font-size:20px;line-height:1.05}
                        .axon-prof-role{color:#334155;font-weight:700;font-size:12.5px;margin-top:3px;text-transform:uppercase}
                        .axon-prof-meta{margin-top:8px;display:flex;gap:10px;flex-wrap:wrap;color:#334155;font-size:12.5px;font-weight:600}
                        .axon-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:#F1F5F9;border:1px solid rgba(15,23,42,.08)}
                        .axon-prof-desc{margin-top:10px;color:#475569;font-size:13px;line-height:1.35;max-width:620px}
                        .axon-prof-tags{margin-top:10px;display:flex;gap:10px;flex-wrap:wrap;color:#0B1220;font-weight:700;font-size:12px}
                        .axon-tag{display:inline-flex;align-items:center;gap:8px}
                        .axon-prof-right{display:flex;flex-direction:column;gap:10px;align-items:flex-end;justify-content:center}
                        .axon-price{color:#0B1220;font-weight:800;font-size:14px;text-align:right}
                        .axon-card-ghost{opacity:.9}
                        @media (max-width: 900px){
                            .axon-prof-carousel{height:640px}
                            .axon-prof-card{grid-template-columns:1fr;grid-template-rows:auto auto}
                            .axon-prof-right{grid-column:1 / -1;flex-direction:row;justify-content:space-between;align-items:center}
                        }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                def _icono_especialidad(esp: str) -> str:
                    e = (esp or "").strip().lower()
                    if "nutri" in e:
                        return "🍏"
                    if "fisio" in e:
                        return "🦴"
                    if "entren" in e:
                        return "🏋️"
                    return "⭐"

                def _resumen(texto: str | None, max_len: int = 130) -> str:
                    t = (texto or "").strip()
                    if not t:
                        return "Perfil profesional en verificación. Revisa su especialidad, experiencia y tarifa para elegir el mejor para ti."
                    if len(t) <= max_len:
                        return t
                    return t[: max_len - 1].rstrip() + "…"

                cards = []
                for prof in profs:
                    pid = int(prof.get("id") or 0)
                    nombre = _h(prof.get("nombre") or "Profesional")
                    esp = prof.get("especialidad") or "Profesional"
                    esp_label = _h(str(esp).upper())
                    exp = prof.get("experiencia")
                    exp_text = f"+{int(exp)} años" if exp is not None else "Experiencia"
                    ciudad = (prof.get("ciudad") or "").strip()
                    depto = (prof.get("departamento") or "").strip()
                    ubicacion = ", ".join([x for x in [ciudad, depto] if x])
                    ubicacion = _h(ubicacion) if ubicacion else "Colombia"
                    tarifa_val = prof.get("tarifa")
                    tarifa_text = f"${float(tarifa_val):,.0f} COP" if tarifa_val is not None else "Tarifa a convenir"
                    desc = _h(_resumen(prof.get("metodologia")))
                    icono = _icono_especialidad(str(esp))
                    href = _href_inicio_prof(pid, token_sesion, q_buscar)

                    estado = (prof.get("estado_verificacion") or "pendiente").strip().lower()
                    meta_badge = "✅ Verificado" if estado == "verificado" else "⏳ En verificación"
                    card_class = "axon-prof-card"
                    cards.append(
                        f"""
                        <div class="{card_class}">
                            <a class="axon-card-overlay" href="{_h(href)}" aria-label="Ver perfil" target="_self"></a>
                            <div class="axon-prof-mid">
                                <div class="axon-prof-name">{nombre}</div>
                                <div class="axon-prof-role">{esp_label}</div>
                                <div class="axon-prof-meta">
                                    <span class="axon-pill">{meta_badge}</span>
                                    <span class="axon-pill">🕒 { _h(exp_text) }</span>
                                    <span class="axon-pill">📍 {ubicacion}</span>
                                </div>
                                <div class="axon-prof-desc">{desc}</div>
                                <div class="axon-prof-tags">
                                    <span class="axon-tag">{_h(icono)} {_h(esp)}</span>
                                </div>
                            </div>
                            <div class="axon-prof-right">
                                <div class="axon-price">💰 { _h(tarifa_text) }</div>
                            </div>
                        </div>
                        """
                    )

                if len(cards) >= 3:
                    track = "\n".join(cards + cards)
                    st.markdown(
                        f"""
                        <div class="axon-prof-carousel axon-anim">
                            <div class="axon-prof-track">
                                {track}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="axon-prof-carousel">
                            <div class="axon-prof-track">
                                {"".join(cards)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                if q_buscar:
                    st.info("No hay profesionales verificados que coincidan con tu búsqueda.")
                else:
                    st.info(
                        "Aún no hay profesionales verificados en el directorio. "
                        "Los nuevos perfiles aparecen cuando el administrador los aprueba."
                    )

        elif rol == "profesional":
            st.title("Panel de Control Profesional")
            st.write(f"Bienvenido de nuevo, {nombre_usuario}")

            col_go_profile, col_spacer = st.columns([1, 3])
            with col_go_profile:
                if st.button("Ver mi perfil", use_container_width=True, key="pro_ir_mi_perfil"):
                    st.session_state.submenu_actual = "perfil"
                    _qp_set({"tab": "perfil"})
                    st.rerun()

            token_sesion = st.session_state.get("auth_token") or _qp_get("s")
            try:
                clientes = _api_get_contratos(token_sesion, include_foto=False)
            except Exception:
                clientes = []

            if not clientes:
                st.info("Todavía no tienes clientes vinculados activos.")
            else:
                st.markdown("### Mis Clientes Activos")
                for c in clientes:
                    with st.container():
                        st.markdown(f"#### {c.get('nombre', 'Cliente')}")
                        if c.get("telefono"):
                            st.write(f"📞 Teléfono: {c.get('telefono')}")
                        st.markdown("---")
        
    elif vista == "Mensajes":
        st.markdown("<h2 style='color:#0F172A;margin-bottom:8px;'>Mensajes</h2>", unsafe_allow_html=True)

        token_chat = st.session_state.get("auth_token") or _qp_get("s")
        if not token_chat:
            st.info("Inicia sesión para ver tus mensajes.")
        else:
            def _fmt_ts(v):
                if not v:
                    return ""
                s = str(v).replace("T", " ")
                return s[:16] if len(s) >= 16 else s

            def _preview(t):
                t = (t or "").strip().replace("\n", " ")
                if len(t) > 56:
                    t = t[:56].rstrip() + "…"
                return t

            def _initials(nombre: str) -> str:
                parts = [p for p in (nombre or "").strip().split() if p]
                return ("".join([p[0] for p in parts[:2]]) or "?").upper()

            st.markdown(
                """
                <style>
                .axon-inbox {max-width: 780px; margin: 0 auto;}
                .axon-inbox a{ text-decoration: none !important; }
                .axon-inbox-item{
                  display:flex; align-items:center; gap:14px;
                  padding: 12px 10px;
                  border-radius: 16px;
                  border: 1px solid rgba(15,23,42,.06);
                  background: rgba(255,255,255,.92);
                  box-shadow: 0 10px 24px rgba(15,23,42,.06);
                }
                .axon-inbox-item:hover{ background: rgba(248,250,252,1); }
                .axon-inbox-avatar{
                  width:56px; height:56px; border-radius:999px; overflow:hidden;
                  display:flex; align-items:center; justify-content:center;
                  background:#e2e8f0;
                  border: 3px solid rgba(148,163,184,.55);
                  flex: 0 0 56px;
                }
                .axon-inbox-item.unread .axon-inbox-avatar{ border-color: rgba(239,68,68,.75); }
                .axon-inbox-avatar img{ width:100%; height:100%; object-fit:cover; display:block; }
                .axon-inbox-avatar .ini{ font-weight:900; color:#0f172a; font-size:18px; }
                .axon-inbox-body{ flex: 1 1 auto; min-width: 0; }
                .axon-inbox-title{ font-weight:900; color:#0f172a; font-size:16px; line-height:1.1; }
                .axon-inbox-sub{ color:#64748b; font-size:13px; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
                .axon-inbox-meta{ flex: 0 0 auto; text-align:right; min-width:72px; }
                .axon-inbox-time{ color:#64748b; font-size:12px; }
                .axon-inbox-badge{
                  display:inline-flex; min-width:22px; height:22px; padding:0 7px;
                  border-radius:999px; background:#ef4444; color:#fff;
                  align-items:center; justify-content:center;
                  font-weight:900; font-size:12px; margin-top:6px;
                }
                .axon-inbox-sep{ height:10px; }

                [class*="st-key-chat_back_inbox_"] button{
                  width: auto !important;
                  padding: 6px 12px !important;
                  min-height: 34px !important;
                  font-size: 13px !important;
                  border-radius: 12px !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            if rol == "cliente":

                def _href_open_prof(prof_id: int) -> str:
                    params = _qp_all()
                    for k in ["prof", "cli", "open_cli"]:
                        params.pop(k, None)
                    params["tab"] = "Mensajes"
                    params["open_prof"] = str(int(prof_id))
                    qs = urlencode({k: v for k, v in params.items() if v is not None})
                    return "?" + qs

                try:
                    inbox = _backend_get_json("/inbox", {"token": str(token_chat), "limit": 60})
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tus conversaciones: {e}")
                    convs = []

                pid = st.session_state.get("selected_profesional_id")
                open_pid = _qp_get("open_prof")
                if pid is None and open_pid:
                    try:
                        st.session_state.selected_profesional_id = int(open_pid)
                        _qp_set({"open_prof": None})
                        st.rerun()
                    except Exception:
                        pass

                pid = st.session_state.get("selected_profesional_id")

                if pid is None:
                    render_inbox_listener(token=str(token_chat), rol="cliente", user_id=int(usuario_id))
                    st.markdown("<div class='axon-inbox'>", unsafe_allow_html=True)
                    if not convs:
                        st.info("Aún no tienes conversaciones.")
                    else:
                        for it in convs:
                            prof_id = int(it.get("profesional_id") or 0)
                            nombre = (it.get("nombre") or "Profesional").strip() or "Profesional"
                            last_texto = _preview(it.get("last_texto"))
                            last_at = _fmt_ts(it.get("last_at"))
                            unread = int(it.get("unread") or 0)

                            prof_row = obtener_profesional_por_id(int(prof_id)) or {}
                            foto = prof_row.get("foto")
                            mime = prof_row.get("foto_mime")
                            src = None
                            if isinstance(foto, (bytes, bytearray)) and foto:
                                try:
                                    b64 = base64.b64encode(bytes(foto)).decode("ascii")
                                    mt = (mime or "image/jpeg").strip() or "image/jpeg"
                                    src = f"data:{mt};base64,{b64}"
                                except Exception:
                                    src = None

                            avatar_html = (
                                f"<img src='{_h(src)}' alt='{_h(nombre)}' />" if src else f"<div class='ini'>{_h(_initials(nombre))}</div>"
                            )
                            badge_html = f"<div class='axon-inbox-badge'>{unread}</div>" if unread > 0 else ""
                            item_cls = "axon-inbox-item unread" if unread > 0 else "axon-inbox-item"

                            st.markdown(
                                f"""
                                <a class="{item_cls}" href="{_h(_href_open_prof(prof_id))}" target="_self" onclick="event.preventDefault(); window.parent.location.href=this.href;">
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
                    pid = int(pid)

                    if st.button("← Volver", key=f"chat_back_inbox_cli_{usuario_id}_{pid}"):
                        st.session_state.selected_profesional_id = None
                        _qp_set({"tab": "Mensajes"})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="cliente",
                        cliente_id=int(usuario_id),
                        profesional_id=int(pid),
                        height=640,
                    )

            else:

                def _href_open_cli(cli_id: int) -> str:
                    params = _qp_all()
                    for k in ["prof", "cli", "open_prof"]:
                        params.pop(k, None)
                    params["tab"] = "Mensajes"
                    params["open_cli"] = str(int(cli_id))
                    qs = urlencode({k: v for k, v in params.items() if v is not None})
                    return "?" + qs

                try:
                    inbox = _backend_get_json("/inbox", {"token": str(token_chat), "limit": 60})
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tus conversaciones: {e}")
                    convs = []

                cid = st.session_state.get("selected_cliente_chat_id")
                open_cid = _qp_get("open_cli")
                if cid is None and open_cid:
                    try:
                        st.session_state.selected_cliente_chat_id = int(open_cid)
                        _qp_set({"open_cli": None})
                        st.rerun()
                    except Exception:
                        pass

                cid = st.session_state.get("selected_cliente_chat_id")

                if cid is None:
                    render_inbox_listener(token=str(token_chat), rol="profesional", user_id=int(usuario_id))
                    st.markdown("<div class='axon-inbox'>", unsafe_allow_html=True)
                    if not convs:
                        st.info("Aún no tienes conversaciones.")
                    else:
                        for it in convs:
                            cli_id = int(it.get("cliente_id") or 0)
                            nombre = (it.get("nombre") or "Cliente").strip() or "Cliente"
                            last_texto = _preview(it.get("last_texto"))
                            last_at = _fmt_ts(it.get("last_at"))
                            unread = int(it.get("unread") or 0)

                            cli_row = obtener_cliente_por_id(int(cli_id)) or {}
                            foto = cli_row.get("foto")
                            mime = cli_row.get("foto_mime")
                            src = None
                            if isinstance(foto, (bytes, bytearray)) and foto:
                                try:
                                    b64 = base64.b64encode(bytes(foto)).decode("ascii")
                                    mt = (mime or "image/jpeg").strip() or "image/jpeg"
                                    src = f"data:{mt};base64,{b64}"
                                except Exception:
                                    src = None

                            avatar_html = (
                                f"<img src='{_h(src)}' alt='{_h(nombre)}' />" if src else f"<div class='ini'>{_h(_initials(nombre))}</div>"
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

                    if st.button("← Volver", key=f"chat_back_inbox_pro_{usuario_id}_{cid}"):
                        st.session_state.selected_cliente_chat_id = None
                        _qp_set({"tab": "Mensajes"})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="profesional",
                        cliente_id=int(cid),
                        profesional_id=int(usuario_id),
                        height=640,
                    )
    elif vista == "Contratos":
        st.markdown("<h2 style='color:white;'>Contratos</h2>", unsafe_allow_html=True)

        token_sesion = st.session_state.get("auth_token") or _qp_get("s")
        try:
            contratos = _api_get_contratos(token_sesion, include_foto=False)
        except Exception:
            contratos = []

        if not contratos:
            st.info("Aún no tienes contratos activos.")
        else:
            for it in contratos:
                with st.container():
                    st.markdown(f"#### {it.get('nombre', 'Usuario')}")
                    if rol == "cliente":
                        esp = it.get("especialidad")
                        if esp:
                            st.write(f"Especialidad: {esp}")
                    monto = it.get("monto")
                    fecha = it.get("fecha")
                    if monto is not None:
                        st.write(f"Monto: {monto}")
                    if fecha:
                        st.write(f"Fecha: {fecha}")
                    st.markdown("---")

    elif vista == "Configuraciones":
        col_back, _ = st.columns([0.25, 0.75])
        with col_back:
            if st.button("← Volver", key=f"cfg_back_{rol}", use_container_width=True):
                st.session_state.submenu_actual = "perfil"
                _qp_set({"tab": "perfil"})
                st.rerun()

        token_sesion = st.session_state.get("auth_token") or _qp_get("s")
        try:
            profile = _api_get_me_profile(token_sesion)
        except Exception:
            profile = None

        if profile:
            with st.expander("Configuración del perfil", expanded=True):
                if rol == "profesional":
                    configuraciones_profesional_view(profile)
                else:
                    configuraciones_cliente_view(profile)

        with st.expander("Cuenta activa", expanded=True):
            st.write(f"Rol: {rol}")
            st.write(f"ID: {usuario_id}")
            st.write(f"Nombre: {nombre_usuario}")
            token_sesion = st.session_state.get("auth_token") or _qp_get("s")
            try:
                prof = _api_get_me_profile(token_sesion) or {}
            except Exception:
                prof = {}
            if prof.get("email"):
                st.write(f"Correo electrónico: {prof.get('email')}")

        with st.expander("Contratos", expanded=False):
            def _fmt_fecha_hora(v):
                if not v:
                    return None
                s = str(v)
                if "T" in s:
                    s = s.replace("T", " ")
                if len(s) >= 19:
                    s = s[:19]
                return s

            token_sesion = st.session_state.get("auth_token") or _qp_get("s")
            try:
                contratos_cfg = _api_get_contratos(token_sesion, include_foto=False)
            except Exception:
                contratos_cfg = []

            if not contratos_cfg:
                st.info("Aún no tienes contratos activos.")
            else:
                for it in contratos_cfg:
                    st.markdown(f"#### {it.get('nombre', 'Usuario')}")
                    if rol == "cliente":
                        esp = it.get("especialidad")
                        if esp:
                            st.write(f"Especialidad: {esp}")
                    monto = it.get("monto")
                    fecha = _fmt_fecha_hora(it.get("fecha"))
                    if monto is not None:
                        st.write(f"Monto: {monto}")
                    if fecha:
                        st.write(f"Fecha y hora: {fecha}")
                    st.markdown("---")

        if "pref_notif_mensajes" not in st.session_state:
            st.session_state.pref_notif_mensajes = True

        with st.expander("Centro de notificaciones", expanded=False):
            st.toggle("Notificaciones de mensajes", key="pref_notif_mensajes")

        with st.expander("Cambio de contraseña", expanded=False):
            st.text_input("Contraseña actual", type="password", key="cfg_pass_old")
            st.text_input("Nueva contraseña", type="password", key="cfg_pass_new")
            st.text_input("Confirmar nueva contraseña", type="password", key="cfg_pass_new2")
            if st.button("Cambiar contraseña", use_container_width=True, key="cfg_change_pass"):
                st.info("Esta función la activamos en la siguiente etapa.")

        if rol == "profesional":
            with st.expander("Membresía", expanded=False):
                st.write("Plan actual: Gratis")
                st.write("Estado: Activa")
                st.button("Ver planes", use_container_width=True, key="cfg_membership_plans")

        with st.expander("Cerrar sesión", expanded=False):
            if st.button("Cerrar sesión", use_container_width=True, key="cfg_logout"):
                token_q = _qp_get("s") or st.session_state.get("auth_token")
                if token_q:
                    try:
                        _backend_post_json("/auth/logout", {"token": str(token_q)}, {})
                    except Exception:
                        pass
                st.session_state.auth_token = None
                _qp_set({"s": None})
                st.session_state.clear()
                st.rerun()

    elif vista == "Progreso":
        st.markdown("<h2 style='color:white;'>Mensajes</h2>", unsafe_allow_html=True)
        token_chat = st.session_state.get("auth_token") or _qp_get("s")
        if not token_chat:
            st.info("Inicia sesión para ver tus mensajes.")
        else:
            if rol == "cliente":
                render_inbox_listener(token=str(token_chat), rol="cliente", user_id=int(usuario_id))

                def _fmt_ts(v):
                    if not v:
                        return ""
                    s = str(v).replace("T", " ")
                    return s[:16] if len(s) >= 16 else s

                def _preview(t):
                    t = (t or "").strip().replace("\n", " ")
                    if len(t) > 56:
                        t = t[:56].rstrip() + "…"
                    return t

                def _initials(nombre: str) -> str:
                    parts = [p for p in (nombre or "").strip().split() if p]
                    ini = ("".join([p[0] for p in parts[:2]]) or "?").upper()
                    return ini

                def _href_open_prof(prof_id: int) -> str:
                    params = _qp_all()
                    for k in ["prof", "cli", "open_cli"]:
                        params.pop(k, None)
                    params["tab"] = "Mensajes"
                    params["open_prof"] = str(int(prof_id))
                    qs = urlencode({k: v for k, v in params.items() if v is not None})
                    return "?" + qs

                try:
                    inbox = _backend_get_json("/inbox", {"token": str(token_chat), "limit": 60})
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tus conversaciones: {e}")
                    convs = []

                pid = st.session_state.get("selected_profesional_id")
                open_pid = _qp_get("open_prof")
                if pid is None and open_pid:
                    try:
                        st.session_state.selected_profesional_id = int(open_pid)
                        _qp_set({"open_prof": None})
                        st.rerun()
                    except Exception:
                        pass

                pid = st.session_state.get("selected_profesional_id")

                if pid is None:
                    st.markdown(
                        """
                        <style>
                        .axon-inbox {max-width: 780px; margin: 0 auto;}
                        .axon-inbox a{ text-decoration: none !important; }
                        .axon-inbox-item{
                          display:flex; align-items:center; gap:14px;
                          padding: 12px 10px;
                          border-radius: 16px;
                          border: 1px solid rgba(15,23,42,.06);
                          background: rgba(255,255,255,.92);
                          box-shadow: 0 10px 24px rgba(15,23,42,.06);
                        }
                        .axon-inbox-item:hover{ background: rgba(248,250,252,1); }
                        .axon-inbox-avatar{
                          width:56px; height:56px; border-radius:999px; overflow:hidden;
                          display:flex; align-items:center; justify-content:center;
                          background:#e2e8f0;
                          border: 3px solid rgba(148,163,184,.55);
                          flex: 0 0 56px;
                        }
                        .axon-inbox-item.unread .axon-inbox-avatar{ border-color: rgba(239,68,68,.75); }
                        .axon-inbox-avatar img{ width:100%; height:100%; object-fit:cover; display:block; }
                        .axon-inbox-avatar .ini{ font-weight:900; color:#0f172a; font-size:18px; }
                        .axon-inbox-body{ flex: 1 1 auto; min-width: 0; }
                        .axon-inbox-title{ font-weight:900; color:#0f172a; font-size:16px; line-height:1.1; }
                        .axon-inbox-sub{ color:#64748b; font-size:13px; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
                        .axon-inbox-meta{ flex: 0 0 auto; text-align:right; min-width:72px; }
                        .axon-inbox-time{ color:#64748b; font-size:12px; }
                        .axon-inbox-badge{
                          display:inline-flex; min-width:22px; height:22px; padding:0 7px;
                          border-radius:999px; background:#ef4444; color:#fff;
                          align-items:center; justify-content:center;
                          font-weight:900; font-size:12px; margin-top:6px;
                        }
                        .axon-inbox-sep{ height:10px; }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div class='axon-inbox'>", unsafe_allow_html=True)
                    if not convs:
                        st.info("Aún no tienes conversaciones.")
                    else:
                        for it in convs:
                            prof_id = int(it.get("profesional_id") or 0)
                            nombre = (it.get("nombre") or "Profesional").strip() or "Profesional"
                            last_texto = _preview(it.get("last_texto"))
                            last_at = _fmt_ts(it.get("last_at"))
                            unread = int(it.get("unread") or 0)

                            prof_row = obtener_profesional_por_id(int(prof_id)) or {}
                            foto = prof_row.get("foto")
                            mime = prof_row.get("foto_mime")
                            src = None
                            if isinstance(foto, (bytes, bytearray)) and foto:
                                try:
                                    b64 = base64.b64encode(bytes(foto)).decode("ascii")
                                    mt = (mime or "image/jpeg").strip() or "image/jpeg"
                                    src = f"data:{mt};base64,{b64}"
                                except Exception:
                                    src = None

                            avatar_html = (
                                f"<img src='{_h(src)}' alt='{_h(nombre)}' />" if src else f"<div class='ini'>{_h(_initials(nombre))}</div>"
                            )
                            badge_html = f"<div class='axon-inbox-badge'>{unread}</div>" if unread > 0 else ""
                            item_cls = "axon-inbox-item unread" if unread > 0 else "axon-inbox-item"

                            st.markdown(
                                f"""
                                <a class="{item_cls}" href="{_h(_href_open_prof(prof_id))}" target="_self" onclick="event.preventDefault(); window.parent.location.href=this.href;">
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
                    pid = int(pid)
                    prof = obtener_profesional_por_id(pid) or {}
                    st.markdown(f"### {prof.get('nombre') or 'Profesional'}")

                    if st.button("← Volver", use_container_width=True, key=f"chat_back_inbox_cli_{usuario_id}_{pid}"):
                        st.session_state.selected_profesional_id = None
                        _qp_set({"tab": "Mensajes"})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="cliente",
                        cliente_id=int(usuario_id),
                        profesional_id=int(pid),
                        height=640,
                    )

            else:
                render_inbox_listener(token=str(token_chat), rol="profesional", user_id=int(usuario_id))

                def _fmt_ts(v):
                    if not v:
                        return ""
                    s = str(v).replace("T", " ")
                    return s[:16] if len(s) >= 16 else s

                def _preview(t):
                    t = (t or "").strip().replace("\n", " ")
                    if len(t) > 56:
                        t = t[:56].rstrip() + "…"
                    return t

                def _initials(nombre: str) -> str:
                    parts = [p for p in (nombre or "").strip().split() if p]
                    ini = ("".join([p[0] for p in parts[:2]]) or "?").upper()
                    return ini

                def _href_open_cli(cli_id: int) -> str:
                    params = _qp_all()
                    for k in ["prof", "cli", "open_prof"]:
                        params.pop(k, None)
                    params["tab"] = "Mensajes"
                    params["open_cli"] = str(int(cli_id))
                    qs = urlencode({k: v for k, v in params.items() if v is not None})
                    return "?" + qs

                try:
                    inbox = _backend_get_json("/inbox", {"token": str(token_chat), "limit": 60})
                    convs = inbox.get("items") or []
                except Exception as e:
                    st.error(f"No se pudo cargar tus conversaciones: {e}")
                    convs = []

                cid = st.session_state.get("selected_cliente_chat_id")
                open_cid = _qp_get("open_cli")
                if cid is None and open_cid:
                    try:
                        st.session_state.selected_cliente_chat_id = int(open_cid)
                        _qp_set({"open_cli": None})
                        st.rerun()
                    except Exception:
                        pass

                cid = st.session_state.get("selected_cliente_chat_id")

                if cid is None:
                    st.markdown(
                        """
                        <style>
                        .axon-inbox {max-width: 780px; margin: 0 auto;}
                        .axon-inbox a{ text-decoration: none !important; }
                        .axon-inbox-item{
                          display:flex; align-items:center; gap:14px;
                          padding: 12px 10px;
                          border-radius: 16px;
                          border: 1px solid rgba(15,23,42,.06);
                          background: rgba(255,255,255,.92);
                          box-shadow: 0 10px 24px rgba(15,23,42,.06);
                        }
                        .axon-inbox-item:hover{ background: rgba(248,250,252,1); }
                        .axon-inbox-avatar{
                          width:56px; height:56px; border-radius:999px; overflow:hidden;
                          display:flex; align-items:center; justify-content:center;
                          background:#e2e8f0;
                          border: 3px solid rgba(148,163,184,.55);
                          flex: 0 0 56px;
                        }
                        .axon-inbox-item.unread .axon-inbox-avatar{ border-color: rgba(239,68,68,.75); }
                        .axon-inbox-avatar img{ width:100%; height:100%; object-fit:cover; display:block; }
                        .axon-inbox-avatar .ini{ font-weight:900; color:#0f172a; font-size:18px; }
                        .axon-inbox-body{ flex: 1 1 auto; min-width: 0; }
                        .axon-inbox-title{ font-weight:900; color:#0f172a; font-size:16px; line-height:1.1; }
                        .axon-inbox-sub{ color:#64748b; font-size:13px; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
                        .axon-inbox-meta{ flex: 0 0 auto; text-align:right; min-width:72px; }
                        .axon-inbox-time{ color:#64748b; font-size:12px; }
                        .axon-inbox-badge{
                          display:inline-flex; min-width:22px; height:22px; padding:0 7px;
                          border-radius:999px; background:#ef4444; color:#fff;
                          align-items:center; justify-content:center;
                          font-weight:900; font-size:12px; margin-top:6px;
                        }
                        .axon-inbox-sep{ height:10px; }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div class='axon-inbox'>", unsafe_allow_html=True)
                    if not convs:
                        st.info("Aún no tienes conversaciones.")
                    else:
                        for it in convs:
                            cli_id = int(it.get("cliente_id") or 0)
                            nombre = (it.get("nombre") or "Cliente").strip() or "Cliente"
                            last_texto = _preview(it.get("last_texto"))
                            last_at = _fmt_ts(it.get("last_at"))
                            unread = int(it.get("unread") or 0)

                            cli_row = obtener_cliente_por_id(int(cli_id)) or {}
                            foto = cli_row.get("foto")
                            mime = cli_row.get("foto_mime")
                            src = None
                            if isinstance(foto, (bytes, bytearray)) and foto:
                                try:
                                    b64 = base64.b64encode(bytes(foto)).decode("ascii")
                                    mt = (mime or "image/jpeg").strip() or "image/jpeg"
                                    src = f"data:{mt};base64,{b64}"
                                except Exception:
                                    src = None

                            avatar_html = (
                                f"<img src='{_h(src)}' alt='{_h(nombre)}' />" if src else f"<div class='ini'>{_h(_initials(nombre))}</div>"
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
                    cliente = obtener_cliente_por_id(cid) or {}
                    cliente_nombre = (cliente.get("nombre") or "Cliente").strip() or "Cliente"
                    st.markdown(f"### {cliente_nombre}")

                    if st.button("← Volver", use_container_width=True, key=f"chat_back_inbox_pro_{usuario_id}_{cid}"):
                        st.session_state.selected_cliente_chat_id = None
                        _qp_set({"tab": "Mensajes"})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="profesional",
                        cliente_id=int(cid),
                        profesional_id=int(usuario_id),
                        height=640,
                    )

    elif vista == "perfil":
        if rol == "cliente":
            col_back, _ = st.columns([0.25, 0.75])
            with col_back:
                if st.button("← Volver", key="perfil_back", use_container_width=True):
                    st.session_state.submenu_actual = "Inicio"
                    if "selected_profesional_id" in st.session_state:
                        st.session_state.selected_profesional_id = None
                    if "selected_cliente_chat_id" in st.session_state:
                        st.session_state.selected_cliente_chat_id = None
                    _qp_set({"tab": "Inicio", "prof": None, "cli": None})
                    st.rerun()

        st.markdown("<h2 style='color:white;'>Mi perfil</h2>", unsafe_allow_html=True)

        token_sesion = st.session_state.get("auth_token") or _qp_get("s")
        try:
            perfil = _api_get_me_profile(token_sesion)
        except Exception:
            perfil = None

        if rol == "cliente":
            if perfil:
                perfil_cliente_view(perfil, mostrar_foto=True)
        elif rol == "profesional":
            if perfil:
                perfil_profesional_view(perfil, owner=True)


# ==========================================
# USUARIO AFUERA (Login / Registro)
# ==========================================
else:
    if st.session_state.pantalla == "login":
        mostrar_interfaz_login()

    elif st.session_state.pantalla == "registro":
        tipo = st.session_state.get("registro_tipo") or "Profesional"
        if tipo == "Profesional": formulario_registro_profesional_ui()
        else: formulario_registro_cliente_ui() 
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Volver a Ingresar", use_container_width=True):
            st.session_state.pantalla = "login"
            st.rerun()

    elif st.session_state.pantalla == "foto_perfil":
        rol = st.session_state.get("rol")
        usuario_id = st.session_state.get("usuario_id")
        nombre = st.session_state.get("nombre_usuario") or "Usuario"

        if rol not in {"cliente", "profesional"} or usuario_id is None:
            st.session_state.pantalla = "login"
            st.rerun()

        st.title("Foto de Perfil")
        st.write(f"Hola, {nombre}. Puedes tomarte o subir una foto. También puedes omitirlo por ahora.")

        tab1, tab2 = st.tabs(["Tomar foto", "Subir foto"])
        foto_file = None
        with tab1:
            foto_file = st.camera_input("Tomar foto", key="foto_perfil_camera")
        with tab2:
            up = st.file_uploader(
                "Subir foto",
                type=["png", "jpg", "jpeg", "webp"],
                key="foto_perfil_upload",
            )
            if up is not None:
                foto_file = up

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Omitir por ahora", use_container_width=True):
                token = st.session_state.get("auth_token") or _qp_get("s")
                if not token:
                    token = crear_sesion(str(rol), int(usuario_id))
                    st.session_state.auth_token = token
                _qp_set({"s": str(token), "tab": "perfil"})
                st.session_state.logeado = True
                st.session_state.pantalla = "login"
                st.session_state.submenu_actual = "perfil"
                if rol == "profesional":
                    st.session_state.prof_en_verificacion = True
                st.rerun()
        with col_b:
            if st.button("Guardar y Continuar", use_container_width=True, disabled=(foto_file is None)):
                try:
                    foto_bytes, foto_mime = _read_image_upload(foto_file)
                except Exception as e:
                    st.error(str(e))
                    st.stop()

                token = st.session_state.get("auth_token") or _qp_get("s")
                if not token:
                    token = crear_sesion(str(rol), int(usuario_id))
                    st.session_state.auth_token = token

                try:
                    _backend_post_json(
                        "/me/foto",
                        {"token": str(token)},
                        {
                            "foto_b64": base64.b64encode(foto_bytes).decode("ascii"),
                            "foto_mime": foto_mime,
                        },
                    )
                except Exception:
                    if rol == "profesional":
                        guardar_foto_profesional(int(usuario_id), foto_bytes, foto_mime)
                    else:
                        guardar_foto_cliente(int(usuario_id), foto_bytes, foto_mime)

                _qp_set({"s": str(token), "tab": "perfil"})
                st.session_state.logeado = True
                st.session_state.pantalla = "login"
                st.session_state.submenu_actual = "perfil"
                if rol == "profesional":
                    st.session_state.prof_en_verificacion = True
                st.rerun()
