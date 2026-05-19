
import streamlit as st
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA
from basededatos.manejarbasededatos import crear_cliente, crear_profesional

def formulario_registro_profesional_ui():
    """
    Formulario de registro exclusivo para Profesionales.
    Ubicación fuera del form para habilitar reactividad en cascada legalmente.
    """
    st.markdown("### Registro de nuevo profesional")
    st.caption("Completa tu perfil para poder ofrecer tus servicios en AXON")

   

    # 2. Ahora sí abrimos el formulario para empaquetar el resto de los datos
    with st.form("form_registro_largo_profesional"):
        st.markdown("Datos de cuenta y contacto")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            nombre_completo = st.text_input("Nombre completo", placeholder="Ej: Javid Martínez", key="prof_nombre")
            correo_electronico = st.text_input("Correo electrónico", placeholder="Ej: javid.martinez@example.com", key="prof_email")
            depto_sel = st.selectbox(
                "Departamento de residencia", 
                list(DEPARTAMENTOS_COLOMBIA.keys()),
                key="prof_depto"
            )

        with col_c2:
            telefono = st.text_input("Teléfono", placeholder="Ej: 3101234567", key="prof_tel")
            contrasena = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres", key="prof_pass")
            confirmar_contrasena = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña", key="prof_pass_conf")
            genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="prof_genero")
        
        st.markdown("---")
        
        # --- SECCIÓN B: FICHA FÍSICA ---
        st.markdown("Ficha Física del Especialista")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            edad = st.number_input("Edad (Años)", min_value=18, max_value=90, value=24, step=1, key="prof_edad")
        with col_f2:
            altura = st.number_input("Altura (Metros)", min_value=1.20, max_value=2.30, value=1.75, step=0.01, format="%.2f", key="prof_altura")
        with col_f3:
            peso = st.number_input("Peso Actual (Kg)", min_value=40.0, max_value=150.0, value=74.0, step=0.1, format="%.1f", key="prof_peso")
            
        st.markdown("---")
        
        # --- SECCIÓN C: PERFIL PROFESIONAL ---
        st.markdown("Información Profesional y Tarifas")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            especialidad = st.selectbox(
                "Tu Especialidad Principal", 
                ["Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"],
                key="prof_espe"
            )
            certificacion = st.text_input("Título o Certificación Destacada", placeholder="Ej: Certificado en Biomecánica", key="prof_cert")
        with col_p2:
            experiencia = st.number_input("Años de Experiencia", min_value=0, max_value=50, value=5, step=1, key="prof_exp")  
            tarifa = st.number_input("Tarifa por Sesión (COP)", min_value=10000.0, value=60000.0, step=5000.0, format="%.2f", key="prof_tarifa")
            
        st.markdown("<br>", unsafe_allow_html=True)
        metodologia = st.text_area(
            "Describe tu Metodología y Enfoque (Esto lo verán tus clientes)", 
            placeholder="Ej: Enfoque estricto en ganancias de masa muscular mediante hipertrofia con tempos controlados...",
            key="prof_metodo"
        )
        
        boton_enviar_prof = st.form_submit_button("Crear Perfil Profesional", use_container_width=True)
        
        if boton_enviar_prof:
            if not nombre_completo.strip() or not correo_electronico.strip() or not contrasena.strip():
                st.error("Por favor, llena los campos obligatorios del profesional.")
            elif contrasena != confirmar_contrasena:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    profesional_id = crear_profesional(
                        {
                            "nombre": nombre_completo.strip(),
                            "email": correo_electronico.strip(),
                            "telefono": telefono.strip(),
                            "password": contrasena,
                            "departamento": depto_sel,
                            "ciudad": None,
                            "genero": genero,
                            "edad": int(edad) if edad is not None else None,
                            "altura": float(altura) if altura is not None else None,
                            "peso": float(peso) if peso is not None else None,
                            "especialidad": especialidad,
                            "certificacion": certificacion.strip(),
                            "experiencia": int(experiencia) if experiencia is not None else None,
                            "tarifa": float(tarifa) if tarifa is not None else None,
                            "metodologia": metodologia.strip(),
                        }
                    )
                except Exception:
                    st.session_state.logeado = False
                    st.session_state.rol = None
                    st.error("No se pudo crear el perfil. Revisa si el correo ya existe e inténtalo de nuevo.")
                else:
                    st.session_state.logeado = False
                    st.session_state.pantalla = "foto_perfil"
                    st.session_state.rol = "profesional"
                    st.session_state.usuario_id = profesional_id
                    st.session_state.nombre_usuario = nombre_completo.strip()
                    st.session_state.email_usuario = correo_electronico.strip().lower()
                    st.success(f"💪 ¡Perfil de {nombre_completo} creado con éxito!")
                    st.rerun()


