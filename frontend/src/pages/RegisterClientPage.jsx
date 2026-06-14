import RegisterClientForm from '../components/forms/registerclientform.jsx'

const initialForm = {
  nombre: '',
  email: '',
  password: '',
  telefono: '',
  departamento: '',
  ciudad: '',
  genero: '',
  edad: '',
  altura: '',
  peso: '',
  patologia_familiar: '',
  metodologia: '',
}

const generoOptions = [
  { value: '', label: 'Selecciona género' },
  { value: 'masculino', label: 'Masculino' },
  { value: 'femenino', label: 'Femenino' },
  { value: 'otro', label: 'Otro' },
]

const toNumberOrNull = (value) => {
  if (value === '') return null
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}

function RegisterClientPage() {
  return <RegisterClientForm />
}

export default RegisterClientPage