# interfaz_base.py
# interfaz_base.py
import streamlit as st

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

        /* 2. BOTONES EN ESTADO NORMAL (Extrusión limpia con relieve) */
        .stButton > button {
            border-radius: 18px !important;
            border: 1px solid rgba(255, 255, 255, 0.9) !important;
            background: #F0F2F5 !important;
            color: #334155 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            padding: 8px 20px !important;
            height: 44px !important;
            
            /* Sombra neumórfica clásica: Luz arriba a la izquierda, sombra abajo a la derecha */
            box-shadow: 
                4px 4px 8px #CBD5E1, 
                -4px -4px 8px #FFFFFF !important;
            transition: all 0.2s ease-in-out !important;
        }

        /* Efecto al pasar el cursor */
        .stButton > button:hover {
            color: #1E293B !important;
            transform: translateY(-1px) !important;
            box-shadow: 
                5px 5px 10px #CBD5E1, 
                -5px -5px 10px #FFFFFF !important;
        }

        /* 3. PESTAÑA SELECCIONADA: INICIO (Estilo Antracita Sólido "Overview") */
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

        /* 4. PESTAÑA SELECCIONADA CON GLOW (Efecto resplandor de luz inferior) */
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
        
        /* Foto circular flotante de perfil */
        .avatar-premium {
            width: 42px;
            height: 42px;
            border-radius: 50% !important;
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

    # Maquetación estructural de las columnas
    with st.container():
        st.markdown('<div class="premium-nav-container">', unsafe_allow_html=True)
        
        col_dots, col_1, col_2, col_3, col_search, col_avatar = st.columns([0.5, 1.1, 1.1, 1.1, 2.2, 0.6])

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
                _qp_set({"tab": "Inicio"})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Botón 2: Progreso (Activa el brillo ámbar inferior al ser seleccionado)
        with col_2:
            is_active = "active-glow" if st.session_state.submenu_actual == "Progreso" else ""
            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button("Progreso", key="nav_p_progreso", use_container_width=True):
                st.session_state.submenu_actual = "Progreso"
                _qp_set({"tab": "Progreso"})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Botón 3: Ajustes
        with col_3:
            is_active = "active-glow" if st.session_state.submenu_actual == "Configuracion" else ""
            st.markdown(f'<div class="{is_active}">', unsafe_allow_html=True)
            if st.button("Configuración", key="nav_p_config", use_container_width=True):
                st.session_state.submenu_actual = "Configuracion"
                _qp_set({"tab": "Configuracion"})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Buscador Neumórfico Integrado
        with col_search:
            st.markdown(
                """
                <div class="search-container-premium">
                    <span style="margin-right: 8px;">🔍</span>
                    <span style="color: #94A3B8; font-family: sans-serif; font-weight: 500;">Buscar atletas o rutinas...</span>
                </div>
                """, 
                unsafe_allow_html=True
            )

        # Avatar o foto del usuario logeado
        with col_avatar:
            st.markdown(
                """
                <img src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&q=80" 
                     class="avatar-premium" alt="User">
                """, 
                unsafe_allow_html=True
            )
            
        st.markdown('</div>', unsafe_allow_html=True)
