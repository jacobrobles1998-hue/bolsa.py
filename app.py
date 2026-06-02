import streamlit as st
import streamlit.components.v1 as components
import base64
import html as _html
import json
import os
import random
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from chat.realtime import render_realtime_chat

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
        html, body, [class*="st-"], p, h1, h2, h3, h4, h5, h6, span, button, input, select, textarea {
            font-family: 'Poppins', sans-serif !important;
        }
    </style>
    """,
)

# IMPORTACIONES
from autenticacion.ingresos import mostrar_interfaz_login
from autenticacion.registro import formulario_registro_profesional_ui, formulario_registro_cliente_ui
from perfiles.profesional import perfil_profesional_view    
from perfiles.cliente import perfil_cliente_view
from basededatos.manejarbasededatos import (
    asegurar_profesional_demo,
    buscar_profesionales,
    crear_contrato,
    crear_sesion,
    crear_tablas_iniciales,
    eliminar_cliente,
    eliminar_profesional,
    eliminar_sesion,
    guardar_foto_cliente,
    guardar_foto_profesional,
    listar_clientes_de_profesional,
    obtener_cliente_por_id,
    obtener_profesional_por_id,
    obtener_sesion,
    obtener_todos_los_profesionales,
)
from estilo.estilocss import css__styles
from interfaz_base import barra_navegacion_glass

st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) 

BACKEND_API_BASE = os.environ.get("AXON_BACKEND_URL", "http://127.0.0.1:8000")


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

def _sync_user_foto(rol: str, usuario_id: int):
    """Carga foto y nombre en sesión para el avatar de la barra."""
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
    tab_q = "Contratos"
if tab_q in {"Inicio", "Mensajes", "Contratos", "perfil"}:
    st.session_state.submenu_actual = tab_q

prof_q = _qp_get("prof")
if st.session_state.submenu_actual == "Inicio" and prof_q and str(prof_q).isdigit():
    st.session_state.selected_profesional_id = int(prof_q)

if not st.session_state.logeado:
    token_q = _qp_get("s") or st.session_state.get("auth_token")
    if token_q:
        ses = obtener_sesion(str(token_q))
        if ses:
            st.session_state.auth_token = str(token_q)
            if ses["rol"] == "profesional":
                user = obtener_profesional_por_id(ses["user_id"])
                estado = (user or {}).get("estado_verificacion")
                st.session_state.logeado = True
                st.session_state.rol = ses["rol"]
                st.session_state.usuario_id = int(ses["user_id"])
                st.session_state.nombre_usuario = (user or {}).get("nombre")
                st.session_state.foto_usuario = (user or {}).get("foto")
                st.session_state.foto_usuario_mime = (user or {}).get("foto_mime")
                st.session_state.auth_token = str(token_q)
                st.session_state.prof_en_verificacion = (
                    (estado or "pendiente").strip().lower() != "verificado"
                )
            else:
                user = obtener_cliente_por_id(ses["user_id"])
                st.session_state.logeado = True
                st.session_state.rol = ses["rol"]
                st.session_state.usuario_id = int(ses["user_id"])
                st.session_state.auth_token = str(token_q)
                if user:
                    st.session_state.nombre_usuario = user.get("nombre")
                    st.session_state.foto_usuario = user.get("foto")
                    st.session_state.foto_usuario_mime = user.get("foto_mime")
        else:
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

    _sync_user_foto(rol, int(usuario_id))
    vista = st.session_state.submenu_actual
    en_detalle_prof = (
        vista == "Inicio"
        and rol == "cliente"
        and st.session_state.get("selected_profesional_id") is not None
    )
    ocultar_nav = en_detalle_prof or (vista == "perfil" and rol == "profesional")
    if not ocultar_nav:
        barra_navegacion_glass()

    if vista == "Inicio":
        if rol == "cliente":
            profesional_id = st.session_state.get("selected_profesional_id")
            if profesional_id:
                profesional = obtener_profesional_por_id(int(profesional_id))
                if profesional:
                    col_back, _ = st.columns([0.25, 0.75])
                    with col_back:
                        if st.button("← Volver", key="volver_listado_prof", use_container_width=True):
                            st.session_state.selected_profesional_id = None
                            _qp_set({"prof": None, "tab": "Inicio"})
                            st.rerun()

                    st.write("---")
                    perfil_profesional_view(profesional)

                    col_c1, col_c2 = st.columns([1.4, 1])
                    with col_c1:
                        if st.button("Contacta al profesional aquí", use_container_width=True, key="contactar_prof_detalle"):
                            st.session_state.selected_profesional_id = int(profesional_id)
                            st.session_state.submenu_actual = "Mensajes"
                            _qp_set({"tab": "Mensajes"})
                            st.rerun()
                    with col_c2:
                        if st.button("Ver contratos", use_container_width=True, key="ver_contratos_desde_detalle"):
                            st.session_state.submenu_actual = "Contratos"
                            _qp_set({"tab": "Contratos"})
                            st.rerun()

                    st.stop()

            st.markdown(
                "<h2 style='color: white; margin-bottom: 0;'>Profesionales disponibles</h2>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Aquí verás los perfiles de profesionales creados. "
                "Los que estén en verificación aparecerán marcados como 'En verificación'."
            )
            
            q_buscar = (_qp_get("q") or st.session_state.get("nav_search") or "").strip()
            try:
                if q_buscar:
                    todos_los_profesionales = buscar_profesionales(texto=q_buscar, solo_verificados=False)
                else:
                    todos_los_profesionales = obtener_todos_los_profesionales(solo_verificados=False)
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
                            .axon-prof-card{background:#fff;border-radius:22px;box-shadow:0 16px 40px rgba(15,23,42,.16);display:grid;grid-template-columns:92px 1fr 190px;gap:14px;padding:16px;align-items:center;cursor:pointer;border:1px solid rgba(15,23,42,.08);position:relative}
                            .axon-card-overlay{position:absolute;inset:0;z-index:2;border-radius:22px;display:block}
                        .axon-prof-left{display:flex;align-items:center;justify-content:center}
                        .axon-prof-avatar{width:78px;height:78px;border-radius:50%;object-fit:cover;border:4px solid #EAB308;box-shadow:0 6px 16px rgba(15,23,42,.18)}
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
                            .axon-prof-card{grid-template-columns:78px 1fr;grid-template-rows:auto auto}
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
                    foto_src = _img_src(prof.get("foto"), prof.get("foto_mime"))
                    href = _href_inicio_prof(pid, token_sesion, q_buscar)

                    estado = (prof.get("estado_verificacion") or "pendiente").strip().lower()
                    meta_badge = "✅ Verificado" if estado == "verificado" else "⏳ En verificación"
                    card_class = "axon-prof-card"
                    cards.append(
                        f"""
                        <div class="{card_class}">
                            <a class="axon-card-overlay" href="{_h(href)}" aria-label="Ver perfil" target="_self"></a>
                            <div class="axon-prof-left">
                                <img class="axon-prof-avatar" src="{_h(foto_src)}" alt="Foto de {nombre}">
                            </div>
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

            clientes = listar_clientes_de_profesional(int(usuario_id))
            if not clientes:
                st.info("Todavía no tienes clientes vinculados activos.")
            else:
                st.markdown("### Mis Clientes Activos")
                for c in clientes:
                    with st.container():
                        st.markdown(f"#### {c.get('nombre', 'Cliente')}")
                        if c.get("telefono"): st.write(f"📞 Teléfono: {c.get('telefono')}")
                        st.markdown("---")
        
    elif vista == "Mensajes":
        st.markdown("<h2 style='color:white;'>Mensajes</h2>", unsafe_allow_html=True)

