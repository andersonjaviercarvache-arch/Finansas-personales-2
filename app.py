import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración visual
st.set_page_config(page_title="Mis Finanzas", layout="wide")

def load_data():
    # Cargamos el archivo saltando las filas de texto iniciales (metadatos)
    df = pd.read_csv("Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv", skiprows=12)
    # Limpiar columnas vacías generadas por el CSV
    df = df.dropna(how='all', axis=1)
    df = df.dropna(subset=['Monto', 'Fecha'])
    # Convertir formatos
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
    df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
    return df

st.title("📊 Mi Dashboard Financiero")

try:
    df = load_data()

    # --- KPI'S ---
    ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
    egresos = df[df["Tipo"] == "Egreso"]["Monto"].sum()
    balance = ingresos - egresos

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos Totales", f"${ingresos:,.2f}")
    col2.metric("Egresos Totales", f"-${egresos:,.2f}", delta_color="inverse")
    col3.metric("Balance Neto", f"${balance:,.2f}")

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Gasto por Categoría")
        fig_pie = px.pie(df[df["Tipo"] == "Egreso"], values='Monto', names='Categoría', hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.subheader("Evolución Diaria")
        fig_line = px.line(df.sort_values("Fecha"), x="Fecha", y="Monto", color="Tipo")
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Listado de Movimientos")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.info("Asegúrate de que el archivo CSV esté en la misma carpeta que este script.")