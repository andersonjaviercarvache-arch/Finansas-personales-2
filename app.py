import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Mi Dashboard Financiero", layout="wide", page_icon="💰")

# Estilo personalizado para las métricas
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            # skiprows=12 porque tus datos reales empiezan en la fila 13
            df = pd.read_csv("finanzas.csv", skiprows=12, sep=None, engine='python', encoding=enc)
            
            # 1. Eliminar columnas completamente vacías
            df = df.dropna(how='all', axis=1)
            
            # 2. Si la primera columna no tiene nombre, la eliminamos (es el desfase del CSV)
            if df.columns[0].startswith('Unnamed'):
                df = df.drop(df.columns[0], axis=1)
            
            # 3. Limpiar espacios en los nombres de columnas
            df.columns = df.columns.str.strip()
            
            # 4. Eliminar filas donde el Monto sea nulo
            df = df.dropna(subset=['Monto'])
            
            # 5. Convertir formatos
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
            
            return df
        except Exception:
            continue
    return None

# --- INICIO DE LA APP ---
st.title("💸 Control de Finanzas Personales")
st.markdown("Analiza tus movimientos bancarios de forma interactiva.")

df = load_data()

if df is not None:
    # --- BARRA LATERAL (Filtros) ---
    st.sidebar.header("Filtros")
    rango_fecha = st.sidebar.date_input("Rango de fechas", [df['Fecha'].min(), df['Fecha'].max()])
    categorias = st.sidebar.multiselect("Categorías", options=df['Categoría'].unique(), default=df['Categoría'].unique())
    
    # Aplicar Filtros
    mask = (df['Fecha'].dt.date >= rango_fecha[0]) & (df['Fecha'].dt.date <= rango_fecha[1]) & (df['Categoría'].isin(categorias))
    df_filtrado = df.loc[mask]

    # --- MÉTRICAS (Infografía) ---
    total_ingresos = df_filtrado[df_filtrado['Tipo'] == 'Ingreso']['Monto'].sum()
    total_egresos = df_filtrado[df_filtrado['Tipo'] == 'Egreso']['Monto'].sum()
    balance = total_ingresos - total_egresos

    c1, c2, c3 = st.columns(3)
    c1.metric("➕ Ingresos", f"${total_ingresos:,.2f}", delta_color="normal")
    c2.metric("➖ Egresos", f"${total_egresos:,.2f}", delta_color="inverse")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}", delta=f"{balance:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("Distribución de Gastos")
        df_gastos = df_filtrado[df_filtrado['Tipo'] == 'Egreso']
        fig_pie = px.pie(df_gastos, values='Monto', names='Categoría', 
                         hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_der:
        st.subheader("Flujo de Dinero en el Tiempo")
        # Agrupamos por fecha para ver la tendencia
        df_tendencia = df_filtrado.groupby(['Fecha', 'Tipo'])['Monto'].sum().reset_index()
        fig_area = px.area(df_tendencia, x="Fecha", y="Monto", color="Tipo",
                           color_discrete_map={"Ingreso": "#2ecc71", "Egreso": "#e74c3c"})
        st.plotly_chart(fig_area, use_container_width=True)

    # --- TABLA DETALLADA ---
    st.subheader("📑 Detalle de Transacciones")
    st.dataframe(df_filtrado.sort_values('Fecha', ascending=False), use_container_width=True)

else:
    st.error("❌ No pudimos leer 'finanzas.csv'. Revisa que esté en la carpeta y sea el formato correcto.")
