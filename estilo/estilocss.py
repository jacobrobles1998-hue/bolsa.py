#/* assets/style.css */

  # /* Cambiar el color de fondo de las tarjetas de los profesionales */
css__styles = """
/* 📱 FONDO DEGRADADO PREMIUM (ESTILO AZUL SATINADO) */
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #0ffffff 70%, #000000 100%) !important;
        background-attachment: fixed !important;
    }

.stButton>button {
    border-radius: 20px;
    background-color: #007bff;
    color: white;
    font-weight: bold;
    width: 100%;
}

  # /* Estilo para los contenedores de los perfiles */
.css-1r6p8d1 {
    border: 1px solid #e6e9ef;
    border-radius: 10px;
    padding: 20px;
    background-color: #f9f9f9;
}

  # /* Títulos con el estilo de AXON */
h1, h2, h3 {
    color: #2c3e50;
    font-family: 'Helvetica', sans-serif;
}

  # /* 🚫 Evita que el enlace de registro se ponga gris o pierda color al pasar el cursor */
    .Links a:hover {
        color: #1eb392 !important;            /* Le da un turquesa un poco más vivo y oscurito */
        text-decoration: underline !important; /* Le añade una línea abajo sutil para que se note el toque */
        opacity: 1 !important;                 /* Forza al navegador a NO ponerlo transparente ni gris */
    }

    /* 🔵 Controla el color cuando la persona hace el clic físico */
    .Links a:active {
        color: #179176 !important;            /* Se pone un pelín más oscuro al hundirlo */
    }

    /* =========================================================================
       🌐 DISEÑO PREMIUM DE PESTAÑAS AXON (ESTILO PESTAÑAS DE GOOGLE CHROME)
       ========================================================================= */
    
    /* 1. Forzar a que TODAS las pestañas tengan forma de ficha limpia de navegador */
    div[data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: #e0e0e0 !important; /* Fondo gris para las pestañas inactivas */
        color: #666666 !important;            /* Texto gris oscuro para lo inactivo */
        border-radius: 8px 8px 0px 0px !important; /* Esquinas redondeadas arriba como Chrome */
        padding: 12px 24px !important;
        margin-right: 6px !important;
        border: none !important;
        transition: background-color 0.3s ease, color 0.3s ease !important;
    }

    /* 2. 💡 PESTAÑA ACTIVA: La ficha que el usuario seleccionó */
    div[data-testid="stTabs"] [aria-selected="true"] {
        background-color: #ffffff !important; /* Se ilumina completamente en blanco limpio */
        color: #1eb392 !important;            /* El texto toma el turquesa elegante de AXON */
        font-weight: bold !important;
        border: none !important;              /* Elimina cualquier borde nativo */
    }

    /* 3. 🖱️ EFECTO HOVER: Al pasar el cursor sobre las pestañas apagadas */
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: #f0f0f0 !important; /* Se aclara sutilmente el gris antes de pulsar */
        color: #333333 !important;
    }

    /* 4. 🚫 EXTINCIÓN DE LA RAYA DE COLOR (Mata la línea roja/verde por completo) */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"],
    div[data-testid="stTabs"] [style*="background-color"],
    div[data-testid="stTabs"] div::after,
    div[data-testid="stTabs"] div::before {
        display: none !important;
        background-color: transparent !important;
        background: transparent !important;
        height: 0px !important;
        border: none !important;
    }

    /* 🧼 Limpieza del contenedor general de las pestañas */
    div[data-testid="stTabs"] {
        border-bottom: none !important;
        background: transparent !important;
    }
   /* 🚫 ELIMINAR POR COMPLETO LOS BOTONES + Y - DE LOS INPUTS NUMÉRICOS */
    div[data-testid="stNumberInput"] button {
        display: none !important;
    }

    /* Ajuste extra opcional: Quita el espacio vacío que dejan los botones a los lados */
    div[data-testid="stNumberInput"] input {
        padding-right: 10px !important;
        padding-left: 10px !important;
    }
"""
