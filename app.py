import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Finanzas de Precisión", layout="wide", page_icon="⚖️")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Cargamos el archivo saltando el encabezado del banco
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Normalización de nombres de columnas
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            # --- LIMPIEZA DE PRECISIÓN PARA MONTOS ---
            if 'monto' in df.columns:
                # Convertimos a string y quitamos TODO lo que no sea número o punto/coma decimal
                df['monto'] = df['monto'].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
                
                # Manejo de formatos europeos/latinos (donde la coma es decimal)
                # Si hay puntos y comas, asumimos que el punto es de miles y la coma es decimal
                def fix_numbers(val):
                    if ',' in val and '.' in val:
                        val = val.replace('.', '').replace(',', '.')
                    elif ',' in val:
                        val = val.replace(',', '.')
                    return val

                df['monto'] = df['monto'].apply(fix_numbers)
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # Limpieza de fechas y textos
            df = df.dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "N/A"
                df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            # Cálculo de Balance Cronológico
            df = df.sort_values('fecha')
            df['monto_neto'] = df.apply(lambda x: x['monto'] if x['tipo'].lower() == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_neto'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("⚖️ Control Financiero de Precisión")

df = load_data()

if df is not None and not df.empty:
    # --- BUSCADOR (Prioridad) ---
    st.subheader("🔍 Buscador Inteligente")
    busqueda = st.text_input("Busca por detalle, categoría o beneficiario (ej: 'Súper', 'Nómina', 'Transferencia'):", "")

    # Filtro de búsqueda
    mask = (df['detalle'].str.contains(busqueda, case=False) | 
            df['beneficiario'].str.contains(busqueda, case=False) |
            df['categoria'].str.contains(busqueda, case=False))
    
    df_filtrado = df[mask].sort_values('fecha', ascending=False)

    # --- MÉTRICAS (Sobre los datos filtrados) ---
    total_in = df_filtrado[df_filtrado['tipo'].str.lower() == 'ingreso']['monto'].sum()
    total_out = df_filtrado[df_filtrado['tipo'].str.lower() == 'egreso']['monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Ingresos Filtrados", f"${total_in:,.2f}")
    c2.metric("🔴 Egresos Filtrados", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    t1, t2 = st.tabs(["📊 Distribución de Gastos", "📈 Línea de Tiempo"])
    
    with t1:
        egresos_plot = df_filtrado[(df_filtrado['tipo'].str.lower() == 'egreso') & (df_filtrado['monto'] > 0)]
        if not egresos_plot.empty:
            fig = px.pie(egresos_plot, values='monto', names='categoria', 
                         title="Reparto de Egresos", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay egresos que coincidan con la búsqueda.")

    with t2:
        fig_evol = px.area(df_filtrado, x='fecha', y='balance_acumulado', 
                           title="Evolución del Saldo", color_discrete_sequence=['#2ecc71'])
        st.plotly_chart(fig_evol, use_container_width=True)

    # --- TABLA DETALLADA ---
    st.subheader("📑 Listado de Movimientos")
    st.dataframe(
        df_filtrado[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
        .style.format({"monto": "${:,.2f}", "balance_acumulado": "${:,.2f}"}),
        use_container_width=True
    )

else:
    st.error("No se pudieron cargar los datos. Verifica el archivo CSV.")



