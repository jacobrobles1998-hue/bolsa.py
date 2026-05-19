import streamlit as st
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA, buscar_profesionales

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

def mostrar_busqueda():
    st.title("Encuentra tu Especialista")
    
    departamentos = ["Todos"] + list(DEPARTAMENTOS_COLOMBIA.keys())
    especialidades = ["Todos", "Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"]

    col1, col2 = st.columns(2)
    
    with col1:
        departamento = st.selectbox("Departamento", departamentos)
    with col2:
        especialidad = st.selectbox("Especialidad", especialidades)

    resultados = buscar_profesionales(
        departamento=departamento,
        especialidad=especialidad,
    )

    titulo_depto = departamento if departamento != "Todos" else "Colombia"
    st.write(f"### Profesionales disponibles en {titulo_depto}")

    if not resultados:
        st.info("No hay profesionales que coincidan con esos filtros.")
        return

    for prof in resultados:
        with st.container():
            st.markdown(f"#### {prof.get('nombre', 'Profesional')}")
            especialidad_txt = prof.get("especialidad") or "Especialidad no definida"
            st.write(especialidad_txt)
            tarifa = prof.get("tarifa")
            if tarifa is not None:
                st.write(f"💰 ${float(tarifa):,.0f} / sesión")
            depto = prof.get("departamento")
            if depto:
                st.write(f"📍 {depto}")

            if st.button("Ver Perfil Completo", key=f"ver_prof_{prof.get('id')}"):
                st.session_state.selected_profesional_id = prof.get("id")
                _qp_set({"prof": str(prof.get("id"))})
                st.rerun()
