ESPECIALIDADES_PROFESIONALES = [
    "Entrenador Personal",
    "Nutricionista Deportivo",
    "Fisioterapeuta",
]

TARIFA_UNIDADES = ["sesion", "semana", "mes"]

ESTADOS_VERIFICACION = [
    "pendiente",
    "verificado",
    "rechazado",
]

UNIVERSIDADES_FISIOTERAPIA = [
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

UNIVERSIDADES_ENTRENAMIENTO_CO = [
    "Servicio Nacional de Aprendizaje (SENA)",
    "Universidad Santo Tomás",
    "Fundación Universitaria del Área Andina",
    "Universidad ECCI",
    "Institución Universitaria Escuela Nacional del Deporte",
]

UNIVERSIDADES_ENTRENAMIENTO_INT = [
    "National Strength and Conditioning Association (NSCA)",
    "International Sports Sciences Association (ISSA)",
    "National Academy of Sports Medicine (NASM)",
    "National Council on Strength and Fitness (NCSF)",
    "American College of Sports Medicine (ACSM)",
    "Escuela Colombiana de Entrenamiento y Fitness (ECEP)",
]

UNIVERSIDADES_NUTRICION_CO = [
    "Universidad de Ciencias Aplicadas y Ambientales (UDCA)",
    "Universidad Nacional de Colombia",
    "Universidad de Antioquia (UdeA)",
    "Universidad El Bosque",
    "Institución Universitaria Escuela Nacional del Deporte",
    "Universidad Pontificia Bolivariana (UPB)",
    "Universidad de los Andes",
]

UNIVERSIDADES_NUTRICION_INT = [
    "Universidad Católica San Antonio de Murcia (UCAM)",
    "Universitat Oberta de Catalunya (UOC)",
    "Universidad Europea de Madrid",
    "Universidad de Barcelona (UB)",
    "International Society of Sports Nutrition (ISSN)",
    "National Academy of Sports Medicine (NASM)",
    "American Council on Exercise (ACE)",
]


def universidades_por_especialidad(especialidad: str, origen: str | None = None) -> list[str]:
    esp = (especialidad or "").strip().lower()
    org = (origen or "").strip()

    if esp == "fisioterapeuta":
        return UNIVERSIDADES_FISIOTERAPIA

    if esp == "entrenador personal":
        return UNIVERSIDADES_ENTRENAMIENTO_INT if org == "Fuera del país" else UNIVERSIDADES_ENTRENAMIENTO_CO

    if esp == "nutricionista deportivo":
        return UNIVERSIDADES_NUTRICION_INT if org == "Fuera del país" else UNIVERSIDADES_NUTRICION_CO

    return []


__all__ = [
    "ESPECIALIDADES_PROFESIONALES",
    "TARIFA_UNIDADES",
    "ESTADOS_VERIFICACION",
    "universidades_por_especialidad",
]