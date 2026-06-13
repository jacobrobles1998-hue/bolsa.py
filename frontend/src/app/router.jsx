import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from '../pages/LoginPages.jsx'
import RegisterClientPage from '../pages/RegisterClientPage.jsx'
import RegisterProfessionalPage from '../pages/RegisterProfessionalPage.jsx'

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro-cliente" element={<RegisterClientPage />} />
        <Route path="/registro-profesional" element={<RegisterProfessionalPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default AppRouter