import streamlit as st

def perfil_cliente_view(datos_usuario):
    """Panel de control para el cliente (atleta)"""
    st.header(f"Panel de Control: {datos_usuario['nombre']}")
    
    tab1, tab2, tab3 = st.tabs(["Mi Progreso", "Mi Plan", "Citas"])

    with tab1:
        st.subheader("Seguimiento Físico")
        col1, col2, col3 = st.columns(3)
        # Datos como los que tú registras: peso, altura, etc.
        col1.metric("Peso Actual", f"{datos_usuario['peso']} kg")
        col2.metric("Altura", f"{datos_usuario['altura']} cm")
        col3.metric("Meta", "80 kg") # Ejemplo basado en tus metas personales

        # Gráfico simple de progreso (usando la lógica que planeas para AXON)
        st.line_chart(datos_usuario['historico_peso'])

    with tab2:
        st.subheader("Plan de Hoy")
        st.write("🏋️ **Rutina:** Empuje (Pecho/Hombro)")
        st.write("🍎 **Calorías Objetivo:** 3000 kcal") # Basado en tus estándares

    with tab3:
        st.subheader("Próximas Sesiones")
        st.write("📅 Mañana 8:00 AM con Entrenador Carlos")