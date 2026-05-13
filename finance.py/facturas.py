import streamlit as st

def mostrar_historial_financiero(es_profesional=True):
    st.subheader("📊 Resumen de Ingresos y Facturación")
    
    if es_profesional:
        col1, col2 = st.columns(2)
        col1.metric("Ganancias del Mes", "$2.500.000", "+15%")
        col2.metric("Pendiente por Cobrar", "$450.000")
        
        st.write("### Últimos cobros")
        # Ejemplo de tabla de facturación
        st.table({
            "Fecha": ["2026-05-10", "2026-05-11"],
            "Cliente": ["Juan Pérez", "Maria Lopez"],
            "Monto": ["$80.000", "$120.000"],
            "Estado": ["Pagado", "En proceso"]
        })
    else:
        st.write("### Mis Compras")
        st.write("Recibo #001 - Plan de Nutrición - $150.000")
        if st.button("Descargar PDF"):
            st.info("Generando factura...")