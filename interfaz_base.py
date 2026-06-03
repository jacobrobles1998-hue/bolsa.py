# interfaz_base.py
# interfaz_base.py
import streamlit as st
import base64

from chat.realtime import render_nav_badge_listener

def barra_navegacion_glass():
    """
    Renderiza una barra de navegación premium basada en la referencia del usuario.
    Estilo Neumorfismo 3D con extrusión, chasis contenedor flotante y sombras profundas.
    """
    
    # 🎨 INYECCIÓN DE CSS AVANZADO - UNIFICACIÓN DE CHASIS Y EFECTO FLOTANTE
    st.markdown(
        """
        <style>
        /* 1. EL CHASIS CONTENEDOR (Esto es lo que le da el aspecto de flotar en el aire) */
        .premium-nav-container {
            position: fixed;
            top: 25px;
            left: 5%;
            width: 90%;
            background-color: #F0F2F5 !important; /* Color gris claro idéntico a la foto base */
            border-radius: 28px !important; /* Bordes ultra suavizados */
            padding: 12px 24px !important;
            z-index: 99999 !important;
            
            /* 🚀 SISTEMA DE SOMBRAS COMBINADAS (Simula la distancia real con el fondo) */
            box-shadow: 
                0px 20px 40px rgba(165, 175, 191, 0.45), 
                0px 8px 16px rgba(0, 0, 0, 0.04),
                inset 1px 1px 0px rgba(255, 255, 255, 0.8) !important;
            
            display: flex;
            align-items: center;
            border: 1px solid rgba(226, 232, 240, 0.8) !important;
        }

        /* Espaciado del cuerpo de la app para que la barra no pise los datos */
        .block-container {
            padding-top: 130px !important;
        }

        /* Pestaña seleccionada: Inicio (antracita, como en la barra) */
        .active-inicio > div > button {
            background: #2D3139 !important; /* Gris oscuro idéntico a la foto */
            color: #FFFFFF !important;
            border: 1px solid #1E2229 !important;
            box-shadow: 
                inset 2px 2px 5px rgba(0,0,0,0.4), 
                2px 4px 6px rgba(0,0,0,0.08) !important;
        }
        .active-inicio > div > button:hover {
            color: #FFFFFF !important;
            background: #2D3139 !important;
        }

        /* Pestaña seleccionada con resplandor (Mensajes / Contratos) */
        .active-glow > div > button {
            background: #F8FAFC !important;
            color: #0F172A !important;
            border: 1px solid #FFFFFF !important;
            /* El resplandor ámbar/oro de tu referencia */
            box-shadow: 
                0px 8px 20px rgba(245, 158, 11, 0.35), 
                3px 3px 6px #CBD5E1, 
                -3px -3px 6px #FFFFFF !important;
        }

        /* Cajón del buscador hundido (Inundado/Neumorfismo cóncavo) */
        .search-container-premium {
            background: #E2E8F0 !important;
            border-radius: 16px !important;
            padding: 6px 16px !important;
            box-shadow: 
                inset 2px 2px 5px #CBD5E1, 
                inset -2px -2px 5px #FFFFFF !important;
            color: #64748B;
            font-size: 13px;
            display: flex;
            align-items: center;
            height: 40px;
            margin-top: 2px;
            border: 1px solid rgba(255,255,255,0.5);
        }

        div[data-testid="stTextInput"]:has(input[aria-label="BUSCADOR_NAV"]) {
            margin-top: 2px;
        }

        input[aria-label="BUSCADOR_NAV"] {
            background: #E2E8F0 !important;
            border-radius: 16px !important;
            height: 40px !important;
            padding: 8px 14px !important;
            box-shadow: inset 2px 2px 5px #CBD5E1, inset -2px -2px 5px #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.5) !important;
            color: #334155 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }

        input[aria-label="BUSCADOR_NAV"]::placeholder {
            color: #94A3B8 !important;
            font-weight: 500 !important;
        }
        
        /* Foto circular flotante de perfil */
        .avatar-premium {
            width: 68px;
            height: 68px;
            border: 2px solid #FFFFFF !important;
            box-shadow: 3px 3px 6px #CBD5E1, -2px -2px 5px #FFFFFF !important;
            object-fit: cover;
            display: block;
            margin: 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "submenu_actual" not in st.session_state:
        st.session_state.submenu_actual = "Inicio"

    def _avatar_src() -> str:
        foto = st.session_state.get("foto_usuario")
        foto_mime = st.session_state.get("foto_usuario_mime") or "image/jpeg"
        if foto:
            try:
                encoded = base64.b64encode(foto).decode("ascii")
                return f"data:{foto_mime};base64,{encoded}"
            except Exception:
                pass
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
            "<rect width='100' height='100' rx='50' fill='#E2E8F0'/>"
            "<circle cx='50' cy='40' r='18' fill='#94A3B8'/>"
            "<path d='M20 92c6-20 24-30 30-30s24 10 30 30' fill='#94A3B8'/>"
            "</svg>"
        )
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

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

    # Maquetación estructural de las columnas
    q_qp = _qp_all().get("q") or ""
    if "nav_search" not in st.session_state:
        st.session_state.nav_search = q_qp

    def _on_search_change():
        q = (st.session_state.get("nav_search") or "").strip()
        st.session_state.submenu_actual = "Inicio"
        if "selected_profesional_id" in st.session_state:
            st.session_state.selected_profesional_id = None
        _qp_set({"tab": "Inicio", "q": q if q else None, "prof": None})

    with st.container():
        st.markdown('<div class="premium-nav-container">', unsafe_allow_html=True)
        
        col_dots, col_1, col_2, col_3, col_search, col_avatar = st.columns([0.5, 1.1, 1.1, 1.1, 2.2, 0.75])

        # Puntos decorativos estilo Mac de la esquina izquierda
        with col_dots:
            st.markdown(
                """
                <div style='display: flex; gap: 6px; justify-content: center; align-items: center; height: 44px;'>
                    <span style='width: 9px; height: 9px; background: #FF5F56; border-radius: 50%; display: inline-block;'></span>
                    <span style='width: 9px; height: 9px; background: #FFBD2E; border-radius: 50%; display: inline-block;'></span>
                    <span style='width: 9px; height: 9px; background: #27C93F; border-radius: 50%; display: inline-block;'></span>
                </div>
                """, 
                unsafe_allow_html=True
            )

        # Botón 1: Inicio (Fuerza el estilo sólido oscuro si está seleccionado)
        with col_1:
            is_active = "active-inicio" if st.session_state.submenu_actual == "Inicio" else ""
            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button("Inicio", key="nav_p_inicio", use_container_width=True):
                st.session_state.submenu_actual = "Inicio"
                if "selected_profesional_id" in st.session_state:
                    st.session_state.selected_profesional_id = None
                if "selected_cliente_chat_id" in st.session_state:
                    st.session_state.selected_cliente_chat_id = None
                _qp_set({"tab": "Inicio", "prof": None, "cli": None})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Botón 2: Mensajes (Activa el brillo ámbar inferior al ser seleccionado)
        with col_2:
            is_active = "active-glow" if st.session_state.submenu_actual == "Mensajes" else ""
            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button("Mensajes", key="nav_p_mensajes", use_container_width=True):
                st.session_state.submenu_actual = "Mensajes"
                _qp_set({"tab": "Mensajes"})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Botón 3: Contratos
        with col_3:
            is_active = "active-glow" if st.session_state.submenu_actual == "Contratos" else ""
            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button("Contratos", key="nav_p_contratos", use_container_width=True):
                st.session_state.submenu_actual = "Contratos"
                _qp_set({"tab": "Contratos"})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Buscador Neumórfico Integrado
        with col_search:
            st.text_input(
                "BUSCADOR_NAV",
                key="nav_search",
                placeholder="Escribe tu necesidad: rodilla, hombro, masa muscular, bajar de peso...",
                label_visibility="collapsed",
                on_change=_on_search_change,
            )

        # Avatar clicable (botón Streamlit: no recarga la página ni pierde la sesión)
        with col_avatar:
            avatar_src = _avatar_src()
            st.markdown(
                f"""
                <style>
                .st-key-nav_avatar {{
                    display: flex;
                    justify-content: center;
                }}
                .st-key-nav_avatar button {{
                    width: 68px !important;
                    height: 68px !important;
                    min-width: 68px !important;
                    border-radius: 50% !important;
                    background: url("{avatar_src}") center/cover no-repeat !important;
                    border: 2px solid #FFFFFF !important;
                    box-shadow: 3px 3px 6px #CBD5E1, -2px -2px 5px #FFFFFF !important;
                    color: transparent !important;
                    font-size: 0 !important;
                    padding: 0 !important;
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            if st.button("\u00a0", key="nav_avatar", help="Ver mi perfil"):
                st.session_state.submenu_actual = "perfil"
                if "selected_profesional_id" in st.session_state:
                    st.session_state.selected_profesional_id = None
                _qp_set({"tab": "perfil", "prof": None})
                st.rerun()

        token_badge = st.session_state.get("auth_token") or _qp_all().get("s")
        if token_badge and st.session_state.get("logeado"):
            render_nav_badge_listener(token=str(token_badge))
