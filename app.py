import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Control Financiero", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Lectura del archivo saltando el encabezado del banco
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Normalización de nombres de columnas (minúsculas y sin tildes)
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            # Limpieza profunda de montos
            if 'monto' in df.columns:
                df['monto'] = df['monto'].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
                def fix_numbers(val):
                    if ',' in val and '.' in val: val = val.replace('.', '').replace(',', '.')
                    elif ',' in val: val = val.replace(',', '.')
                    return val
                df['monto'] = df['monto'].apply(fix_numbers)
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # Limpieza de fechas
            df = df.dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            
            # Asegurar columnas de texto
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "n/a"
                df[col] = df[col].fillna('sin clasificar').astype(str).str.strip().str.lower()
            
            # Cálculo de Balance Acumulado
            df = df.sort_values('fecha')
            df['monto_neto'] = df.apply(lambda x: x['monto'] if x['tipo'] == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_neto'].cumsum()
            
            return df
        except Exception:
            continue
    return None

# --- INTERFAZ PRINCIPAL ---
st.title("⚖️ Estado de Cuenta e Historial")

df = load_data()

if df is not None:
    # --- BUSCADOR ---
    st.subheader("🔍 Buscador de Movimientos")
    busqueda = st.text_input("Escribe el detalle, categoría o beneficiario que deseas encontrar:", "")

    # Aplicar Filtro de Búsqueda
    mask = (df['detalle'].str.contains(busqueda, case=False) | 
            df['beneficiario'].str.contains(busqueda, case=False) |
            df['categoria'].str.contains(busqueda, case=False))
    
    df_f = df[mask]

    # --- MÉTRICAS (Dinámicas según la búsqueda) ---
    ing_f = df_f[df_f['tipo'] == 'ingreso']['monto'].sum()
    egr_f = df_f[df_f['tipo'] == 'egreso']['monto'].sum()
    balance_f = ing_f - egr_f

    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Ingresos Filtrados", f"${ing_f:,.2f}")
    col2.metric("🔴 Egresos Filtrados", f"-${egr_f:,.2f}")
    col3.metric("⚖️ Balance Neto", f"${balance_f:,.2f}")

    st.markdown("---")

    # --- TABLA DE DATOS ---
    st.subheader("📑 Listado Detallado de Transacciones")
    
    # Formateamos la tabla para que se vea impecable
    st.dataframe(
        df_f[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
        .sort_values('fecha', ascending=False)
        .style.format({
            "monto": "${:,.2f}", 
            "balance_acumulado": "${:,.2f}"
        }),
        use_container_width=True
    )

else:
    st.error("No se pudo cargar el archivo. Verifica que el nombre sea exacto y esté en la misma carpeta.")
