import streamlit as st
from datetime import datetime

def gestionar_agenda():
    st.subheader("Gestión de Citas y Calendario")
    
    tab1, tab2 = st.tabs(["Próximas Citas", "Configurar Disponibilidad"])
    
    with tab1:
        # Esto vendría de la base de datos
        st.write("📅 **Lunes 18 de Mayo** - 08:00 AM")
        st.write("👤 Cliente: Jacob (Entrenamiento de Fuerza)")
        if st.button("Confirmar Asistencia"):
            st.success("Cita confirmada")

    with tab2:
        st.write("Selecciona tus horarios disponibles para recibir clientes:")
        dias = st.multiselect("Días de trabajo", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"])
        hora_inicio = st.time_input("Hora de inicio", datetime.strptime("06:00", "%H:%M"))
        
        if st.button("Guardar Horarios"):
            st.success("Agenda actualizada correctamente")