def formulario_registro_cliente_ui():
    """
    Formulario de registro para Clientes.
    Ubicación fuera del form para habilitar reactividad en cascada legalmente.
    """
    st.markdown("### Registro nuevo de cliente")
    st.caption("Regístrate como cliente para buscar y contratar a los mejores profesionales.")

      # 2. Ahora sí abrimos el formulario para empaquetar el resto de los datos
    with st.form("form_registro_largo_cliente"):
        st.markdown("Datos de cuenta y contacto")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            nombre_completo = st.text_input("Nombre completo", placeholder="Ej: Javid Martínez", key="cli_nombre")
            correo_electronico = st.text_input("Correo electrónico", placeholder="Ej: javid.martinez@example.com", key="cli_email")
            depto_sel = st.selectbox(
                "Departamento de residencia", 
                list(DEPARTAMENTOS_COLOMBIA.keys()),
                key="cli_depto"
            )
            patologia_familiar = st.selectbox(
                "Patología Familiar", 
                ["Si", "No"],
                key="cli_patologia"
            )

        with col_c2:
            telefono = st.text_input("Teléfono", placeholder="Ej: 3101234567", key="cli_tel")
            contrasena = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres", key="cli_pass")
            confirmar_contrasena = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña", key="cli_pass_conf")
            genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="cli_genero")

        st.markdown("---")
        st.markdown("Datos básicos")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            edad = st.number_input("Edad (Años)", min_value=14, max_value=90, value=24, step=1, key="cli_edad")
        with col_b2:
            altura = st.number_input("Altura (Metros)", min_value=1.20, max_value=2.30, value=1.70, step=0.01, format="%.2f", key="cli_altura")
        with col_b3:
            peso = st.number_input("Peso Actual (Kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1, format="%.1f", key="cli_peso")

            st.markdown("<br>", unsafe_allow_html=True)
            metodologia = st.text_area(
           "(Esto lo verán tus profesionales)", 
            placeholder="Ej: si tienes alguna patologia o condicion especial, por favor, describela aquí...",
            key="cli_metodo"
        )

        boton_enviar_cli = st.form_submit_button("Crear Perfil Cliente", use_container_width=True)
        
        if boton_enviar_cli:
            if not nombre_completo.strip() or not correo_electronico.strip() or not contrasena.strip():
                st.error("Por favor, llena los campos obligatorios del cliente.")
            elif contrasena != confirmar_contrasena:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    cliente_id = crear_cliente(
                        {
                            "nombre": nombre_completo.strip(),
                            "email": correo_electronico.strip(),
                            "telefono": telefono.strip(),
                            "password": contrasena,
                            "departamento": depto_sel,
                            "ciudad": None,
                            "genero": genero,
                            "edad": int(edad) if edad is not None else None,
                            "altura": float(altura) if altura is not None else None,
                            "peso": float(peso) if peso is not None else None,
                            "patologia_familiar": patologia_familiar,
                            "metodologia": metodologia.strip(),
                        }
                    )
                except Exception:
                    st.session_state.logeado = False
                    st.session_state.rol = None
                    st.error("No se pudo crear el perfil. Revisa si el correo ya existe e inténtalo de nuevo.")
                else:
                    st.session_state.logeado = False
                    st.session_state.pantalla = "foto_perfil"
                    st.session_state.rol = "cliente"
                    st.session_state.usuario_id = cliente_id
                    st.session_state.nombre_usuario = nombre_completo.strip()
                    st.session_state.email_usuario = correo_electronico.strip().lower()
                    st.success(f"¡Perfil de {nombre_completo} creado con éxito!")
                    st.rerun()




    
    
