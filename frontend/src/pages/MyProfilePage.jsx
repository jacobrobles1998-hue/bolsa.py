import { useNavigate } from "react-router-dom";

function ClientePerfilPage() {
    const navigate = useNavigate()

    const handleLogout = () => {
        localStorage.removeItem('axon_session')
        navigate('/login')
    }

    return (
        <div className="perfil-page">
            <h1 className="app-tittle">mi perfil</h1>
            <button calssName="logout-btn" onClick={handleLogout}>
                cerrar sesión
            </button>
        </div>
    )


}
export default ClientePerfilPage
