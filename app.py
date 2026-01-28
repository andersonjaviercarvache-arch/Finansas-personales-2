import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Finanzas Personales", layout="wide", page_icon="🏦")

def load_data():
    # Nombre exacto de tu archivo
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            # Leemos el archivo. skiprows=12 para saltar el resumen inicial.
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            
            # 1. Limpieza de columnas: eliminamos columnas que sean todas nulas o "Unnamed"
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # 2. Limpiar nombres de columnas
            df.columns = df.columns.str.strip()
            
            # 3. Eliminar filas donde falten datos clave
            df = df.dropna(subset=['Fecha', 'Monto'])
            
            # 4. Convertir Fecha a formato real
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            
            # 5. Convertir Monto a número
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
            
            return df
        except Exception:
            continue
    return None

# --- INTERFAZ DE USUARIO ---
st.title("💰 Mi Estado de Cuenta Interactivo")
st.markdown("Visualización de ingresos y gastos basada en tu reporte bancario.")

df = load_data()

# --- AQUÍ ESTABA EL ERROR DE INDENTACIÓN ---
if df is not None:
    # Todo esto ahora tiene 4 espacios de sangría a la izquierda
    ingresos_totales = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    egresos_totales = df[df['Tipo'] == 'Egreso']['Monto'].sum()
    balance = ingresos_totales - egresos_totales

    # Diseño de tarjetas de métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Ingresos", f"${ingresos_totales:,.2f}")
    c2.metric("Total Gastos", f"-${egresos_totales:,.2f}", delta_color="inverse")
    c3.metric("Saldo del Periodo", f"${balance:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Gastos por Categoría")
        df_gastos = df[df['Tipo'] == 'Egreso']
        if not df_gastos.empty:
            fig_pie = px.pie(df_gastos, values='Monto', names='Categoría', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No se detectaron gastos etiquetados.")

    with col_b:
        st.subheader("Historial de Movimientos")
        fig_bar = px.bar(df.sort_values('Fecha'), x='Fecha', y='Monto', color='Tipo',
                         barmode='group', color_discrete_map={'Ingreso': '#00CC96', 'Egreso': '#EF553B'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABLA DE DATOS ---
    st.subheader("📑 Listado Detallado")
    st.dataframe(df.sort_values(by='Fecha', ascending=False), use_container_width=True)

else:
    st.error("❌ No se pudo encontrar o leer el archivo.")
    st.info("Asegúrate de que el archivo CSV esté en la misma carpeta que este script.")
