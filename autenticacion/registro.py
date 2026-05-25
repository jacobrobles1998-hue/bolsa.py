
import streamlit as st

from basededatos.manejarbasededatos import (
    DEPARTAMENTOS_COLOMBIA,
    agregar_certificacion_profesional,
    crear_cliente,
    crear_profesional,
)

def formulario_registro_profesional_ui():
    """
    Formulario de registro exclusivo para Profesionales.
    Ubicación fuera del form para habilitar reactividad en cascada legalmente.
    """
    st.markdown("### Registro de nuevo profesional")
    st.caption("Completa tu perfil para poder ofrecer tus servicios en AXON")

    if "prof_reg_step" not in st.session_state:
        st.session_state.prof_reg_step = 1
    if "prof_reg_data" not in st.session_state:
        st.session_state.prof_reg_data = {}

    step = int(st.session_state.prof_reg_step)

    if step == 1:
        with st.form("form_registro_prof_step_1"):
            st.markdown("Datos de cuenta y contacto")
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                nombre_completo = st.text_input("Nombre completo", placeholder="Ej: Javid Martínez", key="prof_nombre")
                depto_sel = st.selectbox(
                    "Departamento de residencia",
                    list(DEPARTAMENTOS_COLOMBIA.keys()),
                    key="prof_depto",
                )

            with col_c2:
                telefono = st.text_input("Teléfono", placeholder="Ej: 3101234567", key="prof_tel")
                contrasena = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres", key="prof_pass")
                confirmar_contrasena = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña", key="prof_pass_conf")

            st.markdown("---")
            st.markdown("Información personal")
            genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="prof_genero")

            # st.markdown("---")
            # st.markdown("Ficha física")
            # col_f1, col_f2, col_f3 = st.columns(3)
            # with col_f1:
            #     edad = st.number_input("Edad (Años)", min_value=18, max_value=90, value=24, step=1, key="prof_edad")
            # with col_f2:
            #     altura = st.number_input("Altura (Metros)", min_value=1.20, max_value=2.30, value=1.75, step=0.01, format="%.2f", key="prof_altura")
            # with col_f3:
            #     peso = st.number_input("Peso Actual (Kg)", min_value=40.0, max_value=150.0, value=74.0, step=0.1, format="%.1f", key="prof_peso")

            continuar = st.form_submit_button("Continuar", use_container_width=True)

            if continuar:
                if not nombre_completo.strip() or not telefono.strip() or not contrasena.strip():
                    st.error("Por favor, llena los campos obligatorios.")
                elif contrasena != confirmar_contrasena:
                    st.error("Las contraseñas no coinciden.")
                else:
                    st.session_state.prof_reg_data = {
                        "nombre": nombre_completo.strip(),
                        "telefono": telefono.strip(),
                        "password": contrasena,
                        "departamento": depto_sel,
                        "ciudad": None,
                        "genero": genero,
                        # "edad": int(edad) if edad is not None else None,
                        # "altura": float(altura) if altura is not None else None,
                        # "peso": float(peso) if peso is not None else None,
                    }
                    st.session_state.prof_reg_step = 2
                    st.rerun()

    if step == 2:
        col_back, _ = st.columns([0.2, 0.8])
        with col_back:
            if st.button("←", key="prof_reg_back"):
                st.session_state.prof_reg_step = 1
                st.rerun()

        st.markdown("Información personal y tarifas")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            especialidad = st.selectbox(
                "Tu Especialidad Principal",
                ["Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"],
                key="prof_espe",
            )
        with col_p2:
            experiencia = st.number_input("Años de Experiencia", min_value=0, max_value=50, value=5, step=1, key="prof_exp")
            tarifa = st.number_input("Tarifa por Sesión (COP)", min_value=10000.0, value=60000.0, step=5000.0, format="%.2f", key="prof_tarifa")

        st.markdown("---")
        #  lista de institucions fisio
        universidad = None
        if especialidad == "Fisioterapeuta":
            st.markdown("Formación (Fisioterapia)")
            universidades_fisio = [
                "Universidad Simón Bolívar",
                "Universidad Metropolitana",
                "Universidad Libre",
                "Universidad del Sinú",
                "Universidad de Santander",
                "Universidad de San Buenaventura",
                "Universidad del Rosario",
                "Universidad Nacional de Colombia",
                "Fundación Universitaria de Ciencias de la Salud",
                "Universidad Manuela Beltrán",
                "Escuela Colombiana de Rehabilitación",
                "Universidad de La Sabana",
                "Corporación Universitaria Iberoamericana",
                "Universidad CES",
                "Fundación Universitaria María Cano",
                "Universidad Autónoma de Manizales",
                "Universidad Tecnológica de Pereira",
                "Universidad del Quindío",
                "Institución Universitaria Escuela Nacional del Deporte",
                "Universidad del Valle",
                "Universidad Santiago de Cali",
                "Universidad Industrial de Santander",
                "Universidad de Boyacá",
            ]

            #  lista de instituciones entrenadores
            universidad = st.selectbox("¿Dónde estudiaste?", universidades_fisio, key="prof_uni_fisio")
        elif especialidad == "Entrenador Personal":
            st.markdown("Formación (Entrenamiento)")
            origen = st.radio("Origen", ["En Colombia", "Fuera del país"], horizontal=True, key="prof_entrenador_origen")
            if origen == "En Colombia":
                universidades_colombia = [
                    "Servicio Nacional de Aprendizaje (SENA)",
                    "Universidad Santo Tomás",
                    "Fundación Universitaria del Área Andina",
                    "Universidad ECCI",
                    "Institución Universitaria Escuela Nacional del Deporte",
                ]
                universidad = st.selectbox("En Colombia", universidades_colombia, key="prof_uni_entrenador_col")
            else:
                entidades_internacionales = [
                    "National Strength and Conditioning Association (NSCA)",
                    "International Sports Sciences Association (ISSA)",
                    "National Academy of Sports Medicine (NASM)",
                    "National Council on Strength and Fitness (NCSF)",
                    "American College of Sports Medicine (ACSM)",
                    "Escuela Colombiana de Entrenamiento y Fitness (ECEP)",
                ]
                # lista de instituciones nutricionistas 
                universidad = st.selectbox("Fuera del país", entidades_internacionales, key="prof_uni_entrenador_int")
        elif especialidad == "Nutricionista Deportivo":  # <- CORREGIDO: Coincide exactamente con tu selectbox principal
            st.markdown("Formación (Nutrición Deportiva)")
            origen_nutricion = st.radio("Origen", ["En Colombia", "Fuera del país"], horizontal=True, key="prof_nutricionista_origen")
           
           
            if origen_nutricion == "En Colombia":
                universidades_colombia_nutricion = [
                    "Universidad de Ciencias Aplicadas y Ambientales (UDCA)",
                    "Universidad Nacional de Colombia",
                    "Universidad de Antioquia (UdeA)",
                    "Universidad El Bosque",
                    "Institución Universitaria Escuela Nacional del Deporte",
                    "Universidad Pontificia Bolivariana (UPB)",
                    "Universidad de los Andes"
                ]
                universidad = st.selectbox("En Colombia", universidades_colombia_nutricion, key="prof_uni_nutricionista_col")
                
            else:
                entidades_internacionales_nutricion = [
                    "Universidad Católica San Antonio de Murcia (UCAM)",
                    "Universitat Oberta de Catalunya (UOC)",
                    "Universidad Europea de Madrid",
                    "Universidad de Barcelona (UB)",
                    "International Society of Sports Nutrition (ISSN)",
                    "National Academy of Sports Medicine (NASM)",
                    "American Council on Exercise (ACE)"
                ]
                universidad = st.selectbox("Fuera del país", entidades_internacionales_nutricion, key="prof_uni_nutricionista_int")
       
        if "prof_cert_count" not in st.session_state:
            st.session_state.prof_cert_count = 1

        st.markdown("---")
        col_cert_t, col_cert_btn = st.columns([0.82, 0.18])
        with col_cert_t:
            st.markdown("Certificados (foto del diploma)")
        with col_cert_btn:
            if st.button("+", key="prof_cert_add", use_container_width=True):
                st.session_state.prof_cert_count = int(st.session_state.prof_cert_count) + 1
                st.rerun()

        cert_count = int(st.session_state.prof_cert_count)
        for i in range(cert_count):
            #st.markdown(f"Certificado {i + 1}")
            st.file_uploader(
                "Subir imagen",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"prof_cert_up_{i}",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        metodologia = st.text_area(
            "Describe tu Metodología y Enfoque (Esto lo verán tus clientes)",
            placeholder="Ej: Enfoque estricto en ganancias de masa muscular mediante hipertrofia con tempos controlados...",
            key="prof_metodo",
        )

        crear = st.button("Continuar a la foto", key="prof_step2_continue", use_container_width=True)

        if crear:
            data = dict(st.session_state.prof_reg_data or {})
            if not data.get("nombre") or not data.get("telefono") or not data.get("password"):
                st.session_state.prof_reg_step = 1
                st.rerun()

            try:
                profesional_id = crear_profesional(
                    {
                        **data,
                        "especialidad": especialidad,
                        "universidad": universidad,
                        "certificacion": None,
                        "experiencia": int(experiencia) if experiencia is not None else None,
                        "tarifa": float(tarifa) if tarifa is not None else None,
                        "metodologia": metodologia.strip(),
                        "estado_verificacion": "pendiente",
                    }
                )
            except Exception:
                st.session_state.logeado = False
                st.session_state.rol = None
                st.error("No se pudo crear el perfil. Revisa los datos e inténtalo de nuevo.")
            else:
                for i in range(int(st.session_state.get("prof_cert_count") or 0)):
                    foto_obj = st.session_state.get(f"prof_cert_up_{i}")
                    foto_bytes = foto_obj.getvalue() if foto_obj is not None else None
                    foto_mime = getattr(foto_obj, "type", None)
                    if foto_bytes:
                        try:
                            agregar_certificacion_profesional(int(profesional_id), None, foto_bytes, foto_mime)
                        except Exception:
                            pass

                st.session_state.prof_cert_count = 1
                st.session_state.prof_reg_step = 1
                st.session_state.prof_reg_data = {}
                st.session_state.logeado = False
                st.session_state.pantalla = "foto_perfil"
                st.session_state.rol = "profesional"
                st.session_state.usuario_id = profesional_id
                st.session_state.nombre_usuario = data.get("nombre")
                st.session_state.email_usuario = None
                st.success(f"💪 ¡Perfil de {data.get('nombre')} creado con éxito!")
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
            if not nombre_completo.strip() or not telefono.strip() or not contrasena.strip():
                st.error("Por favor, llena los campos obligatorios del cliente.")
            elif contrasena != confirmar_contrasena:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    cliente_id = crear_cliente(
                        {
                            "nombre": nombre_completo.strip(),
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
                    st.error("No se pudo crear el perfil. Revisa los datos e inténtalo de nuevo.")
                else:
                    st.session_state.logeado = False
                    st.session_state.pantalla = "foto_perfil"
                    st.session_state.rol = "cliente"
                    st.session_state.usuario_id = cliente_id
                    st.session_state.nombre_usuario = nombre_completo.strip()
                    st.session_state.email_usuario = None
                    st.success(f"¡Perfil de {nombre_completo} creado con éxito!")
                    st.rerun()




    
    
