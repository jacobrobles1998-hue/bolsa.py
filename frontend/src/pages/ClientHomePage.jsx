import { useEffect, useState } from "react"
import api from '../services/api.js'
import ProfessionalCard from '../components/professionals/professionalcard.jsx'

function ClientHomePage() {

    const [profesionales, setProfesionales] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState ('')


useEffect (() => {
    const token = JSON.parse(localStorage.getItem('axon_session') || 'null')?.token
    const config = token ? {headers: {Authorization: `Bearer ${token}`} } : {}

    api.get('/profesionales?solo-verificados=falso', config)
    .then(({data}) => {
        console.log('PROFESIONALES:', data)
         setProfesionales(data.items || [])}) 
    .catch(() => setError('aun no hay perfil de profesionales...'))
    .finally(() => setLoading(false))
}, [])

if (loading) return <p className="app-text">cargando profesionales...</p>
if (error) return <p className="app-text">{error}</p>

return (
    <div className="home-page">
        <h1 className="app-tittle">profesional</h1>
        <div className="profesional-grid">
            {profesionales.map((pro) => (
                <ProfessionalCard key={pro.id} pro={pro} />
            ))}
        </div>
    </div>
)

}
export default ClientHomePage












