import streamlit as st
import streamlit.components.v1 as components
import base64
import html as _html
import random
from urllib.parse import quote

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

def _wa_url(telefono) -> str | None:
    digits = "".join(ch for ch in str(telefono or "") if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("57"):
        num = digits
    elif len(digits) == 10:
        num = "57" + digits
    else:
        num = digits
    return f"https://wa.me/{num}"

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
    try:
        asegurar_profesional_demo()
        st.session_state.demo_prof_ready = True
    except Exception:
        st.session_state.demo_prof_ready = False

# INICIALIZACIÓN COMPLETA DEL STATE
if "pantalla" not in st.session_state: st.session_state.pantalla = "login"  
if "logeado" not in st.session_state: st.session_state.logeado = False
if "rol" not in st.session_state: st.session_state.rol = None
if "usuario_id" not in st.session_state: st.session_state.usuario_id = None
if "submenu_actual" not in st.session_state: st.session_state.submenu_actual = "Inicio"
if "selected_profesional_id" not in st.session_state: st.session_state.selected_profesional_id = None

tab_q = _qp_get("tab")
if tab_q in {"Inicio", "Progreso", "Configuracion", "perfil"}: st.session_state.submenu_actual = tab_q

prof_q = _qp_get("prof")
if prof_q and str(prof_q).isdigit(): st.session_state.selected_profesional_id = int(prof_q)

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
                    tarifa = profesional.get("tarifa")
                    monto = float(tarifa) if tarifa is not None else None
                    if st.button("Contratar a este profesional", use_container_width=True, key="contratar_prof_detalle"):
                        crear_contrato(id_cliente=int(usuario_id), id_profesional=int(profesional_id), monto=monto)
                        st.session_state.selected_profesional_id = None
                        _qp_set({"prof": None, "tab": "Inicio"})
                        st.success("¡Contrato solicitado de manera exitosa!")
                        st.rerun()
                    st.stop()

            st.markdown(
                "<h2 style='color: white; margin-bottom: 0;'>Profesionales disponibles</h2>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Aquí solo verás perfiles de profesionales verificados que ofrecen sus servicios "
                "(entrenamiento, nutrición, fisioterapia, etc.). Usa el buscador de arriba para filtrar."
            )
            
            q_buscar = (_qp_get("q") or st.session_state.get("nav_search") or "").strip()
            try:
                if q_buscar:
                    todos_los_profesionales = buscar_profesionales(texto=q_buscar)
                else:
                    todos_los_profesionales = obtener_todos_los_profesionales()
            except Exception:
                todos_los_profesionales = []

            profs = []
            for p in (todos_los_profesionales or []):
                estado = (p.get("estado_verificacion") or "").strip().lower()
                if estado and estado != "verificado":
                    continue
                if p.get("id") is None:
                    continue
                profs.append(p)

            if not q_buscar:
                profs = profs[:1]

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
                        .axon-wa{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:#0EA5A4;color:#fff;text-decoration:none;border-radius:16px;padding:12px 14px;font-weight:800;font-size:13px;box-shadow:0 10px 22px rgba(14,165,164,.32);width:100%}
                        .axon-wa:hover{filter:brightness(.98)}
                        .axon-card-ghost{opacity:.9}
                        @media (max-width: 900px){
                            .axon-prof-carousel{height:640px}
                            .axon-prof-card{grid-template-columns:78px 1fr;grid-template-rows:auto auto}
                            .axon-prof-right{grid-column:1 / -1;flex-direction:row;justify-content:space-between;align-items:center}
                            .axon-wa{width:auto}
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
                    wa = _wa_url(prof.get("telefono"))
                    wa_html = (
                        f"<a class='axon-wa' href='{_h(wa)}' target='_blank' rel='noopener'>CONTACTAR POR WHATSAPP</a>"
                        if wa
                        else "<div class='axon-wa axon-card-ghost'>CONTACTAR</div>"
                    )
                    meta_badge = "✅ Verificado"
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
                                {wa_html}
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
        
    elif vista == "perfil":
        st.markdown("<h2 style='color:white;'>Mi perfil</h2>", unsafe_allow_html=True)
        st.caption("Toca tu foto en la barra superior para volver aquí. Aquí ves todo lo que registraste.")

        if rol == "cliente":
            cliente = obtener_cliente_por_id(usuario_id)
            if cliente:
                col_avatar, col_form = st.columns([1, 2])
                with col_avatar:
                    foto = cliente.get("foto") or st.session_state.get("foto_usuario")
                    if foto:
                        st.image(foto, caption=nombre_usuario or "Tu foto", width=200)
                    else:
                        st.info("Sin foto aún. Puedes agregarla abajo.")
                with col_form:
                    perfil_cliente_view(cliente, mostrar_foto=False)
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
