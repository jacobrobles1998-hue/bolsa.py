import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import api from '../../services/api.js'
import { DEPARTAMENTOS_COLOMBIA, ESPECIALIDADES, ORIGEN_FORMACION, getUniversidadesDisponibles } from '../../utils/professionalCatalogs.js'

const initialAccount = {
  nombre: '',
  email: '',
  password: '',
  confirmPassword: '',
}

const initialProfile = {
  departamento: '',
  ciudad: '',
  especialidad: '',
  origenFormacion: 'En Colombia',
  universidad: '',
  metodologia: '',
  tarifaUnidad: 'sesion',
  tarifa: '',
  experiencia: '',
}

const initialUploads = {
  foto: null,
  certFile: null,
  certTitle: '',
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
  } catch (error){
    console.error("error al limpiar sesion", error);
   }
  }


const isProfessionalRegistrationComplete = (session) => {
  const p = session?.profile || {}
  return Boolean(
    session?.token &&
    p.departamento &&
    p.ciudad &&
    p.especialidad &&
    p.universidad &&
    p.metodologia &&
    p.experiencia != null &&
    p.tarifa != null
  )
}

const getInitialStepFromSession = (session) => {
  if (!session?.token) return 1
  const profile = session.profile || {}
  if (profile.departamento && profile.ciudad && profile.especialidad && profile.universidad) return 3
  return 2
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
  const [session, setSession] = useState(getStoredSession())
  const [step, setStep] = useState(() => getInitialStepFromSession(getStoredSession()))
  const [profile, setProfile] = useState(initialProfile)
  const [uploads, setUploads] = useState(initialUploads)
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
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
    register: registerProfile,
    handleSubmit: handleProfileFormSubmit,
    watch: watchProfile,
    reset: resetProfileForm,
    setValue: setProfileValue,
  } = useForm({
    defaultValues: initialProfile,
  })

  const {
    register: registerMedia,
    handleSubmit: handleMediaFormSubmit,
    reset: resetMediaForm,
  } = useForm({
    defaultValues: {
      metodologia: initialProfile.metodologia,
      certTitle: initialUploads.certTitle,
    },
  })

  const {
    register: registerPricing,
    handleSubmit: handlePricingFormSubmit,
    reset: resetPricingForm,
  } = useForm({
    defaultValues: {
      experiencia: initialProfile.experiencia,
      tarifaUnidad: initialProfile.tarifaUnidad,
      tarifa: initialProfile.tarifa,
    },
  })


  const token = session?.token || ''

  const authConfig = token
    ? { headers: { Authorization: `Bearer ${token}` } }
    : undefined

  useEffect(() => {
    const storedSession = getStoredSession()
    if (!isProfessionalRegistrationComplete(storedSession)) return

    clearStoredSession()
    setSession(null)
    setStep(1)
    setProfile(initialProfile)
    setUploads(initialUploads)
    setShowPassword(false)
    resetAccountForm(initialAccount)
    resetProfileForm(initialProfile)
    resetMediaForm({
      metodologia: initialProfile.metodologia,
      certTitle: initialUploads.certTitle,
    })
    resetPricingForm({
      experiencia: initialProfile.experiencia,
      tarifaUnidad: initialProfile.tarifaUnidad,
      tarifa: initialProfile.tarifa,
    })
    setStatus({ type: 'idle', message: '' })
  }, [resetAccountForm, resetMediaForm, resetPricingForm, resetProfileForm])

  useEffect(() => {
    let cancelled = false

    const syncSession = async () => {
      if (!token || !authConfig) return
      try {
        const { data } = await api.get('/me', authConfig)
        if (cancelled) return

        const nextSession = { ...session, profile: data?.profile || session?.profile }
        const nextProfile = { ...initialProfile, ...(nextSession.profile || {}) }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
        setProfile(nextProfile)
        resetProfileForm(nextProfile)
        setStep(getInitialStepFromSession(nextSession))
      } catch (error) {
        if (cancelled) return
        const statusCode = error?.response?.status
        if (statusCode === 401) {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const watchedDepartamento = watchProfile('departamento') || ''
  const watchedEspecialidad = watchProfile('especialidad') || ''
  const watchedOrigenFormacion = watchProfile('origenFormacion') || 'En Colombia'

  const ciudadesDisponibles = DEPARTAMENTOS_COLOMBIA[watchedDepartamento] || []
  const requiereOrigenFormacion = watchedEspecialidad === 'Entrenador Personal' || watchedEspecialidad === 'Nutricionista Deportivo'
  const universidadesDisponibles = getUniversidadesDisponibles(watchedEspecialidad, watchedOrigenFormacion)



  const handleUploadChange = ({ target }) => {
    const { name, value, files } = target
    if (files) {
      setUploads((current) => ({ ...current, [name]: files[0] ?? null }))
      return
    }
    setUploads((current) => ({ ...current, [name]: value }))
  }

  const handleBack = () => {
    if (step > 1 && step < 5) {
      setStatus({ type: 'idle', message: '' })
      setStep((current) => Math.max(1, current - 1))
    }
  }

  const handleAccountSubmit = async (values) => {
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
      const { data } = await api.post('/auth/register_profesional', {
        nombre,
        email,
        password,
      })

      localStorage.setItem('axon_session', JSON.stringify(data))
      setSession(data)
      setStep(2)
      setShowPassword(false)
      resetAccountForm(initialAccount)
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

  const handleProfileSubmit = async (values) => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para continuar el registro.' })
      return
    }

    const departamento = (values?.departamento || '').trim()
    const ciudad = (values?.ciudad || '').trim()
    const especialidad = (values?.especialidad || '').trim()
    const universidad = (values?.universidad || '').trim()
    const origenFormacion = (values?.origenFormacion || 'En Colombia').trim()

    if (!departamento || !ciudad || !especialidad || !universidad) {
      setStatus({
        type: 'error',
        message: 'Departamento, ciudad, especialidad y formación académica son obligatorios.',
      })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post(
        '/me/profile',
        {
          cambios: {
            departamento,
            ciudad,
            especialidad,
            universidad,
          },
        },
        authConfig,
      )

      const nextProfile = {
        ...profile,
        departamento,
        ciudad,
        especialidad,
        origenFormacion,
        universidad,
      }
      setProfile(nextProfile)
      resetProfileForm(nextProfile)

      if (data?.profile) {
        const nextSession = { ...session, profile: data.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
      }

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

  const handleMediaSubmit = async (values) => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para continuar el registro.' })
      return
    }

    const metodologia = (values?.metodologia || '').trim()
    const certTitle = (values?.certTitle || '').trim()

    if (!metodologia) {
      setStatus({ type: 'error', message: 'La metodología de trabajo es obligatoria.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post('/me/profile', {
        cambios: { metodologia },
      }, authConfig)

      const nextProfile = {
        ...profile,
        metodologia,
      }
      setProfile(nextProfile)
      setUploads((current) => ({ ...current, certTitle }))
      resetMediaForm({ metodologia, certTitle })

      if (data?.profile) {
        const nextSession = { ...session, profile: data.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
      }

      if (uploads.foto) {
        const fotoB64 = await fileToBase64(uploads.foto)
        await api.post('/me/foto', {
          foto_b64: fotoB64,
          foto_mime: uploads.foto.type || null,
        }, authConfig)
      }

      if (uploads.certFile) {
        const certB64 = await fileToBase64(uploads.certFile)
        await api.post('/me/certificaciones', {
          titulo: certTitle || uploads.certFile.name,
          archivo_b64: certB64,
          archivo_mime: uploads.certFile.type || null,
        }, authConfig)
      }

      setStep(4)
      setStatus({ type: 'success', message: 'Perfecto. Ahora completa tu experiencia, modalidad y precio.' })
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'No se pudo guardar la metodología o los archivos.',
      })
    } finally {
      setLoading(false)
    }
  }

  const handlePricingSubmit = async (values) => {
    if (!token) {
      setStatus({ type: 'error', message: 'No hay sesión activa para finalizar el registro.' })
      return
    }

    const experiencia = values?.experiencia
    const tarifaUnidad = values?.tarifaUnidad || 'sesion'
    const tarifa = `${values?.tarifa ?? ''}`.trim()

    if ((experiencia === '' || experiencia == null) && experiencia !== 0) {
      setStatus({ type: 'error', message: 'Los años de experiencia son obligatorios.' })
      return
    }
    if (!tarifa) {
      setStatus({ type: 'error', message: 'El precio de trabajo es obligatorio.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post('/me/profile', {
        cambios: {
          experiencia: Number(experiencia),
          tarifa_unidad: tarifaUnidad,
          tarifa: Number(tarifa),
        },
      }, authConfig)

      const nextProfile = {
        ...profile,
        experiencia: `${experiencia ?? ''}`,
        tarifaUnidad,
        tarifa,
      }
      setProfile(nextProfile)
      resetPricingForm(nextProfile)

      if (data?.profile) {
        const nextSession = { ...session, profile: data.profile }
        localStorage.setItem('axon_session', JSON.stringify(nextSession))
        setSession(nextSession)
      }

      setStep(5)
      setStatus({ type: 'success', message: 'Registro profesional completado correctamente.' })
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'No se pudo guardar la experiencia y tarifa.',
      })
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
        <h1 className="app-title">Registro profesional</h1>
        <p className="app-text">
          {step === 1 && 'Paso 1 de 4: crea tu cuenta con los datos básicos.'}
          {step === 2 && 'Paso 2 de 4: completa tu perfil profesional.'}
          {step === 3 && 'Paso 3 de 4: agrega tu metodología, foto y certificaciones.'}
          {step === 4 && 'Paso 4 de 4: agrega tu experiencia, modalidad y precio de trabajo.'}
          {step === 5 && 'Tu perfil quedó listo para continuar dentro de la app.'}
        </p>

        {step === 1 && (
          <form className="login-form" onSubmit={handleAccountFormSubmit(handleAccountSubmit)}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="nombre">Nombre completo</label>
                <input
                  id="nombre"
                  type="text"
                  placeholder="Tu nombre completo"
                  {...registerAccount('nombre', { required: true })}
                />
              </div>

              <div className="login-field">
                <label htmlFor="email">Correo electrónico</label>
                <input
                  id="email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  {...registerAccount('email', { required: true })}
                />
              </div>

              <div className="login-field">
                <label htmlFor="password">Contraseña</label>
                <div className="password-input-wrap">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Tu contraseña"
                    autoComplete="new-password"
                    {...registerAccount('password', { required: true })}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  >
                    {showPassword ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              <div className="login-field full">
                <label htmlFor="confirmPassword">Verificar contraseña</label>
                <div className="password-input-wrap">
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Repite tu contraseña"
                    autoComplete="new-password"
                    {...registerAccount('confirmPassword', {
                      required: true,
                      validate: (value) => value === (watchAccount('password') || ''),
                    })}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  >
                    {showPassword ? '🙈' : '👁'}
                  </button>
                </div>
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
          <form className="login-form" onSubmit={handleProfileFormSubmit(handleProfileSubmit)}>
            <div className="form-grid">
              <div className="login-field">
                <label htmlFor="departamento">Departamento</label>
                <select
                  id="departamento"
                  {...registerProfile('departamento', {
                    onChange: () => {
                      setProfileValue('ciudad', '')
                    },
                  })}
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
                  {...registerProfile('ciudad')}
                  disabled={!watchedDepartamento}
                >
                  <option value="">{watchedDepartamento ? 'Selecciona una ciudad' : 'Primero selecciona un departamento'}</option>
                  {ciudadesDisponibles.map((ciudad) => (
                    <option key={ciudad} value={ciudad}>{ciudad}</option>
                  ))}
                </select>
              </div>

              <div className="login-field">
                <label htmlFor="especialidad">Especialidad</label>
                <select
                  id="especialidad"
                  placeholder="Selecciona una especialidad"
                  {...registerProfile('especialidad', {
                    onChange: () => {
                      setProfileValue('origenFormacion', 'En Colombia')
                      setProfileValue('universidad', '')
                    },
                  })}
                >
                  <option value="">Selecciona una especialidad</option>
                  {ESPECIALIDADES.map((especialidad) => (
                    <option key={especialidad} value={especialidad}>{especialidad}</option>
                  ))}
                </select>
              </div>

              {requiereOrigenFormacion ? (
                <div className="login-field">
                  <label htmlFor="origenFormacion">Dónde fue su formación académica</label>
                  <select
                    id="origenFormacion"
                    {...registerProfile('origenFormacion', {
                      onChange: () => {
                        setProfileValue('universidad', '')
                      },
                    })}
                  >
                    {ORIGEN_FORMACION.map((origen) => <option key={origen} value={origen}>{origen}</option>)}
                  </select>
                </div>
              ) : null}

              <div className={requiereOrigenFormacion ? 'login-field full' : 'login-field'}>
                <label htmlFor="universidad">Formación académica</label>
                <select id="universidad" placeholder="Selecciona una institución" {...registerProfile('universidad')} disabled={!watchedEspecialidad}>
                  <option value="">{watchedEspecialidad ? 'Selecciona una institución' : 'Primero selecciona una especialidad'}</option>
                  {universidadesDisponibles.map((universidad) => (
                    <option key={universidad} value={universidad}>{universidad}</option>
                  ))}
                </select>
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
          <form className="login-form" onSubmit={handleMediaFormSubmit(handleMediaSubmit)}>
            <div className="form-grid">
              <div className="login-field full">
                <label htmlFor="metodologia">Metodología de trabajo</label>
                <textarea
                  id="metodologia"
                  placeholder="Describe tu metodología de trabajo"
                  {...registerMedia('metodologia')}
                />
              </div>

              <div className="login-field full">
                <label htmlFor="foto">Subir foto de perfil</label>
                <input
                  id="foto"
                  name="foto"
                  type="file"
                  accept="image/*"
                  placeholder="Subir foto"
                  onChange={handleUploadChange}
                />
              </div>

              <div className="login-field">
                <label htmlFor="certTitle">Título del certificado</label>
                <input
                  id="certTitle"
                  type="text"
                  placeholder="Diploma, certificación, curso..."
                  {...registerMedia('certTitle')}
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
                {loading ? 'Guardando...' : 'Siguiente'}
              </button>
            </div>
          </form>
        )}

        {step === 4 && (
          <form className="login-form" onSubmit={handlePricingFormSubmit(handlePricingSubmit)}>
            <div className="form-grid">
              <div className="login-field">
                <label htmlFor="experiencia">Años de experiencia</label>
                <input id="experiencia" type="number" min="0" placeholder="Ej: 5" {...registerPricing('experiencia')} />
              </div>

              <div className="login-field">
                <label htmlFor="tarifaUnidad">Trabajo por</label>
                <select id="tarifaUnidad" {...registerPricing('tarifaUnidad')}>
                  <option value="sesion">Sesión</option>
                  <option value="semana">Semana</option>
                  <option value="mes">Mes</option>
                </select>
              </div>

              <div className="login-field full">
                <label htmlFor="tarifa">Precio de trabajo</label>
                <input id="tarifa" type="number" min="0" step="0.01" placeholder="Ej: 120000" {...registerPricing('tarifa')} />
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

        {step === 5 && (
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
