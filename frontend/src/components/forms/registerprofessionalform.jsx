import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../services/api.js'

const initialAccount = {
  nombre: '',
  email: '',
  password: '',
  confirmPassword: '',
}

const initialProfile = {
  departamento: '',
  ciudad: '',
  metodologia: '',
  tarifaUnidad: 'sesion',
  tarifa: '',
  especialidad: '',
  universidad: '',
  experiencia: '',
}

const DEPARTAMENTOS_COLOMBIA = {
  'Atlántico': ['Barranquilla', 'Soledad', 'Puerto Colombia', 'Malambo', 'Sabanalarga', 'Baranoa', 'Galapa'],
  'Antioquia': ['Medellín', 'Envigado', 'Bello', 'Itagüí', 'Rionegro', 'Sabaneta', 'Apartadó', 'Turbo', 'Caucasia'],
  'Bogotá D.C.': ['Bogotá'],
  'Valle del Cauca': ['Cali', 'Palmira', 'Tuluá', 'Buenaventura', 'Buga', 'Cartago', 'Jamundí', 'Yumbo'],
  'Santander': ['Bucaramanga', 'Floridablanca', 'Girón', 'Piedecuesta', 'Barrancabermeja', 'San Gil'],
  'Bolívar': ['Cartagena', 'Turbaco', 'Magangué', 'Arjona', 'Carmen de Bolívar'],
  'Magdalena': ['Santa Marta', 'Ciénaga', 'Fundación', 'El Banco'],
  'Cundinamarca': ['Soacha', 'Chía', 'Zipaquirá', 'Facatativá', 'Fusagasugá', 'Mosquera', 'Madrid', 'Funza', 'Girardot'],
  'Norte de Santander': ['Cúcuta', 'Ocaña', 'Villa del Rosario', 'Los Patios', 'Pamplona'],
  'Risaralda': ['Pereira', 'Dosquebradas', 'Santa Rosa de Cabal'],
  'Caldas': ['Manizales', 'La Dorada', 'Riosucio', 'Chinchiná'],
  'Quindío': ['Armenia', 'Calarcá', 'Tebaida', 'Montenegro'],
  'Córdoba': ['Montería', 'Cereté', 'Lorica', 'Sahagún', 'Montelíbano'],
  'Cesar': ['Valledupar', 'Aguachica', 'Agustín Codazzi', 'Bosconia'],
}

const ESPECIALIDADES = ['Nutricionista deportivo', 'Fisioterapeuta', 'Entrenador personal']

const initialUploads = {
  foto: null,
  certFile: null,
  certTitle: '',
}

const toNumberOrNull = (value) => {
  if (value === '') return null
  const parsed = Number(value)
  return Number.isNaN(parsed) ? null : parsed
}

const getStoredSession = () => {
  try {
    return JSON.parse(localStorage.getItem('axon_session') || 'null')
  } catch {
    return null
  }
}

const fileToBase64 = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = typeof reader.result === 'string' ? reader.result : ''
      resolve(result.split(',')[1] || '')
    }
    reader.onerror = () => reject(new Error('No se pudo leer el archivo.'))
    reader.readAsDataURL(file)
  })

