import streamlit as st
import streamlit.components.v1 as components

# 1. Configuración de la página (Siempre de primero)
st.set_page_config(
    page_title="AXON - Optimización Humana",
    page_icon="🚀",
    layout="wide"
)

# 2. Inyectar la tipografía Poppins en toda la app de forma global
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

# 3. IMPORTACIÓN DE TUS MÓDULOS
from autenticacion.registro import formulario_registro_profesional_ui
from autenticacion.ingresos import mostrar_interfaz_login
from autenticacion.registro import formulario_registro_cliente_ui
from perfiles.profesional import perfil_profesional_view    
from perfiles.cliente import perfil_cliente_view
from nucleo.citas import mostrar_busqueda
from nucleo.agendamiento import gestionar_agenda
from finanzas.pagos import procesar_pago
from basededatos.manejarbasededatos import crear_contrato, crear_sesion, crear_tablas_iniciales, eliminar_cliente, eliminar_profesional, eliminar_sesion, guardar_foto_cliente, guardar_foto_profesional, listar_clientes_de_profesional, obtener_cliente_por_id, obtener_profesional_por_id, obtener_sesion
from estilo.estilocss import css__styles 
from interfaz_base import barra_navegacion_glass
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA

# Inyectar estilos CSS generales
st.markdown(f'<style>{css__styles}</style>', unsafe_allow_html=True) 

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

def _qp_get(key: str):
    return _qp_all().get(key)

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

if "db_inicializada" not in st.session_state:
    try:
        crear_tablas_iniciales()
        st.session_state.db_inicializada = True
    except Exception as e:
        st.session_state.db_inicializada = False
        st.error(f"No se pudo inicializar la base de datos: {e}")

def mostrar_login_neumorfico():
    """
    Busca los archivos visuales usando rutas relativas directas 
    e inyecta el diseño neumórfico en la app.
    """
    html_path = "estilo/panel.html"
    css_path = "estilo/neumorfico.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_codigo = f.read()
        with open(html_path, "r", encoding="utf-8") as f:
            html_codigo = f.read()
        diseno_final = f"<style>{css_codigo}</style>\n{html_codigo}"
        components.html(diseno_final, height=850, scrolling=False)
    except FileNotFoundError as e:
        st.error(f"Alerta visual: No se pudo cargar la plantilla: {e}")


# ==========================================
# 4. INICIALIZAR EL ESTADO (Estructura Limpia)
# ==========================================
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "login"  # Arrenca estrictamente en el Login

if "logeado" not in st.session_state:
    st.session_state.logeado = False

if "rol" not in st.session_state:
    st.session_state.rol = None

if "submenu_actual" not in st.session_state:
    st.session_state.submenu_actual = "Inicio"

if "selected_profesional_id" not in st.session_state:
    st.session_state.selected_profesional_id = None

tab_q = _qp_get("tab")
if tab_q in {"Inicio", "Progreso", "Configuracion"}:
    st.session_state.submenu_actual = tab_q

prof_q = _qp_get("prof")
if prof_q and str(prof_q).isdigit():
    st.session_state.selected_profesional_id = int(prof_q)

if not st.session_state.logeado:
    token_q = _qp_get("s")
    if token_q:
        ses = obtener_sesion(str(token_q))
        if ses:
            if ses["rol"] == "profesional":
                user = obtener_profesional_por_id(ses["user_id"])
                estado = (user or {}).get("estado_verificacion")
                if (estado or "pendiente").strip().lower() != "verificado":
                    eliminar_sesion(str(token_q))
                    _qp_set({"s": None})
                    st.warning("Tu perfil profesional está en verificación. Cuando sea aprobado podrás iniciar sesión.")
                else:
                    st.session_state.logeado = True
                    st.session_state.pantalla = "login"
                    st.session_state.rol = ses["rol"]
                    st.session_state.usuario_id = ses["user_id"]
                    st.session_state.nombre_usuario = (user or {}).get("nombre")
                    st.session_state.email_usuario = None
                    st.session_state.foto_usuario = (user or {}).get("foto")
                    st.session_state.foto_usuario_mime = (user or {}).get("foto_mime")
            else:
                user = obtener_cliente_por_id(ses["user_id"])
                st.session_state.logeado = True
                st.session_state.pantalla = "login"
                st.session_state.rol = ses["rol"]
                st.session_state.usuario_id = ses["user_id"]
                if user:
                    st.session_state.nombre_usuario = user.get("nombre")
                    st.session_state.email_usuario = None
                    st.session_state.foto_usuario = user.get("foto")
                    st.session_state.foto_usuario_mime = user.get("foto_mime")
        else:
            _qp_set({"s": None})


