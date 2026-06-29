import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from '../pages/LoginPages.jsx'
import RegisterClientPage from '../pages/RegisterClientPage.jsx'
import RegisterProfessionalPage from '../pages/RegisterProfessionalPage.jsx'
import Appshell from '../components/layout/appshell.jsx'
import ClientHomePage from '../pages/ClientHomePage.jsx'
import InboxPage from '../pages/InboxPage.jsx'
import ClientePerfilPage from '../pages/ClientePerfilPage.jsx'


function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro-cliente" element={<RegisterClientPage />} />
        <Route path="/registro-profesional" element={<RegisterProfessionalPage />} />

        <Route path="/cliente" element={<Appshell/>}>
          <Route index element={<Navigate to="inicio"  replace />} />
          <Route path="inicio" element={<ClientHomePage />} />
          <Route path="chat" element={<InboxPage />} />
          <Route path="contratos" element={<div> contratos proximamanete</div>} />
          <Route path="perfil" element={<ClientePerfilPage />} />

        </Route>       
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default AppRouter