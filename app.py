import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Financiero Pro", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # 1. Normalización de nombres de columnas
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            # 2. LIMPIEZA DE MONTOS (ELIMINAR SÍMBOLOS RARO)
            # Esto quita el signo $, comas de miles y espacios para que Python vea solo el número
            if 'monto' in df.columns:
                df['monto'] = (df['monto'].astype(str)
                               .str.replace('$', '', regex=False)
                               .str.replace(',', '', regex=False)
                               .str.strip())
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # 3. Limpiar fechas y filtrar filas vacías
            df = df.dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            
            # 4. Asegurar columnas de texto
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "N/A"
                df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            # 5. Cálculo de Balance
            df = df.sort_values('fecha')
            df['monto_signo'] = df.apply(lambda x: x['monto'] if x['tipo'].lower() == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Control de Finanzas - Cantidades Corregidas")

df = load_data()

if df is not None and not df.empty:
    # --- MÉTRICAS ---
    # Usamos sum() directamente sobre la columna limpia
    total_in = df[df['tipo'].str.lower() == 'ingreso']['monto'].sum()
    total_out = df[df['tipo'].str.lower() == 'egreso']['monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    tab1, tab2 = st.tabs(["📊 Distribución", "📈 Tendencia"])
    
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            df_egresos = df[(df['tipo'].str.lower() == 'egreso') & (df['monto'] > 0)]
            if not df_egresos.empty:
                st.plotly_chart(px.pie(df_egresos, values='monto', names='categoria', title="Gastos por Categoría"), use_container_width=True)
            else:
                st.info("No hay gastos mayores a $0 para graficar.")
        with col_b:
            df_ingresos = df[(df['tipo'].str.lower() == 'ingreso') & (df['monto'] > 0)]
            if not df_ingresos.empty:
                st.plotly_chart(px.pie(df_ingresos, values='monto', names='categoria', title="Fuentes de Ingreso"), use_container_width=True)

    with tab2:
        st.plotly_chart(px.area(df, x='fecha', y='balance_acumulado', title="Evolución del Saldo"), use_container_width=True)

    # --- TABLA ---
    st.subheader("📑 Listado de Movimientos")
    st.dataframe(
        df[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
        .sort_values('fecha', ascending=False)
        .style.format({"monto": "${:,.2f}", "balance_acumulado": "${:,.2f}"}),
        use_container_width=True
    )

else:
    st.error("No se detectaron datos. Revisa que la columna 'Monto' tenga números en tu archivo.")


