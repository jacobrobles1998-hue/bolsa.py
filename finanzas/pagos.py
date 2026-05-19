import streamlit as st


def procesar_pago(monto, profesional_nombre):
    st.subheader("💰 Pasarela de Pago Segura")
    
    # Calculamos la comisión basándonos en tu config.py
    comision = monto * Config.COMISION_APP
    total_a_pagar = monto
    
    st.write(f"Vas a contratar a: **{profesional_nombre}**")
    st.write(f"Monto total: ${total_a_pagar:,.0f} {Config.MONEDA}")
    
    # Simulación de botones de pago locales
    metodo = st.radio("Selecciona tu método de pago:", ["PSE (Débito)", "Tarjeta de Crédito", "Efecty"])
    
    if st.button("Confirmar Pago"):
        # Aquí iría la lógica del SDK de Mercado Pago
        st.success("¡Pago procesado con éxito!")
        st.balloons()
        # Esta información se enviaría a database/db_handler.py para registrar la venta