# aqui inicia los codigos dl chat del cliente

        token_chat = st.session_state.get("auth_token") or _qp_get("s")
        if not token_chat:
            st.info("Inicia sesión para ver tus mensajes.")
        else:
            if rol == "cliente":
                pid = st.session_state.get("selected_profesional_id")

                if pid is None:
                    st.markdown("### Tus conversaciones")
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
                        st.info("Aún no tienes conversaciones. Entra a Inicio y contacta a un profesional.")
                    else:
                        options = []
                        id_map = {}
                        total_unread = 0
                        for r in convs:
                            pid_r = int(r.get("profesional_id") or 0)
                            nombre_r = (r.get("nombre") or "Profesional").strip() or "Profesional"
                            last_at = (r.get("last_at") or "")
                            last_at = last_at.replace("T", " ")[:19] if last_at else ""
                            unread = int(r.get("unread_count") or 0)
                            total_unread += unread
                            label = f"{nombre_r} (ID {pid_r})"
                            if last_at:
                                label = f"{label} • {last_at}"
                            if unread > 0:
                                label = f"🔴 {unread} · {label}"
                            options.append(label)
                            id_map[label] = pid_r

                        if total_unread > 0:
                            st.caption(f"Tienes {total_unread} mensajes sin leer")

                        inbox_key = f"chat_inbox_cli_{usuario_id}"
                        st.selectbox("Selecciona un profesional", options, key=inbox_key)

                        def _open_chat_cli():
                            sel = st.session_state.get(inbox_key)
                            pid_sel = int(id_map.get(sel) or 0)
                            if not pid_sel:
                                return
                            st.session_state.selected_profesional_id = pid_sel
                            _qp_set({"tab": "Mensajes"})

                        st.button("Abrir chat", use_container_width=True, key=f"chat_open_cli_{usuario_id}", on_click=_open_chat_cli)
                else:
                    pid = int(pid)
                    prof = obtener_profesional_por_id(pid) or {}
                    st.markdown(f"### {prof.get('nombre') or 'Profesional'}")

                    tarifa = prof.get("tarifa")
                    monto = float(tarifa) if tarifa is not None else None

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="cliente",
                        cliente_id=int(usuario_id),
                        profesional_id=int(pid),
                        height=640,
                        backend_url=BACKEND_API_BASE,
                    )

                    if st.button("Contratar a este profesional", use_container_width=True, key=f"contratar_prof_mensajes_{usuario_id}_{pid}"):
                        crear_contrato(id_cliente=int(usuario_id), id_profesional=int(pid), monto=monto)
                        st.session_state.submenu_actual = "Contratos"
                        _qp_set({"tab": "Contratos"})
                        st.success("¡Contrato solicitado de manera exitosa!")
                        st.rerun()

            else:
                st.markdown("### Bandeja de mensajes")

                cid = st.session_state.get("selected_cliente_chat_id")

                if cid is None:
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
                        total_unread = 0
                        for r in convs:
                            cid_r = int(r.get("cliente_id") or 0)
                            nombre_r = (r.get("nombre") or "Cliente").strip() or "Cliente"
                            last_at = (r.get("last_at") or "")
                            last_at = last_at.replace("T", " ")[:19] if last_at else ""
                            unread = int(r.get("unread_count") or 0)
                            total_unread += unread
                            label = f"{nombre_r} (ID {cid_r})"
                            if last_at:
                                label = f"{label} • {last_at}"
                            if unread > 0:
                                label = f"🔴 {unread} · {label}"
                            options.append(label)
                            id_map[label] = cid_r
                            name_map[label] = nombre_r

                        if total_unread > 0:
                            st.caption(f"Tienes {total_unread} mensajes sin leer")

                        inbox_key = f"chat_inbox_pro_{usuario_id}"
                        st.selectbox("Selecciona un cliente", options, key=inbox_key)

                        def _open_chat_pro():
                            sel = st.session_state.get(inbox_key)
                            cid_sel = int(id_map.get(sel) or 0)
                            if not cid_sel:
                                return
                            st.session_state.selected_cliente_chat_id = cid_sel
                            _qp_set({"tab": "Mensajes"})

                        st.button(
                            "Abrir chat",
                            use_container_width=True,
                            key=f"chat_open_pro_{usuario_id}",
                            on_click=_open_chat_pro,
                        )
                else:
                    cid = int(cid)
                    cliente = obtener_cliente_por_id(cid) or {}
                    cliente_nombre = (cliente.get("nombre") or "Cliente").strip() or "Cliente"
                    st.markdown(f"### {cliente_nombre}")

                    if st.button("Volver", use_container_width=True, key=f"chat_back_inbox_pro_{usuario_id}_{cid}"):
                        st.session_state.selected_cliente_chat_id = None
                        _qp_set({"tab": "Mensajes"})
                        st.rerun()

                    render_realtime_chat(
                        token=str(token_chat),
                        rol="profesional",
                        cliente_id=int(cid),
                        profesional_id=int(usuario_id),
                        height=640,
                        backend_url=BACKEND_API_BASE,
                    )
    elif vista == "Contratos":
        st.markdown("<h2 style='color:white;'>Contratos</h2>", unsafe_allow_html=True)

        if rol == "profesional":
            contratos = listar_clientes_de_profesional(int(usuario_id))
            if not contratos:
                st.info("Aún no tienes contratos activos.")
            else:
                for c in contratos:
                    with st.container():
                        st.markdown(f"#### {c.get('nombre', 'Cliente')}")
                        monto = c.get("monto")
                        fecha = c.get("fecha")
                        if monto is not None:
                            st.write(f"Monto: {monto}")
                        if fecha:
                            st.write(f"Fecha: {fecha}")
                        st.markdown("---")
        else:
            from basededatos.manejarbasededatos import listar_profesionales_de_cliente

            contratos = listar_profesionales_de_cliente(int(usuario_id))
            if not contratos:
                st.info("Aún no tienes contratos activos.")
            else:
                for p in contratos:
                    with st.container():
                        st.markdown(f"#### {p.get('nombre', 'Profesional')}")
                        esp = p.get("especialidad")
                        if esp:
                            st.write(f"Especialidad: {esp}")
                        monto = p.get("monto")
                        fecha = p.get("fecha")
                        if monto is not None:
                            st.write(f"Monto: {monto}")
                        if fecha:
                            st.write(f"Fecha: {fecha}")
                        st.markdown("---")

    elif vista == "Progreso":
        st.markdown("<h2 style='color:white;'>Mensajes</h2>", unsafe_allow_html=True)
        token_chat = st.session_state.get("auth_token") or _qp_get("s")
        if not token_chat:
            st.info("Inicia sesión para ver tus mensajes.")
        else:
            if rol == "cliente":
                pid = st.session_state.get("selected_profesional_id")
                if pid is None:
                    st.info("Entra a Inicio, abre un profesional y pulsa 'Contacta al profesional aquí'.")
                else:
                    pid = int(pid)
                    prof = obtener_profesional_por_id(pid) or {}
                    st.markdown(f"### {prof.get('nombre') or 'Profesional'}")

                    col_r1, col_r2 = st.columns([1, 1])
                    with col_r2:
                        if st.button("Actualizar", use_container_width=True, key=f"chat_refresh_cli_{usuario_id}_{pid}"):
                            st.rerun()

                    try:
                        resp = _backend_get_json(
                            "/messages",
                            {"token": str(token_chat), "profesional_id": pid, "limit": 80},
                        )
                        items = resp.get("items") or []
                    except Exception as e:
                        st.error(f"No se pudo cargar el chat: {e}")
                        items = []

                    if items:
                        for m in items:
                            sender_rol = (m.get("sender_rol") or "").strip().lower()
                            sender_id = int(m.get("sender_id") or 0)
                            yo = sender_rol == "cliente" and sender_id == int(usuario_id)
                            who = "Tú" if yo else (prof.get("nombre") or "Profesional")
                            ts = (m.get("created_at") or "")
                            ts = ts.replace("T", " ")[:19] if ts else ""
                            texto = m.get("texto") or ""
                            st.write(f"{who} {f'[{ts}]' if ts else ''}: {texto}")
                    else:
                        st.info("Aún no hay mensajes.")

                    msg_key = f"chat_msg_cli_{usuario_id}_{pid}"
                    st.text_area("Escribe tu mensaje", key=msg_key, height=90)
                    col_s1, col_s2 = st.columns([1, 1])
                    with col_s1:
                        if st.button("Enviar", use_container_width=True, key=f"chat_send_cli_{usuario_id}_{pid}"):
                            texto = (st.session_state.get(msg_key) or "").strip()
                            if not texto:
                                st.warning("Escribe un mensaje.")
                            else:
                                try:
                                    _backend_post_json(
                                        "/messages",
                                        {"token": str(token_chat)},
                                        {"profesional_id": pid, "texto": texto},
                                    )
                                except Exception as e:
                                    st.error(f"No se pudo enviar el mensaje: {e}")
                                else:
                                    st.session_state[msg_key] = ""
                                    st.rerun()
                    with col_s2:
                        if st.button("Ir a Inicio", use_container_width=True, key=f"chat_back_inicio_cli_{usuario_id}_{pid}"):
                            st.session_state.submenu_actual = "Inicio"
                            _qp_set({"tab": "Inicio"})
                            st.rerun()

            else:
                st.markdown("### Bandeja de clientes")
                clientes = listar_clientes_de_profesional(int(usuario_id))
                if not clientes:
                    st.info("Aún no tienes clientes con contrato activo.")
                else:
                    options = []
                    id_map = {}
                    for c in clientes:
                        cid = int(c.get("id") or 0)
                        label = f"{c.get('nombre') or 'Cliente'} (ID {cid})"
                        options.append(label)
                        id_map[label] = cid

                    sel = st.selectbox("Selecciona un cliente", options, key=f"chat_sel_cli_{usuario_id}")
                    cid = int(id_map.get(sel) or 0)

                    col_r1, col_r2 = st.columns([1, 1])
                    with col_r2:
                        if st.button("Actualizar", use_container_width=True, key=f"chat_refresh_pro_{usuario_id}_{cid}"):
                            st.rerun()

                    try:
                        resp = _backend_get_json(
                            "/messages",
                            {"token": str(token_chat), "cliente_id": cid, "limit": 80},
                        )
                        items = resp.get("items") or []
                    except Exception as e:
                        st.error(f"No se pudo cargar el chat: {e}")
                        items = []

                    if items:
                        for m in items:
                            sender_rol = (m.get("sender_rol") or "").strip().lower()
                            sender_id = int(m.get("sender_id") or 0)
                            yo = sender_rol == "profesional" and sender_id == int(usuario_id)
                            who = "Tú" if yo else (sel.split("(", 1)[0].strip() or "Cliente")
                            ts = (m.get("created_at") or "")
                            ts = ts.replace("T", " ")[:19] if ts else ""
                            texto = m.get("texto") or ""
                            st.write(f"{who} {f'[{ts}]' if ts else ''}: {texto}")
                    else:
                        st.info("Aún no hay mensajes.")

                    msg_key = f"chat_msg_pro_{usuario_id}_{cid}"
                    st.text_area("Escribe tu mensaje", key=msg_key, height=90)
                    if st.button("Enviar", use_container_width=True, key=f"chat_send_pro_{usuario_id}_{cid}"):
                        texto = (st.session_state.get(msg_key) or "").strip()
                        if not texto:
                            st.warning("Escribe un mensaje.")
                        else:
                            try:
                                _backend_post_json(
                                    "/messages",
                                    {"token": str(token_chat)},
                                    {"cliente_id": cid, "texto": texto},
                                )
                            except Exception as e:
                                st.error(f"No se pudo enviar el mensaje: {e}")
                            else:
                                st.session_state[msg_key] = ""
                                st.rerun()

    elif vista == "perfil":
        st.markdown("<h2 style='color:white;'>Mi perfil</h2>", unsafe_allow_html=True)
        st.caption("Toca tu foto en la barra superior para volver aquí. Aquí ves todo lo que registraste.")

        with st.expander("Cuenta activa", expanded=False):
            st.write(f"Rol: {rol}")
            st.write(f"ID: {usuario_id}")
            st.write(f"Nombre: {nombre_usuario}")
            token_dbg = st.session_state.get("auth_token") or _qp_get("s")
            if token_dbg:
                st.write(f"Sesión: {token_dbg}")
            user_dbg = None
            if rol == "cliente":
                user_dbg = obtener_cliente_por_id(int(usuario_id))
            elif rol == "profesional":
                user_dbg = obtener_profesional_por_id(int(usuario_id))
            if user_dbg and user_dbg.get("email"):
                st.write(f"Email: {user_dbg.get('email')}")

        if rol == "cliente":
            cliente = obtener_cliente_por_id(usuario_id)
            if cliente:
                foto_ss = st.session_state.get("foto_usuario")
                mime_ss = st.session_state.get("foto_usuario_mime")
                if (not cliente.get("foto")) and foto_ss:
                    cliente = dict(cliente)
                    cliente["foto"] = foto_ss
                    if mime_ss and not cliente.get("foto_mime"):
                        cliente["foto_mime"] = mime_ss

                perfil_cliente_view(cliente, mostrar_foto=True)
        elif rol == "profesional":
            profesional = obtener_profesional_por_id(usuario_id)
            if profesional:
                perfil_profesional_view(profesional, editable=True)

        st.markdown("---")
        with st.expander("Actualizar foto de perfil", expanded=False):
            tab1 = st.tabs(["Subir foto"])[0]
            foto_file = None
            with tab1:
                up = st.file_uploader(
                    "Subir foto",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="ajustes_foto_upload",
                )
                if up is not None:
                    foto_file = up

            if st.button("Guardar foto", use_container_width=True, disabled=(foto_file is None)):
                foto_bytes = foto_file.getvalue()
                foto_mime = getattr(foto_file, "type", None)
                if rol == "profesional":
                    guardar_foto_profesional(int(usuario_id), foto_bytes, foto_mime)
                else:
                    guardar_foto_cliente(int(usuario_id), foto_bytes, foto_mime)
                st.session_state.foto_usuario = foto_bytes
                st.session_state.foto_usuario_mime = foto_mime
                st.success("Foto de perfil actualizada correctamente.")
                st.rerun()

        st.write("<br>", unsafe_allow_html=True)
        if st.button("Cerrar sesión", use_container_width=True):
            token_q = _qp_get("s") or st.session_state.get("auth_token")
            if token_q:
                eliminar_sesion(str(token_q))
            st.session_state.auth_token = None
            _qp_set({"s": None})
            st.session_state.clear()
            st.rerun()

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
                token = crear_sesion(str(rol), int(usuario_id))
                st.session_state.auth_token = token
                _qp_set({"s": token, "tab": "perfil"})
                st.session_state.logeado = True
                st.session_state.pantalla = "login"
                st.session_state.submenu_actual = "perfil"
                if rol == "profesional":
                    st.session_state.prof_en_verificacion = True
                st.rerun()
        with col_b:
            if st.button("Guardar y Continuar", use_container_width=True, disabled=(foto_file is None)):
                foto_bytes = foto_file.getvalue() if foto_file is not None else None
                foto_mime = getattr(foto_file, "type", None)
                if foto_bytes:
                    if rol == "profesional":
                        guardar_foto_profesional(int(usuario_id), foto_bytes, foto_mime)
                    else:
                        guardar_foto_cliente(int(usuario_id), foto_bytes, foto_mime)

                token = crear_sesion(str(rol), int(usuario_id))
                st.session_state.auth_token = token
                _qp_set({"s": token, "tab": "perfil"})
                st.session_state.logeado = True
                st.session_state.pantalla = "login"
                st.session_state.submenu_actual = "perfil"
                if rol == "profesional":
                    st.session_state.prof_en_verificacion = True
                st.rerun()
