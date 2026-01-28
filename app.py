import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Mi Dashboard Financiero", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # --- LIMPIEZA AGRESIVA DE COLUMNAS ---
            # Pasamos todo a minúsculas y quitamos tildes para no fallar nunca
            df.columns = (df.columns.str.strip()
                          .str.lower()
                          .str.replace('í', 'i')
                          .str.replace('ó', 'o')
                          .str.replace('á', 'a')
                          .str.replace('é', 'e')
                          .str.replace('ú', 'u'))
            
            # Limpiar datos básicos
            df = df.dropna(subset=['fecha', 'monto'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # Asegurar que las columnas existan con los nombres nuevos (minúsculas y sin tildes)
            columnas_esperadas = ['tipo', 'categoria', 'beneficiario', 'detalle']
            for col in columnas_esperadas:
                if col not in df.columns:
                    df[col] = "No disponible" # Crea la columna si no existe para evitar el KeyError
                df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            df = df.sort_values('fecha')
            df['monto_signo'] = df.apply(lambda x: x['monto'] if x['tipo'].lower() == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Análisis Financiero Final")

df = load_data()

if df is not None:
    # Métricas usando nombres en minúscula
    total_in = df[df['tipo'].str.lower() == 'ingreso']['monto'].sum()
    total_out = df[df['tipo'].str.lower() == 'egreso']['monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📉 Gastos", "📈 Ingresos", "🗓️ Evolución"])

    with tab1:
        df_egresos = df[(df['tipo'].str.lower() == 'egreso') & (df['monto'] > 0)]
        if not df_egresos.empty:
            col_p, col_b = st.columns(2)
            with col_p:
                st.plotly_chart(px.pie(df_egresos, values='monto', names='categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
            with col_b:
                top_egresos = df_egresos.groupby('beneficiario')['monto'].sum().sort_values(ascending=False).head(10).reset_index()
                st.plotly_chart(px.bar(top_egresos, x='monto', y='beneficiario', orientation='h', title="Top 10 Beneficiarios", color='monto', color_continuous_scale='Reds'), use_container_width=True)
        else:
            st.warning("No se encontraron Egresos.")

    with tab2:
        df_ingresos = df[(df['tipo'].str.lower() == 'ingreso') & (df['monto'] > 0)]
        if not df_ingresos.empty:
            col_p_in, col_b_in = st.columns(2)
            with col_p_in:
                st.plotly_chart(px.pie(df_ingresos, values='monto', names='categoria', hole=0.4, title="Fuentes de Ingresos"), use_container_width=True)
            with col_b_in:
                top_ingresos = df_ingresos.groupby('beneficiario')['monto'].sum().sort_values(ascending=False).head(10).reset_index()
                st.plotly_chart(px.bar(top_ingresos, x='monto', y='beneficiario', orientation='h', title="Principales Origenes", color='monto', color_continuous_scale='Greens'), use_container_width=True)
        else:
            st.warning("No se encontraron Ingresos.")

    with tab3:
        st.plotly_chart(px.area(df, x='fecha', y='balance_acumulado', title="Evolución del Saldo"), use_container_width=True)

    st.markdown("---")

    # --- BUSCADOR ---
    st.subheader("🔍 Buscador de Movimientos")
    busqueda = st.text_input("Filtrar por detalle, beneficiario o categoria:", "")

    mask = (df['detalle'].str.contains(busqueda, case=False) | 
            df['beneficiario'].str.contains(busqueda, case=False) |
            df['categoria'].str.contains(busqueda, case=False))
    
    df_filtrado = df[mask].sort_values('fecha', ascending=False)

    st.dataframe(df_filtrado[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']], use_container_width=True)

else:
    st.error("Error crítico: No se pudo procesar el archivo. Revisa que las columnas 'Fecha', 'Tipo' y 'Monto' existan.")
