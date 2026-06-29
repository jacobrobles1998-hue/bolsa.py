import { NavLink } from "react-router-dom";

function Navbar() {
return(
    <nav className="bottom-navbar">
      <NavLink to="/cliente/inicio" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
        <span className="nav-icon"></span>
        <span className="nav-label">Inicio</span>
      </NavLink>

      
      <NavLink to="/cliente/chat" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
        <span className="nav-icon"></span>
        <span className="nav-label">chats</span>
      </NavLink>

      <NavLink to="/cliente/contratos" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
        <span className="nav-icon"></span>
        <span className="nav-label">contratos</span>
      </NavLink>

      <NavLink to="/cliente/perfil" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
      <span className="nav-icon"></span>
      <span className="nav-label">perfil</span>
      </NavLink>



    </nav>
)
}

export default Navbar