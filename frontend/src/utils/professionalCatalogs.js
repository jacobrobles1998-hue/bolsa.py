export const DEPARTAMENTOS_COLOMBIA = {
  'Atlántico': ['Barranquilla', 'Soledad', 'Puerto Colombia', 'Malambo', 'Sabanalarga', 'Baranoa', 'Galapa'],
  'Antioquia': ['Medellín', 'Envigado', 'Bello', 'Itagüí', 'Rionegro', 'Sabaneta', 'Apartadó', 'Turbo', 'Caucasia'],
  'Bogotá D.C.': ['Bogotá'],
  'Valle del Cauca': ['Cali', 'Palmira', 'Tuluá', 'Buenaventura', 'Buga', 'Cartago', 'Jamundí', 'Yumbo'],
  Santander: ['Bucaramanga', 'Floridablanca', 'Girón', 'Piedecuesta', 'Barrancabermeja', 'San Gil'],
  Bolívar: ['Cartagena', 'Turbaco', 'Magangué', 'Arjona', 'Carmen de Bolívar'],
  Magdalena: ['Santa Marta', 'Ciénaga', 'Fundación', 'El Banco'],
  Cundinamarca: ['Soacha', 'Chía', 'Zipaquirá', 'Facatativá', 'Fusagasugá', 'Mosquera', 'Madrid', 'Funza', 'Girardot'],
  'Norte de Santander': ['Cúcuta', 'Ocaña', 'Villa del Rosario', 'Los Patios', 'Pamplona'],
  Risaralda: ['Pereira', 'Dosquebradas', 'Santa Rosa de Cabal'],
  Caldas: ['Manizales', 'La Dorada', 'Riosucio', 'Chinchiná'],
  Quindío: ['Armenia', 'Calarcá', 'Tebaida', 'Montenegro'],
  Córdoba: ['Montería', 'Cereté', 'Lorica', 'Sahagún', 'Montelíbano'],
  Cesar: ['Valledupar', 'Aguachica', 'Agustín Codazzi', 'Bosconia'],
}

export const ESPECIALIDADES = [
  'Entrenador Personal',
  'Nutricionista Deportivo',
  'Fisioterapeuta',
]

export const ORIGEN_FORMACION = ['En Colombia', 'Fuera del país']

const UNIVERSIDADES_FISIOTERAPIA = [
  'Universidad Simón Bolívar',
  'Universidad Metropolitana',
  'Universidad Libre',
  'Universidad del Sinú',
  'Universidad de Santander',
  'Universidad de San Buenaventura',
  'Universidad del Rosario',
  'Universidad Nacional de Colombia',
  'Fundación Universitaria de Ciencias de la Salud',
  'Universidad Manuela Beltrán',
  'Escuela Colombiana de Rehabilitación',
  'Universidad de La Sabana',
  'Corporación Universitaria Iberoamericana',
  'Universidad CES',
  'Fundación Universitaria María Cano',
  'Universidad Autónoma de Manizales',
  'Universidad Tecnológica de Pereira',
  'Universidad del Quindío',
  'Institución Universitaria Escuela Nacional del Deporte',
  'Universidad del Valle',
  'Universidad Santiago de Cali',
  'Universidad Industrial de Santander',
  'Universidad de Boyacá',
]

const UNIVERSIDADES_ENTRENAMIENTO_CO = [
  'Servicio Nacional de Aprendizaje (SENA)',
  'Universidad Santo Tomás',
  'Fundación Universitaria del Área Andina',
  'Universidad ECCI',
  'Institución Universitaria Escuela Nacional del Deporte',
]

const UNIVERSIDADES_ENTRENAMIENTO_INT = [
  'National Strength and Conditioning Association (NSCA)',
  'International Sports Sciences Association (ISSA)',
  'National Academy of Sports Medicine (NASM)',
  'National Council on Strength and Fitness (NCSF)',
  'American College of Sports Medicine (ACSM)',
  'Escuela Colombiana de Entrenamiento y Fitness (ECEP)',
]

const UNIVERSIDADES_NUTRICION_CO = [
  'Universidad de Ciencias Aplicadas y Ambientales (UDCA)',
  'Universidad Nacional de Colombia',
  'Universidad de Antioquia (UdeA)',
  'Universidad El Bosque',
  'Institución Universitaria Escuela Nacional del Deporte',
  'Universidad Pontificia Bolivariana (UPB)',
  'Universidad de los Andes',
]

const UNIVERSIDADES_NUTRICION_INT = [
  'Universidad Católica San Antonio de Murcia (UCAM)',
  'Universitat Oberta de Catalunya (UOC)',
  'Universidad Europea de Madrid',
  'Universidad de Barcelona (UB)',
  'International Society of Sports Nutrition (ISSN)',
  'National Academy of Sports Medicine (NASM)',
  'American Council on Exercise (ACE)',
]

export function getUniversidadesDisponibles(especialidad, origen = 'En Colombia') {
  const esp = (especialidad || '').trim().toLowerCase()

  if (esp === 'fisioterapeuta') return UNIVERSIDADES_FISIOTERAPIA
  if (esp === 'entrenador personal') {
    return origen === 'Fuera del país' ? UNIVERSIDADES_ENTRENAMIENTO_INT : UNIVERSIDADES_ENTRENAMIENTO_CO
  }
  if (esp === 'nutricionista deportivo') {
    return origen === 'Fuera del país' ? UNIVERSIDADES_NUTRICION_INT : UNIVERSIDADES_NUTRICION_CO
  }

  return []
}