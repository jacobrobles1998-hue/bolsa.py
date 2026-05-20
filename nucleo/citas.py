import streamlit as st
from basededatos.manejarbasededatos import DEPARTAMENTOS_COLOMBIA, buscar_profesionales
import unicodedata

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

def _qp_get(key: str):
    return _qp_all().get(key)

def _normalize_text(texto: str) -> str:
    texto = (texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))

def inferir_especialidades(texto: str) -> list[str]:
    q = _normalize_text(texto)
    if not q:
        return []

    reglas = {
        "Nutricionista Deportivo": [
            "nutricion",
            "nutricionista",
            "dieta",
            "calorias",
            "caloria",
            "subir de peso",
            "ganar peso",
            "ganar masa",
            "masa muscular",
            "hipertrofia",
            "aumentar peso",
            "volumen",
        ],
        "Entrenador Personal": [
            "entrenador",
            "entrenamiento",
            "rutina",
            "gimnasio",
            "fuerza",
            "musculo",
            "subir de peso",
            "ganar masa",
            "hipertrofia",
            "bajar de peso",
            "perder peso",
            "definir",
            "quemar grasa",
            "cardio",
        ],
        "Fisioterapeuta": [
            "fisio",
            "fisioterapia",
            "rehabilitacion",
            "recuperacion",
            "lesion",
            "esguince",
            "tendinitis",
            "contractura",
            "dolor",
            "rodilla",
            "espalda",
            "hombro",
            "codo",
            "tobillo",
            "cuello",
            "postura",
        ],
    }

    scores: list[tuple[int, str]] = []
    for esp, kws in reglas.items():
        score = 0
        for kw in kws:
            if _normalize_text(kw) in q:
                score += 1
        if score:
            scores.append((score, esp))

    scores.sort(reverse=True)
    return [esp for _, esp in scores]

def mostrar_busqueda():
    st.title("Encuentra tu Especialista")
    
    departamentos = ["Todos"] + list(DEPARTAMENTOS_COLOMBIA.keys())
    especialidades = ["Todos", "Entrenador Personal", "Nutricionista Deportivo", "Fisioterapeuta"]

    q = (st.session_state.get("nav_search") or _qp_get("q") or "").strip()

    if q:
        col_q1, col_q2 = st.columns([0.82, 0.18])
        with col_q1:
            st.caption(f"Búsqueda: {q}")
        with col_q2:
            if st.button("Limpiar", key="limpiar_busqueda", use_container_width=True):
                if "nav_search" in st.session_state:
                    st.session_state.nav_search = ""
                _qp_set({"q": None})
                st.rerun()

    sugeridas = inferir_especialidades(q) if q else []

    col1, col2 = st.columns(2)
    
    with col1:
        departamento = st.selectbox("Departamento", departamentos)
    with col2:
        if sugeridas:
            opciones = ["Ver todos"] + sugeridas
            eleccion = st.selectbox("Según tu búsqueda, te recomiendo:", opciones)
            especialidad = "Todos" if eleccion == "Ver todos" else eleccion
        else:
            especialidad = st.selectbox("Especialidad", especialidades)

    resultados = buscar_profesionales(
        departamento=departamento,
        especialidad=especialidad,
        texto=q if (q and not sugeridas) else None,
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
