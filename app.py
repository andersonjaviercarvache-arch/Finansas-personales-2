import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Finanzas", layout="wide", page_icon="🏦")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Lectura del archivo omitiendo el encabezado de 12 filas
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # Limpieza de nombres de columnas
            df.columns = df.columns.str.strip().str.replace('í', 'i').str.replace('ó', 'o')
            
            # Limpieza de datos
            df = df.dropna(subset=['Fecha', 'Monto'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # Ordenar por fecha para cálculos acumulados
            df = df.sort_values('Fecha')
            
            # Crear columna de monto con signo para el balance (Ingreso +, Egreso -)
            df['Monto_Neto'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
            
            # Calcular Balance Acumulado
            df['Balance_Acumulado'] = df['Monto_Neto'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("💰 Análisis de Flujo de Caja")

df = load_data()

if df is not None:
    # --- MÉTRICAS SUPERIORES ---
    ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    egresos = df[df['Tipo'] == 'Egreso']['Monto'].sum()
    balance_final = ingresos - egresos

    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Total Ingresos", f"${ingresos:,.2f}")
    c2.metric("📉 Total Egresos", f"-${egresos:,.2f}", delta_color="inverse")
    c3.metric("⚖️ Balance Neto", f"${balance_final:,.2f}")

    st.divider()

    # ---

