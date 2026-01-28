import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mi Dashboard Financiero", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Saltamos las filas de encabezado (12)
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip().str.replace('í', 'i').str.replace('ó', 'o')
            
            # Limpiar y convertir datos
            df = df.dropna(subset=['Fecha', 'Monto'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # Ordenar cronológicamente
            df = df.sort_values('Fecha')
            
            # Calcular Balance Acumulado para la línea de tiempo
            df['Monto_Signo'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
            df['Balance_Acumulado'] = df['Monto_Signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Análisis Detallado de Ingresos y Egresos")

df = load_data()

if df is not None:
    # --- RESUMEN DE MÉTRICAS ---
    total_in = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    total_out = df[df['Tipo'] == 'Egreso']['Monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}", delta_color="inverse")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS DE FLUJO ---
    tab1, tab2 = st.tabs(["📉 Análisis de Gastos", "📈 Análisis de Ingresos"])

    with tab1:
        st.subheader("¿A dónde se va tu dinero?")
        df_egresos = df[df['Tipo'] == 'Egreso']
        
        col_pie, col_bar = st.columns(2)
        with col_pie:
            fig_pie_out = px.pie(df_egresos, values='Monto', names='Categoria', 
                                 title="Gastos por Categoría", hole=0.4,
                                 color_discrete_sequence=px.colors.sequential.Reds_r)
            st.plotly_chart(fig_pie_out, use_container_width=True)
        
        with col_bar:
            # Top Beneficiarios de gastos
            top_egresos = df_egresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
            fig_bar_out = px.bar(top_egresos, x='Monto', y='Beneficiario', orientation='h',
                                 title="Top 10 Beneficiarios (Egresos)", color='Monto',
                                 color_continuous_scale='Reds')
            st.plotly_chart(fig_bar_out, use_container_width=True)

    with tab2:
        st.subheader("¿De dónde viene tu dinero?")
        df_ingresos = df[df['Tipo'] == 'Ingreso']
        
        col_pie_in, col_bar_in = st.columns(2)
        with col_pie_in:
            fig_pie_in = px.pie(df_ingresos, values='Monto', names='Categoria', 
                                title="Fuentes de Ingreso", hole=0.4,
                                color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig_pie_in, use_container_width=True)
            
        with col_bar_in:
            top_ingresos = df_ingresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
            fig_bar_in = px.bar(top_ingresos, x='Monto', y='Beneficiario', orientation='h',
                                title="Principales Emisores (Ingresos)", color='Monto',
                                color_continuous_scale='Greens')
            st.plotly_chart(fig_bar_in, use_container_width=True)

    st.markdown("---")

    # --- BALANCE Y TABLA ---
    st.subheader("📅 Evolución del Saldo y Detalle")
    
    # Gráfico de balance acumulado
    fig_balance = px.area(df, x='Fecha', y='Balance_Acumulado', title="Saldo Disponible en el Tiempo")
    st.plotly_chart(fig_balance, use_container_width=True)

    # Tabla interactiva con filtros de búsqueda
    st.dataframe(df[['Fecha', 'Tipo', 'Monto', 'Categoria', 'Beneficiario', 'Detalle']].sort_values('Fecha', ascending=False), use_container_width=True)

else:
    st.error("No se pudo cargar el archivo. Verifica que el nombre coincida exactamente.")
