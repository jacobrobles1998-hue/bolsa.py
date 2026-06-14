import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api.js'

function LoginPages() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: 'idle', message: '' })

  const handleChange = ({ target }) => {
    const { name, value } = target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!form.email.trim() || !form.password.trim()) {
      setStatus({ type: 'error', message: 'Escribe tu correo y tu contraseña.' })
      return
    }

    setLoading(true)
    setStatus({ type: 'idle', message: '' })

    try {
      const { data } = await api.post('/auth/login', {
        email: form.email.trim().toLowerCase(),
        password: form.password,
      })

      localStorage.setItem('axon_session', JSON.stringify(data))
      setStatus({
        type: 'success',
        message: `Bienvenido${data?.profile?.nombre ? `, ${data.profile.nombre}` : ''}. Ya quedó conectado con el backend.`,
      })
    } catch (error) {
      const backendDetail = error.response?.data?.detail
      const message = backendDetail || (error.code === 'ECONNABORTED'
        ? 'El backend tardó demasiado en responder.'
        : error.request
          ? 'No se pudo conectar con el backend en 8001. Verifica que esté corriendo.'
          : error.message || 'No se pudo iniciar sesión.')

      setStatus({
        type: 'error',
        message,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="app-card login-card">
        <p className="app-kicker">Axon Login</p>
        <h1 className="app-title">Bienvenido</h1>
        <p className="app-text">Conectamos entrenadores personalizados, nutricionistas deportivos y fisioterapeutas con personas que quieren resultados reales.</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="email">Correo electrónico</label>
            <input id="email" name="email" type="email" placeholder="Tu correo" autoComplete="email" value={form.email} onChange={handleChange} />
          </div>

          <div className="login-field">
            <label htmlFor="password">Contraseña</label>
            <input id="password" name="password" type="password" placeholder="Tu contraseña" autoComplete="current-password" value={form.password} onChange={handleChange} />
          </div>

          {status.message ? <p className={`form-status ${status.type === 'error' ? 'is-error' : 'is-success'}`}>{status.message}</p> : null}

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <div className="register-actions">
          <Link to="/registro-cliente" className="register-link">Registrarme como cliente</Link>
          <Link to="/registro-profesional" className="register-link secondary">Registrarme como profesional</Link>
        </div>
      </section>
    </main>
  )
}

export default LoginPages
