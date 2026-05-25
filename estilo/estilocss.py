#/* assets/style.css */

BOTONES_AXON_CSS = """
/* =========================================================================
   Botones AXON — mismo estilo neumórfico que la barra flotante del dashboard
   (no aplica en pantalla de login: .axon-login-marker)
   ========================================================================= */
.stApp:not(:has(.axon-login-marker)) .stButton > button,
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[kind="secondary"],
.stApp div[data-testid="stFormSubmitButton"] > button,
.stApp div[data-testid="stFormSubmitButton"] > button[kind="primary"],
.stApp div[data-testid="stFormSubmitButton"] > button[kind="secondary"],
.stApp div[data-testid="baseButton-primary"] > button,
.stApp div[data-testid="baseButton-secondary"] > button,
.stApp a[data-testid="stLinkButton"],
.stApp button[data-testid="stBaseButton-primary"],
.stApp button[data-testid="stBaseButton-secondary"] {
    border-radius: 18px !important;
    border: 1px solid rgba(255, 255, 255, 0.9) !important;
    background: #F0F2F5 !important;
    background-color: #F0F2F5 !important;
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    font-family: 'Poppins', sans-serif !important;
    padding: 8px 20px !important;
    min-height: 44px !important;
    height: auto !important;
    box-shadow: 4px 4px 8px #CBD5E1, -4px -4px 8px #FFFFFF !important;
    transition: all 0.2s ease-in-out !important;
}

.stApp:not(:has(.axon-login-marker)) .stButton > button:hover,
.stApp:not(:has(.axon-login-marker)) .stButton > button:focus:not(:active),
.stApp:not(:has(.axon-login-marker)) div[data-testid="stFormSubmitButton"] > button:hover,
.stApp:not(:has(.axon-login-marker)) div[data-testid="stFormSubmitButton"] > button:focus:not(:active),
.stApp:not(:has(.axon-login-marker)) a[data-testid="stLinkButton"]:hover {
    color: #1E293B !important;
    background: #F0F2F5 !important;
    background-color: #F0F2F5 !important;
    border-color: rgba(255, 255, 255, 0.9) !important;
    transform: translateY(-1px) !important;
    box-shadow: 5px 5px 10px #CBD5E1, -5px -5px 10px #FFFFFF !important;
}

.stApp:not(:has(.axon-login-marker)) .stButton > button:active,
.stApp:not(:has(.axon-login-marker)) div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0) !important;
    box-shadow: inset 2px 2px 5px #CBD5E1, inset -2px -2px 5px #FFFFFF !important;
}

.stApp:not(:has(.axon-login-marker)) .stButton > button:disabled,
.stApp:not(:has(.axon-login-marker)) div[data-testid="stFormSubmitButton"] > button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    transform: none !important;
    color: #94A3B8 !important;
}

"""

css__styles = f"""
{BOTONES_AXON_CSS}

/* FONDO DEGRADADO PREMIUM (dashboard; login usa #E3EDF7) */
    .stApp:not(:has(.axon-login-marker)) {{
        background: linear-gradient(135deg, #ffffff 0%, #0ffffff 70%, #000000 100%) !important;
        background-attachment: fixed !important;
    }}

  # /* Estilo para los contenedores de los perfiles */
.css-1r6p8d1 {{
    border: 1px solid #e6e9ef;
    border-radius: 10px;
    padding: 20px;
    background-color: #f9f9f9;
}}

  # /* Títulos con el estilo de AXON */
h1, h2, h3 {{
    color: #2c3e50;
    font-family: 'Poppins', sans-serif;
}}

  # /* Enlaces de registro */
    .Links a:hover {{
        color: #334155 !important;
        text-decoration: underline !important;
        opacity: 1 !important;
    }}

    .Links a:active {{
        color: #1E293B !important;
    }}

    /* =========================================================================
       🌐 DISEÑO PREMIUM DE PESTAÑAS AXON (ESTILO PESTAÑAS DE GOOGLE CHROME)
       ========================================================================= */
    
    /* 1. Forzar a que TODAS las pestañas tengan forma de ficha limpia de navegador */
    div[data-testid="stTabs"] [data-baseweb="tab"] {{
        background-color: #E2E8F0 !important;
        color: #64748B !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 12px 24px !important;
        margin-right: 6px !important;
        border: none !important;
        transition: background-color 0.3s ease, color 0.3s ease !important;
    }}

    div[data-testid="stTabs"] [aria-selected="true"] {{
        background-color: #F0F2F5 !important;
        color: #334155 !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 4px 4px 8px #CBD5E1, -4px -4px 8px #FFFFFF !important;
    }}

    div[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
        background-color: #F8FAFC !important;
        color: #334155 !important;
    }}

    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"],
    div[data-testid="stTabs"] [style*="background-color"],
    div[data-testid="stTabs"] div::after,
    div[data-testid="stTabs"] div::before {{
        display: none !important;
        background-color: transparent !important;
        background: transparent !important;
        height: 0px !important;
        border: none !important;
    }}

    div[data-testid="stTabs"] {{
        border-bottom: none !important;
        background: transparent !important;
    }}

    div[data-testid="stNumberInput"] button {{
        display: none !important;
    }}

    div[data-testid="stNumberInput"] input {{
        padding-right: 10px !important;
        padding-left: 10px !important;
    }}
"""
