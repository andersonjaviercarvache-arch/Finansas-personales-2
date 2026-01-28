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
            # index_col=False ayuda a manejar la columna vacía al principio.
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
            
            # 5. Convertir Monto a número (limpiando posibles caracteres extraños)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
            
            return df
        except Exception as e:
            last_error = e
            continue
    return None

# --- INTERFAZ DE USUARIO ---
st.title("💰 Mi Estado de Cuenta Interactivo")
st.markdown("Visualización de ingresos y gastos basada en tu reporte bancario.")

df = load_data()

if df is not None:
    # --- MÉTRICAS GENERAL