# ==========================================
# 5. LÓGICA DE CONTROL (Aislamiento Radical)
# ==========================================

# 🚀 MUNDO 1: EL USUARIO YA ENTRÓ (Dashboard & Barra Flotante Premium)
if st.session_state.logeado: 
    if "usuario_id" not in st.session_state or st.session_state.get("rol") not in {"cliente", "profesional"}:
        st.session_state.logeado = False
        st.session_state.pantalla = "login"
        st.session_state.rol = None
        st.rerun()

    # 1. Ejecuta tu barra de navegación glass desde interfaz_base
    barra_navegacion_glass() 
    
    # 2. Captura la pestaña activa
    vista = st.session_state.submenu_actual
    
    # 3. Renderizado de Contenedores Limpios
    if vista == "Inicio":
        rol = st.session_state.get("rol")
        usuario_id = st.session_state.get("usuario_id")

        if rol == "cliente":
            mostrar_busqueda()

            profesional_id = st.session_state.get("selected_profesional_id")
            if profesional_id:
                profesional = obtener_profesional_por_id(profesional_id)
                if profesional:
                    perfil_profesional_view(profesional)
                    tarifa = profesional.get("tarifa")
                    monto = float(tarifa) if tarifa is not None else None
                    if st.button("Contratar a este profesional", use_container_width=True):
                        crear_contrato(
                            id_cliente=int(usuario_id),
                            id_profesional=int(profesional_id),
                            monto=monto,
                        )
                        st.session_state.selected_profesional_id = None
                        _qp_set({"prof": None})
                        st.success("Contrato creado. Ya eres cliente de este profesional.")
                        st.rerun()

            cliente = obtener_cliente_por_id(usuario_id)
            if cliente:
                with st.expander("Mi perfil", expanded=False):
                    perfil_cliente_view(cliente)

        elif rol == "profesional":
            profesional = obtener_profesional_por_id(usuario_id)
            if profesional:
                perfil_profesional_view(profesional)
            clientes = listar_clientes_de_profesional(int(usuario_id))
            if not clientes:
                st.info("Todavía no tienes clientes activos.")
            else:
                for c in clientes:
                    with st.container():
                        st.markdown(f"#### {c.get('nombre', 'Cliente')}")
                        telefono = c.get("telefono")
                        if telefono:
                            st.write(f"{telefono}")
                        depto = c.get("departamento")
                        if depto:
                            st.write(f"{depto}")
                        patologia = c.get("patologia_familiar")
                        if patologia:
                            st.write(f"Patología familiar: {patologia}")
                        metodologia = c.get("metodologia")
                        if metodologia:
                            st.write(metodologia)
                        monto = c.get("monto")
                        if monto is not None:
                            st.write(f"Monto: ${float(monto):,.0f}")
                        fecha = c.get("fecha")
                        if fecha:
                            st.write(f"Desde: {fecha}")
                        st.markdown("---")
        
    elif vista == "Progreso":
        st.markdown("Historial de Rendimiento Avanzado")
        
    elif vista == "Configuracion":
        st.subheader("Ajustes")

        with st.expander("Foto de perfil", expanded=False):
            rol = st.session_state.get("rol")
            usuario_id = st.session_state.get("usuario_id")

            tab1, tab2 = st.tabs(["Tomar foto", "Subir foto"])
            foto_file = None
            with tab1:
                foto_file = st.camera_input("Tomar foto", key="ajustes_foto_camera")
            with tab2:
                up = st.file_uploader(
                    "Subir foto",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="ajustes_foto_upload",
                )
                if up is not None:
                    foto_file = up

            disabled = foto_file is None or rol not in {"cliente", "profesional"} or usuario_id is None
            if st.button("Guardar foto", use_container_width=True, disabled=disabled):
                foto_bytes = foto_file.getvalue() if foto_file is not None else None
                foto_mime = getattr(foto_file, "type", None)
                if foto_bytes:
                    if rol == "profesional":
                        guardar_foto_profesional(int(usuario_id), foto_bytes, foto_mime)
                    else:
                        guardar_foto_cliente(int(usuario_id), foto_bytes, foto_mime)
                    st.session_state.foto_usuario = foto_bytes
                    st.session_state.foto_usuario_mime = foto_mime
                    st.success("Foto actualizada.")
                    st.rerun()

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Cerrar sesión", use_container_width=True):
                token_q = _qp_get("s")
                if token_q:
                    eliminar_sesion(str(token_q))
                _qp_set({"s": None})
                st.session_state.logeado = False
                st.session_state.pantalla = "login"
                st.session_state.rol = None
                st.session_state.usuario_id = None
                st.session_state.nombre_usuario = None
                st.session_state.email_usuario = None
                st.session_state.foto_usuario = None
                st.session_state.foto_usuario_mime = None
                st.session_state.selected_profesional_id = None
                st.rerun()

        with col_b:
            if "confirmar_eliminar" not in st.session_state:
                st.session_state.confirmar_eliminar = False

            if not st.session_state.confirmar_eliminar:
                if st.button("Eliminar mi cuenta", use_container_width=True):
                    st.session_state.confirmar_eliminar = True
                    st.rerun()
            else:
                st.warning("Esto borrará tu perfil y tus contratos. Esta acción no se puede deshacer.")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Cancelar", use_container_width=True):
                        st.session_state.confirmar_eliminar = False
                        st.rerun()
                with col_c2:
                    if st.button("Sí, borrar", use_container_width=True):
                        token_q = _qp_get("s")
                        if token_q:
                            eliminar_sesion(str(token_q))
                        _qp_set({"s": None})
                        rol = st.session_state.get("rol")
                        uid = st.session_state.get("usuario_id")
                        if rol == "profesional":
                            eliminar_profesional(int(uid))
                        else:
                            eliminar_cliente(int(uid))
                        st.session_state.confirmar_eliminar = False
                        st.session_state.logeado = False
                        st.session_state.pantalla = "login"
                        st.session_state.rol = None
                        st.session_state.usuario_id = None
                        st.session_state.nombre_usuario = None
                        st.session_state.email_usuario = None
                        st.session_state.selected_profesional_id = None
                        st.success("Cuenta eliminada.")
                        st.rerun()


