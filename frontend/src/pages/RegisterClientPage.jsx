import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api.js'

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
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: 'idle', message: '' })

  const handleChange = ({ target }) => {
    const { name, value } = target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!form.nombre.trim() || !form.email.trim() || !form.password.trim()) {
      setStatus({
        type: 'error',
        message: 'Nombre, correo y contraseña son obligatorios.',
      })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const payload = {
        nombre: form.nombre.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        telefono: form.telefono.trim() || null,
        departamento: form.departamento.trim() || null,
        ciudad: form.ciudad.trim() || null,
        genero: form.genero || null,
        edad: toNumberOrNull(form.edad),
        altura: toNumberOrNull(form.altura),
        peso: toNumberOrNull(form.peso),
        patologia_familiar: form.patologia_familiar.trim() || null,
        metodologia: form.metodologia.trim() || null,
      }

      const { data } = await api.post('/auth/register_cliente', payload)
      localStorage.setItem('axon_session', JSON.stringify(data))

      setStatus({
        type: 'success',
        message: 'Cliente registrado correctamente. La sesión quedó guardada.',
      })

      setForm(initialForm)
    } catch (error) {
      setStatus({
        type: 'error',
        message:
          error.response?.data?.detail ||
          'No se pudo completar el registro del cliente.',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="app-card app-card--wide login-card">
        <p className="app-kicker">Axon Registro</p>
        <h1 className="app-title">Registro de cliente</h1>
        <p className="app-text">
          Este formulario envía los datos reales al endpoint
          {' '}
          /auth/register_cliente
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="login-field">
              <label htmlFor="nombre">Nombre completo</label>
              <input id="nombre" name="nombre" type="text" value={form.nombre} onChange={handleChange} placeholder="Tu nombre" />
            </div>

            <div className="login-field">
              <label htmlFor="email">Correo electrónico</label>
              <input id="email" name="email" type="email" value={form.email} onChange={handleChange} placeholder="correo@ejemplo.com" />
            </div>

            <div className="login-field">
              <label htmlFor="password">Contraseña</label>
              <input id="password" name="password" type="password" value={form.password} onChange={handleChange} placeholder="Tu contraseña" />
            </div>

            <div className="login-field">
              <label htmlFor="telefono">Teléfono</label>
              <input id="telefono" name="telefono" type="text" value={form.telefono} onChange={handleChange} placeholder="Tu teléfono" />
            </div>

            <div className="login-field">
              <label htmlFor="departamento">Departamento</label>
              <input id="departamento" name="departamento" type="text" value={form.departamento} onChange={handleChange} placeholder="Tu departamento" />
            </div>

            <div className="login-field">
              <label htmlFor="ciudad">Ciudad</label>
              <input id="ciudad" name="ciudad" type="text" value={form.ciudad} onChange={handleChange} placeholder="Tu ciudad" />
            </div>

            <div className="login-field">
              <label htmlFor="genero">Género</label>
              <select id="genero" name="genero" value={form.genero} onChange={handleChange}>
                {generoOptions.map((option) => (
                  <option key={option.value || 'empty'} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="login-field">
              <label htmlFor="edad">Edad</label>
              <input id="edad" name="edad" type="number" min="0" value={form.edad} onChange={handleChange} placeholder="Tu edad" />
            </div>

            <div className="login-field">
              <label htmlFor="altura">Altura</label>
              <input id="altura" name="altura" type="number" step="0.01" min="0" value={form.altura} onChange={handleChange} placeholder="Ej: 1.72" />
            </div>

            <div className="login-field">
              <label htmlFor="peso">Peso</label>
              <input id="peso" name="peso" type="number" step="0.01" min="0" value={form.peso} onChange={handleChange} placeholder="Ej: 70" />
            </div>

            <div className="login-field full">
              <label htmlFor="patologia_familiar">Patología familiar</label>
              <textarea id="patologia_familiar" name="patologia_familiar" value={form.patologia_familiar} onChange={handleChange} placeholder="Cuéntanos si hay alguna patología familiar relevante" />
            </div>

            <div className="login-field full">
              <label htmlFor="metodologia">Metodología / objetivo</label>
              <textarea id="metodologia" name="metodologia" value={form.metodologia} onChange={handleChange} placeholder="Objetivos, hábitos, rutina o metodología deseada" />
            </div>
          </div>

          {status.message ? (
            <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>
              {status.message}
            </p>
          ) : null}

          <div className="form-actions">
            <button type="submit" className="login-button" disabled={loading}>
              {loading ? 'Registrando...' : 'Crear cuenta cliente'}
            </button>

            <Link to="/login" className="register-link secondary">
              Volver al login
            </Link>
          </div>
        </form>
      </section>
    </main>
  )
}

export default RegisterClientPage