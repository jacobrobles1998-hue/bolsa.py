import streamlit as st
import streamlit.components.v1 as components
import random

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

def _qp_all() -> dict:
    try: return dict(st.query_params)
    except Exception: return st.experimental_get_query_params()

def _qp_get(key: str):
    return _qp_all().get(key)

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
                if (estado or "pendiente").strip().lower() != "verificado":
                    eliminar_sesion(str(token_q))
                    _qp_set({"s": None})
                    st.warning("Tu perfil profesional está en verificación.")
                else:
                    st.session_state.logeado = True
                    st.session_state.rol = ses["rol"]
                    st.session_state.usuario_id = int(ses["user_id"])
                    st.session_state.nombre_usuario = (user or {}).get("nombre")
                    st.session_state.foto_usuario = (user or {}).get("foto")
                    st.session_state.foto_usuario_mime = (user or {}).get("foto_mime")
                    st.session_state.auth_token = str(token_q)
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
    barra_navegacion_glass()
    vista = st.session_state.submenu_actual

    if vista == "Inicio":
        if rol == "cliente":
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

            if todos_los_profesionales:
                random.shuffle(todos_los_profesionales)
                for prof in todos_los_profesionales:
                    with st.container():
                        esp_label = str(prof.get('especialidad', 'Profesional')).upper()
                        tarifa_val = prof.get('tarifa')
                        tarifa_text = f"| 💰 Tarifa: ${float(tarifa_val):,.0f}" if tarifa_val else ""
                        
                        st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #00F0FF;'>
                            <h4 style='color: white; margin: 0;'>{prof.get('nombre', 'Profesional')}</h4>
                            <p style='color: #00F0FF; margin: 5px 0; font-weight: bold; font-size: 14px;'>✨ {esp_label}</p>
                            <p style='color: #ccc; margin: 5px 0;'>📍 {prof.get('ciudad', '')}, {prof.get('departamento', '')} {tarifa_text}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Ver perfil detallado", key=f"btn_global_{prof.get('id')}", use_container_width=True):
                            st.session_state.selected_profesional_id = prof.get('id')
                            st.rerun()
            else:
                if q_buscar:
                    st.info("No hay profesionales verificados que coincidan con tu búsqueda.")
                else:
                    st.info(
                        "Aún no hay profesionales verificados en el directorio. "
                        "Los nuevos perfiles aparecen cuando el administrador los aprueba."
                    )

            profesional_id = st.session_state.get("selected_profesional_id")
            if profesional_id:
                profesional = obtener_profesional_por_id(profesional_id)
                if profesional:
                    st.write("---")
                    perfil_profesional_view(profesional)
                    tarifa = profesional.get("tarifa")
                    monto = float(tarifa) if tarifa is not None else None
                    if st.button("Contratar a este profesional", use_container_width=True):
                        crear_contrato(id_cliente=int(usuario_id), id_profesional=int(profesional_id), monto=monto)
                        st.session_state.selected_profesional_id = None
                        _qp_set({"prof": None})
                        st.success("¡Contrato solicitado de manera exitosa!")
                        st.rerun()
                        
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
                perfil_profesional_view(profesional)

        st.markdown("---")
        with st.expander("Actualizar foto de perfil", expanded=False):
            tab1, tab2 = st.tabs(["Tomar foto", "Subir foto"])
            foto_file = None
            with tab1: foto_file = st.camera_input("Tomar foto", key="ajustes_foto_camera")
            with tab2:
                up = st.file_uploader("Subir foto", type=["png", "jpg", "jpeg", "webp"], key="ajustes_foto_upload")
                if up is not None: foto_file = up

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
            if rol != "profesional":
                if st.button("Omitir por ahora", use_container_width=True):
                    token = crear_sesion(str(rol), int(usuario_id))
                    st.session_state.auth_token = token
                    _qp_set({"s": token, "tab": _qp_get("tab") or "Inicio"})
                    st.session_state.logeado = True
                    st.session_state.pantalla = "login"
                    st.rerun()
            else:
                st.caption("La foto es obligatoria para verificación.")
        with col_b:
            if st.button("Guardar y Continuar", use_container_width=True, disabled=(foto_file is None)):
                foto_bytes = foto_file.getvalue() if foto_file is not None else None
                foto_mime = getattr(foto_file, "type", None)
                if foto_bytes:
                    if rol == "profesional":
                        guardar_foto_profesional(int(usuario_id), foto_bytes, foto_mime)
                    else:
                        guardar_foto_cliente(int(usuario_id), foto_bytes, foto_mime)
                if rol == "profesional":
                    st.session_state.logeado = False
                    st.session_state.pantalla = "login"
                    st.session_state.rol = None
                    st.session_state.usuario_id = None
                    st.session_state.nombre_usuario = None
                    st.success(
                        "Foto guardada. Tu perfil quedó en verificación; cuando sea aprobado podrás iniciar sesión."
                    )
                    st.rerun()
                else:
                    token = crear_sesion(str(rol), int(usuario_id))
                    st.session_state.auth_token = token
                    _qp_set({"s": token, "tab": _qp_get("tab") or "Inicio"})
                    st.session_state.logeado = True
                    st.session_state.pantalla = "login"
                    st.rerun()