# 🔒 MUNDO 2: EL USUARIO ESTÁ AFUERA (Login o Registros - Totalmente Ocultos del Dashboard)
else:
    # --- PANTALLA EXCLUSIVA: LOGIN NEUMÓRFICO ---
    if st.session_state.pantalla == "login":
        mostrar_interfaz_login()

    # --- PANTALLA DE SELECCIÓN DE REGISTRO ---
    elif st.session_state.pantalla == "registro":
        st.subheader("¿Cómo quieres unirte a AXON?")
        
        # Radio button para que el usuario elija su camino
        tipo = st.radio("Selecciona tu perfil:", ["Profesional", "Cliente"], horizontal=True)
        
        st.markdown("---")
        
        # Según lo que elija, llamamos a la función correcta
        if tipo == "Profesional":
            formulario_registro_profesional_ui()
        else:
            formulario_registro_cliente_ui() # Aquí llamas al que te salía en la foto c60f88a3
            
            
        # Botón para volver al login si se arrepintió
        if st.button("← Volver al Inicio de Sesión"):
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
                    _qp_set({"s": token, "tab": _qp_get("tab") or "Inicio"})
                    st.session_state.logeado = True
                    st.session_state.pantalla = "login"
                    st.rerun()
            else:
                st.caption("La foto es obligatoria para verificación.")
        with col_b:
            disabled = foto_file is None
            if st.button("Guardar y Continuar", use_container_width=True, disabled=disabled):
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
                    st.session_state.email_usuario = None
                    st.success("Foto guardada. Tu perfil quedó en verificación; cuando sea aprobado podrás iniciar sesión.")
                    st.rerun()
                else:
                    token = crear_sesion(str(rol), int(usuario_id))
                    _qp_set({"s": token, "tab": _qp_get("tab") or "Inicio"})
                    st.session_state.logeado = True
                    st.session_state.pantalla = "login"
                    st.rerun()
        

    
