import streamlit as st

def perfil_profesional_view(datos):
    """Muestra la vista detallada del profesional para los clientes"""
    st.title(f"Esp. {datos['nombre']}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(datos.get('foto', 'https://via.placeholder.com/150'), use_column_width=True)
        st.metric("Experiencia", f"{datos['años_exp']} años")
        st.write(f"📍 {datos['ciudad']}")

    with col2:
        st.subheader("Metodología y Especialidad")
        st.write(datos['descripcion'])
        
        st.write("### Servicios Ofrecidos")
        for servicio in datos['servicios']:
            st.write(f"✅ {servicio}")
            
        st.success(f"Precio por sesión: ${datos['tarifa']} COP")
        
        if st.button("Reservar Cita Ahora"):
            st.session_state['interes_en'] = datos['id']
            st.info("Conectando con el calendario...")