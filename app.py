import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mi Dashboard Financiero", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Saltamos las 12 filas de metadatos
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip().str.replace('í', 'i').str.replace('ó', 'o')
            
            # Limpieza y conversión
            df = df.dropna(subset=['Fecha', 'Monto'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # Aseguramos que Detalle y Beneficiario sean texto para el buscador
            df['Detalle'] = df['Detalle'].fillna('').astype(str)
            df['Beneficiario'] = df['Beneficiario'].fillna('').astype(str)
            
            # Ordenar cronológicamente y calcular Balance
            df = df.sort_values('Fecha')
            df['Monto_Signo'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
            df['Balance_Acumulado'] = df['Monto_Signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Análisis Financiero con Buscador Inteligente")

df = load_data()

if df is not None:
    # --- MÉTRICAS ---
    total_in = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    total_out = df[df['Tipo'] == 'Egreso']['Monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- PESTAÑAS DE ANÁLISIS ---
    tab1, tab2, tab3 = st.tabs(["📉 Gastos", "📈 Ingresos", "🗓️ Evolución Temporal"])

    with tab1:
        df_egresos = df[df['Tipo'] == 'Egreso']
        col_p, col_b = st.columns(2)
        with col_p:
            st.plotly_chart(px.pie(df_egresos, values='Monto', names='Categoria', hole=0.4, title="Gastos por Categoría"), use_container_width=True)
        with col_b:
            top_egresos = df_egresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
            st.plotly_chart(px.bar(top_egresos, x='Monto', y='Beneficiario', orientation='h', title="Top 10 Beneficiarios", color_continuous_scale='Reds', color='Monto'), use_container_width=True)

    with tab2:
        df_ingresos = df[df['Tipo'] == 'Ingreso']
        col_p_in, col_b_in = st.columns(2)
        with col_p_in:
            st.plotly_chart(px.pie(df_ingresos, values='Monto', names='Categoria', hole=0.4, title="Fuentes de Ingresos"), use_container_width=True)
        with col_b_in:
            top_ingresos = df_ingresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
            st.plotly_chart(px.bar(top_ingresos, x='Monto', y='Beneficiario', orientation='h', title="Principales Orígenes", color_continuous_scale='Greens', color='Monto'), use_container_width=True)

    with tab3:
        st.subheader("Balance Acumulado")
        st.plotly_chart(px.area(df, x='Fecha', y='Balance_Acumulado', color_discrete_sequence=['#3498db']), use_container_width=True)

    st.markdown("---")

    # --- BUSCADOR Y TABLA ---
    st.subheader("🔍 Buscador de Movimientos")
    busqueda = st.text_input("Filtrar por detalle, beneficiario o categoría:", "")

    # Aplicamos el filtro de búsqueda
    df_filtrado = df[
        df['Detalle'].str.contains(busqueda, case=False) | 
        df['Beneficiario'].str.contains(busqueda, case=False) |
        df['Categoria'].str.contains(busqueda, case=False)
    ]

    st.write(f"Mostrando {len(df_filtrado)} movimientos encontrados:")
    st.dataframe(
        df_filtrado[['Fecha', 'Tipo', 'Monto', 'Categoria', 'Beneficiario', 'Detalle', 'Balance_Acumulado']]
        .sort_values('Fecha', ascending=False), 
        use_container_width=True
    )

else:
    st.error("Archivo no encontrado o error en el formato.")