function RegisterProfessionalWizard() {
  const [step, setStep] = useState(1)
  const [account, setAccount] = useState(initialAccount)
  const [profile, setProfile] = useState(initialProfile)
  const [uploads, setUploads] = useState(initialUploads)
  const [loading, setLoading] = useState(false)
  const [session, setSession] = useState(getStoredSession())
  const [status, setStatus] = useState({ type: 'idle', message: '' })

  const token = session?.token || ''

  const authConfig = token
    ? { headers: { Authorization: `Bearer ${token}` } }
    : undefined

  const ciudadesDisponibles = DEPARTAMENTOS_COLOMBIA[profile.departamento] || []

  const handleAccountChange = ({ target }) => {
    const { name, value } = target
    setAccount((current) => ({ ...current, [name]: value }))
  }

  const handleProfileChange = ({ target }) => {
    const { name, value } = target
    setProfile((current) => {
      if (name === 'departamento') {
        return { ...current, departamento: value, ciudad: '' }
      }
      return { ...current, [name]: value }
    })
  }

  const handleUploadChange = ({ target }) => {
    const { name, value, files } = target
    if (files) {
      setUploads((current) => ({ ...current, [name]: files[0] ?? null }))
      return
    }
    setUploads((current) => ({ ...current, [name]: value }))
  }

  const handleAccountSubmit = async (event) => {
    event.preventDefault()

    if (!account.nombre.trim() || !account.email.trim() || !account.password.trim()) {
      setStatus({ type: 'error', message: 'Nombre, correo y contraseña son obligatorios.' })
      return
    }

    if (account.password !== account.confirmPassword) {
      setStatus({ type: 'error', message: 'La confirmación de contraseña no coincide.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post('/auth/register_profesional', {
        nombre: account.nombre.trim(),
        email: account.email.trim().toLowerCase(),
        password: account.password,
      })

      localStorage.setItem('axon_session', JSON.stringify(data))
      setSession(data)
      setStep(2)
      setStatus({
        type: 'success',
        message: 'Felicitaciones, tu cuenta fue creada. Continuemos con tu registro profesional.',
      })
    } catch (error) {
      const backendDetail = error.response?.data?.detail
      const message = backendDetail || (error.code === 'ECONNABORTED'
        ? 'El backend tardó demasiado en responder.'
        : error.request
          ? 'No se pudo conectar con el backend. Revisa backend, puerto y CORS.'
          : error.message || 'No se pudo completar el primer paso del registro.')

      setStatus({
        type: 'error',
        message,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleProfileSubmit = async (event) => {
    event.preventDefault()

    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para continuar el registro.' })
      return
    }

    if (!profile.departamento.trim() || !profile.ciudad.trim() || !profile.metodologia.trim()) {
      setStatus({
        type: 'error',
        message: 'Departamento, ciudad y metodología son obligatorios.',
      })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      await api.post(
        '/me/profile',
        {
          cambios: {
            departamento: profile.departamento.trim(),
            ciudad: profile.ciudad.trim(),
            metodologia: profile.metodologia.trim(),
            tarifa_unidad: profile.tarifaUnidad || 'sesion',
            tarifa: toNumberOrNull(profile.tarifa),
            especialidad: profile.especialidad.trim() || null,
            universidad: profile.universidad.trim() || null,
            experiencia: toNumberOrNull(profile.experiencia),
          },
        },
        authConfig,
      )

      setStep(3)
      setStatus({
        type: 'success',
        message: 'Perfecto. Ahora sube tu foto y tus certificaciones.',
      })
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error.response?.data?.detail ||
          'No se pudo guardar la información del perfil profesional.',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleUploadsSubmit = async (event) => {
    event.preventDefault()

    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para finalizar el registro.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      if (uploads.foto) {
        const fotoB64 = await fileToBase64(uploads.foto)
        await api.post(
          '/me/foto',
          {
            foto_b64: fotoB64,
            foto_mime: uploads.foto.type || null,
          },
          authConfig,
        )
      }

      if (uploads.certFile) {
        const certB64 = await fileToBase64(uploads.certFile)
        await api.post(
          '/me/certificaciones',
          {
            titulo: uploads.certTitle.trim() || uploads.certFile.name,
            archivo_b64: certB64,
            archivo_mime: uploads.certFile.type || null,
          },
          authConfig,
        )
      }

      setStep(4)
      setStatus({
        type: 'success',
        message: 'Registro profesional completado correctamente.',
      })
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error.response?.data?.detail ||
          'No se pudo finalizar la carga de archivos.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="app-card app-card--wide login-card">
        <Link to="/login" className="back-link">← Volver</Link>
        <p className="app-kicker">Axon Registro</p>
        <h1 className="app-title">Registro profesional</h1>
        <p className="app-text">
          {step === 1 && 'Paso 1 de 3: crea tu cuenta con los datos básicos.'}
          {step === 2 && 'Paso 2 de 3: completa tu perfil profesional.'}
          {step === 3 && 'Paso 3 de 3: sube tu foto y tus certificaciones.'}
          {step === 4 && 'Tu perfil quedó listo para continuar dentro de la app.'}
        </p>

        {step === 1 && (
          <form className="login-form" onSubmit={handleAccountSubmit}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="nombre">Nombre completo</label>
                <input
                  id="nombre"
                  name="nombre"
                  type="text"
                  value={account.nombre}
                  onChange={handleAccountChange}
                  placeholder="Tu nombre completo"
                />
              </div>

              <div className="login-field">
                <label htmlFor="email">Correo electrónico</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={account.email}
                  onChange={handleAccountChange}
                  placeholder="correo@ejemplo.com"
                />
              </div>

              <div className="login-field">
                <label htmlFor="password">Contraseña</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={account.password}
                  onChange={handleAccountChange}
                  placeholder="Tu contraseña"
                />
              </div>

              <div className="login-field full">
                <label htmlFor="confirmPassword">Verificar contraseña</label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={account.confirmPassword}
                  onChange={handleAccountChange}
                  placeholder="Repite tu contraseña"
                />
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>
                {status.message}
              </p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Creando cuenta...' : 'Continuar'}
              </button>

              <Link to="/login" className="register-link secondary">
                Volver al login
              </Link>
            </div>
          </form>
        )}

        {step === 2 && (
          <form className="login-form" onSubmit={handleProfileSubmit}>
            <div className="form-grid">
              <div className="login-field">
                <label htmlFor="departamento">Departamento</label>
                <select
                  id="departamento"
                  name="departamento"
                  value={profile.departamento}
                  onChange={handleProfileChange}
                >
                  <option value="">Selecciona un departamento</option>
                  {Object.keys(DEPARTAMENTOS_COLOMBIA).map((depto) => (
                    <option key={depto} value={depto}>{depto}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="ciudad">Ciudad o municipio</label>
                <select
                  id="ciudad"
                  name="ciudad"
                  value={profile.ciudad}
                  onChange={handleProfileChange}
                  disabled={!profile.departamento}
                >
                  <option value="">{profile.departamento ? 'Selecciona una ciudad' : 'Primero selecciona un departamento'}</option>
                  {ciudadesDisponibles.map((ciudad) => (
                    <option key={ciudad} value={ciudad}>{ciudad}</option>
                  ))}
                </select>
              </div>

              <div className="login-field full">
                <label htmlFor="metodologia">Metodología de trabajo</label>
                <textarea
                  id="metodologia"
                  name="metodologia"
                  value={profile.metodologia}
                  onChange={handleProfileChange}
                  placeholder="Describe tu forma de trabajar"
                />
              </div>

              <div className="login-field">
                <label htmlFor="tarifaUnidad">Trabajo por</label>
                <select
                  id="tarifaUnidad"
                  name="tarifaUnidad"
                  value={profile.tarifaUnidad}
                  onChange={handleProfileChange}
                >
                  <option value="sesion">Sesión</option>
                  <option value="semana">Semana</option>
                  <option value="mes">Mes</option>
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="tarifa">Precio de trabajo</label>
                <input
                  id="tarifa"
                  name="tarifa"
                  type="number"
                  min="0"
                  step="0.01"
                  value={profile.tarifa}
                  onChange={handleProfileChange}
                  placeholder="Ej: 120000"
                />
              </div>

              <div className="login-field">
                <label htmlFor="especialidad">Especialidad</label>
                <select
                  id="especialidad"
                  name="especialidad"
                  value={profile.especialidad}
                  onChange={handleProfileChange}
                >
                  <option value="">Selecciona una especialidad</option>
                  {ESPECIALIDADES.map((especialidad) => (
                    <option key={especialidad} value={especialidad}>{especialidad}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="universidad">Universidad</label>
                <input
                  id="universidad"
                  name="universidad"
                  type="text"
                  value={profile.universidad}
                  onChange={handleProfileChange}
                  placeholder="Tu universidad o institución"
                />
              </div>

              <div className="login-field full">
                <label htmlFor="experiencia">Años de experiencia</label>
                <input
                  id="experiencia"
                  name="experiencia"
                  type="number"
                  min="0"
                  value={profile.experiencia}
                  onChange={handleProfileChange}
                  placeholder="Ej: 5"
                />
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>
                {status.message}
              </p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Guardando...' : 'Siguiente'}
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form className="login-form" onSubmit={handleUploadsSubmit}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="foto">Subir foto de perfil</label>
                <input
                  id="foto"
                  name="foto"
                  type="file"
                  accept="image/*"
                  onChange={handleUploadChange}
                />
              </div>

              <div className="login-field">
                <label htmlFor="certTitle">Título del certificado</label>
                <input
                  id="certTitle"
                  name="certTitle"
                  type="text"
                  value={uploads.certTitle}
                  onChange={handleUploadChange}
                  placeholder="Diploma, certificación, curso..."
                />
              </div>

              <div className="login-field">
                <label htmlFor="certFile">Subir certificación o diploma</label>
                <input
                  id="certFile"
                  name="certFile"
                  type="file"
                  accept=".pdf,image/*"
                  onChange={handleUploadChange}
                />
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>
                {status.message}
              </p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Finalizando...' : 'Finalizar registro'}
              </button>
            </div>
          </form>
        )}

        {step === 4 && (
          <>
            <p className="form-status is-success">
              Tu perfil profesional quedó creado y completado.
            </p>

            <div className="form-actions">
              <Link to="/login" className="register-link">
                Ir al login
              </Link>
            </div>
          </>
        )}
      </section>
    </main>
  )
}

export default RegisterProfessionalWizard