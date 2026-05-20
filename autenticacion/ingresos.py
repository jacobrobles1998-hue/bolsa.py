import streamlit as st
from basededatos.manejarbasededatos import autenticar_usuario, crear_sesion

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
    for k, v in updates.items():
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

def mostrar_interfaz_login():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

        .axon-neumorfico,
        .axon-neumorfico * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }

        .axon-neumorfico {
            background-color: #E3EDF7;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 88vh;
            padding: 24px 16px;
        }

        .axon-neumorfico .login-container {
            background-color: #E3EDF7;
            width: 420px;
            padding: 54px 46px 34px;
            border-radius: 28px;
            text-align: center;
            box-shadow: 14px 14px 28px rgba(163, 177, 198, 0.55),
                        -14px -14px 28px rgba(255, 255, 255, 0.9);
        }

        .axon-neumorfico .logo-circle {
            background-color: #0B1220;
            width: 104px;
            height: 104px;
            border-radius: 50%;
            margin: 0 auto 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            border: 6px solid #E3EDF7;
            box-shadow: 8px 8px 16px rgba(163, 177, 198, 0.55),
                        -8px -8px 16px rgba(255, 255, 255, 0.9);
        }

        .axon-neumorfico .webdev-logo {
            display: flex;
            flex-direction: column;
            color: white;
            font-size: 8px;
            position: relative;
            line-height: 1;
        }

        .axon-neumorfico .lt,
        .axon-neumorfico .gt {
            font-size: 30px;
            font-weight: bold;
        }
        .axon-neumorfico .lt { color: #fff; position: absolute; left: -18px; top: 0px; }
        .axon-neumorfico .gt { color: #50e3c2; position: absolute; right: -18px; top: 0px; }
        .axon-neumorfico .made { font-weight: bold; letter-spacing: 0.5px; }
        .axon-neumorfico .easy { font-weight: 300; }

        .axon-neumorfico .title {
            font-size: 1.6rem;
            color: #0F172A;
            font-weight: 700;
            margin: 8px 0 0 0;
        }

        .axon-neumorfico .subtitle {
            color: #475569;
            font-size: 0.95rem;
            font-weight: 500;
            margin: 6px 0 30px 0;
        }

        .axon-neumorfico .input-group {
            background-color: #E3EDF7;
            width: 100%;
            height: 60px;
            border-radius: 30px;
            margin-bottom: 22px;
            display: flex;
            align-items: center;
            padding: 0 25px;
            box-shadow: inset 10px 10px 20px rgba(163, 177, 198, 0.55),
                        inset -10px -10px 20px rgba(255, 255, 255, 0.9);
        }

        .axon-neumorfico .input-group i {
            color: #94A3B8;
            font-size: 1.2rem;
            margin-right: 15px;
        }

        .axon-neumorfico .input-group [data-testid="stTextInput"] {
            margin: 0;
            flex: 1;
        }

        .axon-neumorfico .input-group [data-testid="stTextInput"] > div {
            width: 100%;
        }

        .axon-neumorfico .input-group input {
            border: none !important;
            background: transparent !important;
            outline: none !important;
            color: #555 !important;
            font-size: 1rem !important;
            width: 100% !important;
            height: 42px !important;
            box-shadow: none !important;
        }

        .axon-neumorfico .input-group input::placeholder {
            color: #999 !important;
            font-weight: 300 !important;
        }

        .axon-neumorfico .login-container [data-testid="stFormSubmitButton"] button {
            background-color: #52B7D3;
            color: white;
            width: 100%;
            height: 60px;
            border-radius: 30px;
            border: none;
            outline: none;
            cursor: pointer;
            font-size: 1.05rem;
            font-weight: 700;
            margin-top: 10px;
            box-shadow: 12px 12px 20px rgba(163, 177, 198, 0.55),
                        -12px -12px 20px rgba(255, 255, 255, 0.9);
            transition: background 0.3s ease;
        }

        .axon-neumorfico .login-container [data-testid="stFormSubmitButton"] button:hover {
            background-color: #3AAECF;
        }

        .axon-neumorfico .links {
            margin-top: 22px;
            font-size: 0.9rem;
            color: #64748B;
        }

        .axon-neumorfico .links .stButton > button {
            background: transparent !important;
            box-shadow: none !important;
            height: auto !important;
            padding: 0 !important;
            border: none !important;
            color: #64748B !important;
            font-weight: 600 !important;
        }

        .axon-neumorfico .links .stButton > button:hover {
            text-decoration: underline;
        }

        .axon-neumorfico .links .signup .stButton > button {
            color: #0F172A !important;
            font-weight: 800 !important;
        }

        @media (max-width: 480px) {
            .axon-neumorfico .login-container {
                width: 100%;
                padding: 44px 18px 30px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="axon-neumorfico">', unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="logo-circle">
            <div class="webdev-logo">
                <span class="lt">&lt;</span>
                <span class="gt">&gt;</span>
                <span class="made">Web Dev</span>
                <span class="easy">made easy!</span>
            </div>
        </div>
        <div class="title">Web Development</div>
        <div class="subtitle">Made easy!</div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_login"):
        st.markdown(
            """
            <div class="input-group">
                <i class="far fa-user"></i>
            """,
            unsafe_allow_html=True,
        )
        telefono = st.text_input(
            "Teléfono",
            key="login_tel",
            placeholder="3101234567",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="input-group">
                <i class="fas fa-lock"></i>
            """,
            unsafe_allow_html=True,
        )
        password = st.text_input(
            "Contraseña",
            type="password",
            key="login_pass",
            placeholder="password",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        auth = autenticar_usuario(telefono, password)
        if auth is None:
            st.error("Usuario o contraseña incorrectos")
        else:
            if auth.get("rol") == "profesional":
                estado = (auth.get("estado_verificacion") or "pendiente").strip().lower()
                if estado != "verificado":
                    st.warning("Tu perfil profesional está en verificación. Cuando sea aprobado podrás iniciar sesión.")
                    return
            st.session_state.logeado = True
            st.session_state.pantalla = "login"
            st.session_state.rol = auth["rol"]
            st.session_state.usuario_id = auth["id"]
            st.session_state.nombre_usuario = auth["nombre"]
            st.session_state.email_usuario = None
            token = crear_sesion(auth["rol"], auth["id"])
            _qp_set({"s": token, "tab": _qp_all().get("tab") or "Inicio"})
            st.rerun()

    st.markdown('<div class="links">', unsafe_allow_html=True)
    col_forgot, col_or, col_signup = st.columns([2.5, 0.7, 1.4])
    with col_forgot:
        if st.button("Forgot password?"):
            st.info("Función en desarrollo. Contacta al administrador de AXON.")
    with col_or:
        st.markdown("<div style='padding-top: 8px; text-align:center;'>or</div>", unsafe_allow_html=True)
    with col_signup:
        st.markdown('<div class="signup">', unsafe_allow_html=True)
        if st.button("Sign Up"):
            st.session_state.pantalla = "registro"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_interfaz_registro():
    st.subheader("Registro de Usuario")
