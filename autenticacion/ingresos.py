import streamlit as st
from pathlib import Path

from api_cliente import backend_post_json as _backend_post_json

_ESTILO_DIR = Path(__file__).resolve().parents[1] / "estilo"


def _leer_estilo_archivo(nombre_archivo: str) -> str:
    try:
        return (_ESTILO_DIR / nombre_archivo).read_text(encoding="utf-8")
    except Exception:
        return ""


def _procesar_login(correo: str, password: str) -> bool:
    correo = (correo or "").strip().lower()
    try:
        res = _backend_post_json(
            "/auth/login",
            None,
            {"email": correo, "password": password or ""},
        )
    except Exception as e:
        st.error(str(e))
        return False

    if not (res or {}).get("ok"):
        st.error("Usuario o contraseña incorrectos")
        return False

    rol = str(res.get("rol") or "")
    user_id = int(res.get("user_id") or 0)
    token = str(res.get("token") or "")
    profile = (res or {}).get("profile") or {}

    st.session_state.auth_token = token
    st.session_state.logeado = True
    st.session_state.rol = rol
    st.session_state.usuario_id = user_id
    st.session_state.nombre_usuario = profile.get("nombre")
    st.session_state.foto_usuario = None
    st.session_state.foto_usuario_mime = profile.get("foto_mime")

    if rol == "profesional":
        st.session_state.prof_en_verificacion = bool(res.get("prof_en_verificacion"))
        st.session_state.submenu_actual = "perfil" if st.session_state.prof_en_verificacion else "Inicio"
    else:
        st.session_state.prof_en_verificacion = False
        st.session_state.submenu_actual = "Inicio"

    st.session_state.pantalla = "login"
    st.rerun()


def mostrar_interfaz_login():
    """Login neumórfico (referencia Pinterest) + botones de registro."""
    login_css = _leer_estilo_archivo("neumorfico.css")
    if login_css:
        st.markdown(f"<style>{login_css}</style>", unsafe_allow_html=True)
    st.markdown('<div class="axon-login-marker"></div>', unsafe_allow_html=True)

    st.markdown('<div class="axon-login-shell">', unsafe_allow_html=True)

    with st.form("form_login", clear_on_submit=False):
        panel_html = _leer_estilo_archivo("panel.html")
        if panel_html:
            st.markdown(panel_html, unsafe_allow_html=True)
        correo = st.text_input(
            "Correo electrónico",
            key="login_email",
            placeholder="correo@ejemplo.com",
            label_visibility="collapsed",
        )
        password = st.text_input(
            "Contraseña",
            type="password",
            key="login_pass",
            placeholder="password",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Login", use_container_width=True, key="login_submit")

    if submitted:
        _procesar_login(correo, password)

    st.markdown('<div class="axon-registro-zone">', unsafe_allow_html=True)
    col_reg_1, col_reg_2 = st.columns(2)
    with col_reg_1:
        if st.button(
            "Registrarse como Profesional",
            use_container_width=True,
            key="btn_reg_prof_login",
        ):
            st.session_state.registro_tipo = "Profesional"
            st.session_state.pantalla = "registro"
            st.rerun()
    with col_reg_2:
        if st.button(
            "Registrarse como Cliente",
            use_container_width=True,
            key="btn_reg_cli_login",
        ):
            st.session_state.registro_tipo = "Cliente"
            st.session_state.pantalla = "registro"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
