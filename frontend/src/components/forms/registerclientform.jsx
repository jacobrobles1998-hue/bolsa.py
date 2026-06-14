import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import api from '../../services/api.js'
import { DEPARTAMENTOS_COLOMBIA } from '../../utils/professionalCatalogs.js'

const GENEROS = ['Masculino', 'Femenino', 'Otro']

const initialAccount = {
  nombre: '',
  email: '',
  password: '',
  confirmPassword: '',
}

const initialClient = {
  genero: '',
  edad: '',
  altura: '',
  peso: '',
  departamento: '',
  ciudad: '',
  tienePatologia: 'No',
  patologia: '',
}

const getStoredSession = () => {
  try {
    return JSON.parse(localStorage.getItem('axon_session') || 'null')
  } catch {
    return null
  }
}

const clearStoredSession = () => {
  try {
    localStorage.removeItem('axon_session')
  } catch {
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

const isClientRegistrationComplete = (session) => {
  const p = session?.profile || {}
  return Boolean(session?.token && p.foto_b64)
}

const getInitialStepFromSession = (session) => {
  if (!session?.token) return 1
  const p = session.profile || {}
  const hasStep2 = p.genero || p.edad != null || p.altura != null || p.peso != null
  const hasStep3 = p.departamento && p.ciudad
  const hasPhoto = Boolean(p.foto_b64)
  if (hasPhoto) return 5
  if (hasStep3) return 4
  if (hasStep2) return 3
  return 2
}

function RegisterClientForm() {
  const [session, setSession] = useState(getStoredSession())
  const [step, setStep] = useState(() => getInitialStepFromSession(getStoredSession()))
  const [client, setClient] = useState(initialClient)
  const [foto, setFoto] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: 'idle', message: '' })

  const {
    register: registerAccount,
    handleSubmit: handleAccountFormSubmit,
    watch: watchAccount,
    reset: resetAccountForm,
  } = useForm({
    defaultValues: initialAccount,
  })

  const {
    register: registerStep2,
    handleSubmit: handleStep2FormSubmit,
    reset: resetStep2Form,
  } = useForm({
    defaultValues: {
      genero: initialClient.genero,
      edad: initialClient.edad,
      altura: initialClient.altura,
      peso: initialClient.peso,
    },
  })

  const {
    register: registerStep3,
    handleSubmit: handleStep3FormSubmit,
    watch: watchStep3,
    reset: resetStep3Form,
    setValue: setStep3Value,
  } = useForm({
    defaultValues: {
      departamento: initialClient.departamento,
      ciudad: initialClient.ciudad,
      tienePatologia: initialClient.tienePatologia,
      patologia: initialClient.patologia,
    },
  })

  const {
    handleSubmit: handleStep4FormSubmit,
  } = useForm()

  const token = session?.token || ''
  const authConfig = token ? { headers: { Authorization: `Bearer ${token}` } } : undefined

  const watchedDepartamento = watchStep3('departamento') || ''
  const watchedTienePatologia = watchStep3('tienePatologia') || 'No'
  const ciudadesDisponibles = DEPARTAMENTOS_COLOMBIA[watchedDepartamento] || []

  useEffect(() => {
    const storedSession = getStoredSession()
    if (!isClientRegistrationComplete(storedSession)) return

    clearStoredSession()
    setSession(null)
    setStep(1)
    setClient(initialClient)
    setFoto(null)
    resetAccountForm(initialAccount)
    resetStep2Form({
      genero: initialClient.genero,
      edad: initialClient.edad,
      altura: initialClient.altura,
      peso: initialClient.peso,
    })
    resetStep3Form({
      departamento: initialClient.departamento,
      ciudad: initialClient.ciudad,
      tienePatologia: initialClient.tienePatologia,
      patologia: initialClient.patologia,
    })
    setStatus({ type: 'idle', message: '' })
  }, [resetAccountForm, resetStep2Form, resetStep3Form])

  useEffect(() => {
    let cancelled = false

    const syncSession = async () => {
      if (!token || !authConfig) return
      try {
        const { data } = await api.get('/me', authConfig)
        if (cancelled) return
        const nextSession = { ...session, profile: data?.profile || session?.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
        setStep(getInitialStepFromSession(nextSession))
      } catch (error) {
        if (cancelled) return
        if (error?.response?.status === 401) {
          clearStoredSession()
          setSession(null)
          setStatus({ type: 'idle', message: '' })
          setStep(1)
        }
      }
    }

    syncSession()
    return () => {
      cancelled = true
    }
  }, [token])

  const handleBack = () => {
    if (step > 1 && step < 5) {
      setStatus({ type: 'idle', message: '' })
      setStep((current) => Math.max(1, current - 1))
    }
  }

  const handleClientChange = ({ target }) => {
    const { name, value } = target
    setClient((current) => {
      if (name === 'departamento') return { ...current, departamento: value, ciudad: '' }
      if (name === 'tienePatologia') return { ...current, tienePatologia: value, patologia: value === 'Si' ? current.patologia : '' }
      return { ...current, [name]: value }
    })
  }

  const handleStep1Submit = async (values) => {
    const nombre = (values?.nombre || '').trim()
    const email = (values?.email || '').trim().toLowerCase()
    const password = values?.password || ''

    if (!nombre || !email || !password) {
      setStatus({ type: 'error', message: 'Nombre, correo y contraseña son obligatorios.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post('/auth/register_cliente', {
        nombre,
        email,
        password,
      })

      localStorage.setItem('axon_session', JSON.stringify(data))
      setSession(data)
      setStep(2)
      resetAccountForm(initialAccount)
      setStatus({ type: 'success', message: 'Felicitaciones, tu cuenta fue creada. Continuemos con tu registro.' })
    } catch (error) {
      const backendDetail = error.response?.data?.detail
      const message = backendDetail || (error.request ? 'No se pudo conectar con el backend.' : error.message || 'No se pudo crear la cuenta.')
      setStatus({ type: 'error', message })
    } finally {
      setLoading(false)
    }
  }

  const handleStep2Submit = async (values) => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para continuar.' })
      return
    }

    const genero = values?.genero || ''
    const edad = values?.edad ?? ''
    const altura = values?.altura ?? ''
    const peso = values?.peso ?? ''

    if (!genero) {
      setStatus({ type: 'error', message: 'Selecciona género.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const cambios = {
        genero: genero || null,
        edad: edad === '' ? null : Number(edad),
        altura: altura === '' ? null : Number(altura),
        peso: peso === '' ? null : Number(peso),
      }

      const { data } = await api.post('/me/profile', { cambios }, authConfig)

      const nextClient = {
        ...client,
        genero,
        edad: `${edad ?? ''}`,
        altura: `${altura ?? ''}`,
        peso: `${peso ?? ''}`,
      }
      setClient(nextClient)
      resetStep2Form(nextClient)

      if (data?.profile) {
        const nextSession = { ...session, profile: data.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
      }

      setStep(3)
      setStatus({ type: 'success', message: 'Perfecto. Sigamos.' })
    } catch (error) {
      setStatus({ type: 'error', message: error.response?.data?.detail || 'No se pudo guardar la información.' })
    } finally {
      setLoading(false)
    }
  }

  const handleStep3Submit = async (values) => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para continuar.' })
      return
    }

    const departamento = values?.departamento || ''
    const ciudad = values?.ciudad || ''
    const tienePatologia = values?.tienePatologia || 'No'
    const patologia = (values?.patologia || '').trim()

    if (!departamento || !ciudad) {
      setStatus({ type: 'error', message: 'Departamento y ciudad son obligatorios.' })
      return
    }
    if (tienePatologia === 'Si' && !patologia) {
      setStatus({ type: 'error', message: 'Escribe tu patología o condición.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const cambios = {
        departamento,
        ciudad,
        patologia_familiar: tienePatologia === 'Si' ? patologia : null,
      }

      const { data } = await api.post('/me/profile', { cambios }, authConfig)

      const nextClient = {
        ...client,
        departamento,
        ciudad,
        tienePatologia,
        patologia,
      }
      setClient(nextClient)
      resetStep3Form(nextClient)

      if (data?.profile) {
        const nextSession = { ...session, profile: data.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
      }

      setStep(4)
      setStatus({ type: 'success', message: 'Perfecto. Ahora sube tu foto de perfil.' })
    } catch (error) {
      setStatus({ type: 'error', message: error.response?.data?.detail || 'No se pudo guardar la información.' })
    } finally {
      setLoading(false)
    }
  }

  const handleStep4Submit = async () => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para finalizar.' })
      return
    }
    if (!foto) {
      setStatus({ type: 'error', message: 'Sube una foto de perfil.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const fotoB64 = await fileToBase64(foto)
      await api.post('/me/foto', { foto_b64: fotoB64, foto_mime: foto.type || null }, authConfig)
      setStep(5)
      setStatus({ type: 'success', message: 'Registro de cliente completado correctamente.' })
    } catch (error) {
      setStatus({ type: 'error', message: error.response?.data?.detail || 'No se pudo subir la foto.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="app-card app-card--wide login-card">
        {step === 1 || step === 5 ? (
          <Link to="/login" className="back-link">← Volver</Link>
        ) : (
          <button type="button" className="back-link back-button" onClick={handleBack}>← Volver</button>
        )}

        <p className="app-kicker">Axon Registro</p>
        <h1 className="app-title">Registro de cliente</h1>

        <p className="app-text">
          {step === 1 && 'Paso 1 de 4: crea tu cuenta.'}
          {step === 2 && 'Paso 2 de 4: edad, altura, género y peso.'}
          {step === 3 && 'Paso 3 de 4: ubicación y patología.'}
          {step === 4 && 'Paso 4 de 4: sube tu foto de perfil.'}
          {step === 5 && 'Tu perfil quedó listo para continuar dentro de la app.'}
        </p>

        {step === 1 && (
          <form className="login-form" onSubmit={handleAccountFormSubmit(handleStep1Submit)}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="nombre">Nombre completo</label>
                <input id="nombre" 
                type="text"
                placeholder="Nombre completo"
                {...registerAccount('nombre', { required: true })} />
              </div>

              <div className="login-field">
                <label htmlFor="email">Correo electrónico</label>
                <input id="email" 
                type="email"
                placeholder="Correo electrónico"
                {...registerAccount('email', { required: true })} />
              </div>

              <div className="login-field">
                <label htmlFor="password">Contraseña</label>
                <input id="password" 
                type="password"
                placeholder="Contraseña"
                autoComplete="new-password"
                {...registerAccount('password', { required: true })} />
              </div>

              <div className="login-field full">
                <label htmlFor="confirmPassword">Verificar contraseña</label>
                <input
                  id="confirmPassword" 
                  type="password"
                  placeholder="repite tu contraseña"
                  autoComplete="new-password"
                  {...registerAccount('confirmPassword', {
                    required: true,
                    validate: (value) => value === (watchAccount('password') || ''),
                  })}
                />
                
                
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>{status.message}</p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Creando...' : 'Continuar'}
              </button>
            </div>
          </form>
        )}

        {step === 2 && (
          <form className="login-form" onSubmit={handleStep2FormSubmit(handleStep2Submit)}>
            <div className="form-grid">
              <div className="login-field">
                <label htmlFor="edad">Edad</label>
                <input id="edad" 
                placeholder="27"
                {...registerStep2('edad')} 
                type="number" min="0" {...registerStep2('edad')} />
              </div>

              <div className="login-field">
                <label htmlFor="altura">Altura</label>
                <input id="altura" 
                placeholder="Altura"
                {...registerStep2('altura')} 
                type="number" step="0.01" min="0" placeholder="Ej: 1.72" {...registerStep2('altura')} />
              </div>

              <div className="login-field">
                <label htmlFor="genero">Género</label>
                <select id="genero" placeholder="Selecciona género" {...registerStep2('genero')}>
                  <option value="">Selecciona género</option>
                  {GENEROS.map((g) => (
                    <option key={g} value={g.toLowerCase()}>{g}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="peso">Peso</label>
                <input id="peso" type="number" step="0.01" min="0" placeholder="Ej: 70" {...registerStep2('peso')} />
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>{status.message}</p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Guardando...' : 'Siguiente'}
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form className="login-form" onSubmit={handleStep3FormSubmit(handleStep3Submit)}>
            <div className="form-grid">
              <div className="login-field">
                <label htmlFor="departamento">Departamento</label>
                <select
                  id="departamento"
                  {...registerStep3('departamento', {
                    onChange: () => {
                      setStep3Value('ciudad', '')
                    },
                  })}
                >
                  <option value="">Selecciona un departamento</option>
                  {Object.keys(DEPARTAMENTOS_COLOMBIA).map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="ciudad">Ciudad o municipio</label>
                <select id="ciudad" placeholder="Selecciona una ciudad" {...registerStep3('ciudad')} disabled={!watchedDepartamento}>
                  <option value="">{watchedDepartamento ? 'Selecciona una ciudad' : 'Primero selecciona un departamento'}</option>
                  {ciudadesDisponibles.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="tienePatologia">¿Tienes alguna patología?</label>
                <select
                  id="tienePatologia"
                  placeholder="¿Tienes alguna patología?"
                  {...registerStep3('tienePatologia', {
                    onChange: (event) => {
                      if (event.target.value !== 'Si') setStep3Value('patologia', '')
                    },
                  })}
                >
                  <option value="No">No</option>
                  <option value="Si">Si</option>
                </select>
              </div>

              {watchedTienePatologia === 'Si' ? (
                <div className="login-field full">
                  <label htmlFor="patologia">¿Cuál patología o condición?</label>
                  <textarea id="patologia" placeholder="Esto se verá en tu perfil" {...registerStep3('patologia')} />
                </div>
              ) : null}
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>{status.message}</p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Guardando...' : 'Siguiente'}
              </button>
            </div>
          </form>
        )}

        {step === 4 && (
          <form className="login-form" onSubmit={handleStep4FormSubmit(handleStep4Submit)}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="foto">Subir foto de perfil</label>
                <input id="foto" name="foto" type="file" accept="image/*" placeholder="Subir foto" onChange={(e) => setFoto(e.target.files?.[0] ?? null)} />
              </div>
            </div>

            {status.message ? (
              <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>{status.message}</p>
            ) : null}

            <div className="form-actions">
              <button type="submit" className="login-button" disabled={loading}>
                {loading ? 'Finalizando...' : 'Finalizar registro'}
              </button>
            </div>
          </form>
        )}

        {step === 5 && (
          <>
            <p className="form-status is-success">{status.message || 'Registro de cliente completado correctamente.'}</p>
            <div className="form-actions">
              <Link to="/login" className="register-link">Ir al login</Link>
            </div>
          </>
        )}
      </section>
    </main>
  )
}

export default RegisterClientForm
