const COLORES_ESPECIALIDAD = {
    "Entrenador personalizado" : '#8E9BAE',
    "nutricionista deportivo" : '#FF6B6B',
    "fisioterapeuta" : '#5B8DEF',

}

const getInitials = (nombre) => {
    if (!nombre) return '?'
    return nombre
    .split(' ')
    .slice(0, 2)
    .map((n) => n [0]. toUpperCase())
    .join(' ')
}

    function ProfessionalCard({ pro }) {
        const color = COLORES_ESPECIALIDAD[pro.especialidad] || '#8E9BAE'
        const Initials = getInitials(pro.nombre)
        return (
            <div className ="pro-card">
                <div className ="pro-avatar" style={{ backgroundColor: color}}>
                    {Initials}
                </div>
                <div className="pro-info">
                    <p className="pro-nombre">{pro.nombre}</p>
                    <p className="pro-especialidad">{pro.especialidad}</p>
                    <p className="pro-cuidad">{pro.ciudad}</p>
                    <p className="pro-tarifa">${pro.tarifa} / {pro.tarifa_unidad}</p>
                </div>
                
            </div>

        )    
}

export default ProfessionalCard 
