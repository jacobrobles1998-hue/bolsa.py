import { Outlet } from 'react-router-dom'
import Navbar from './navbar.jsx'

function Appshell() {
    return(
        <div className="appshell">
            <main className="appsahell-content">
                <Outlet />
                </main>
                <Navbar />     
        </div>
    )
}

export default Appshell