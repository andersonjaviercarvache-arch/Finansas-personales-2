import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Finanzas Pro - Dashboard", layout="wide", page_icon="📈")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            # Normalizar columnas
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            if 'monto' in df.columns:
                df['monto'] = df['monto'].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
                def fix_numbers(val):
                    if ',' in val and '.' in val: val = val.replace('.', '').replace(',', '.')
                    elif ',' in val: val = val.replace(',', '.')
                    return val
                df['monto'] = df['monto'].apply(fix_numbers)
                df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            df = df.dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            df['mes'] = df['fecha'].dt.strftime('%Y-%m')
            
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "n/a"
                df[col] = df[col].fillna('sin clasificar').astype(str).str.strip().str.lower()
            
            df = df.sort_values('fecha')
            df['monto_neto'] = df.apply(lambda x: x['monto'] if x['tipo'] == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_neto'].cumsum()
            return df
        except Exception:
            continue
    return None

df = load_data()

if df is not None:
    # --- CÁLCULOS GLOBALES (Para evitar NameError) ---
    total_ingresos_global = df[df['tipo'] == 'ingreso']['monto'].sum()
    total_egresos_global = df[df['tipo'] == 'egreso']['monto'].sum()

    st.sidebar.title("📌 Navegación")
    seccion = st.sidebar.radio("Ir a:", ["Vista General", "Gráficos Interactivos"])

    if seccion == "Vista General":
        st.title("⚖️ Control Financiero")
        
        busqueda = st.text_input("🔍 Buscar (ej: supermercado, nomina...)", "")
        mask = (df['detalle'].str.contains(busqueda, case=False) | 
                df['beneficiario'].str.contains(busqueda, case=False) |
                df['categoria'].str.contains(busqueda, case=False))
        df_f = df[mask]

        ing_f = df_f[df_f['tipo'] == 'ingreso']['monto'].sum()
        egr_f = df_f[df_f['tipo'] == 'egreso']['monto'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Ingresos", f"${ing_f:,.2f}")
        c2.metric("🔴 Egresos", f"-${egr_f:,.2f}")
        c3.metric("⚖️ Balance", f"${ing_f - egr_f:,.2f}")

        st.dataframe(df_f[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
                     .sort_values('fecha', ascending=False).style.format({"monto": "${:,.2f}", "balance_acumulado": "${:,.2f}"}), 
                     use_container_width=True)

    elif seccion == "Gráficos Interactivos":
        st.title("📊 Análisis Visual Avanzado")
        
        # 1. Comparativa Mensual
        st.subheader("🗓️ Flujo Mensual")
        df_mensual = df.groupby(['mes', 'tipo'])['monto'].sum().reset_index()
        fig_mes = px.bar(df_mensual, x='mes', y='monto', color='tipo', barmode='group',
                         color_discrete_map={'ingreso': '#2ecc71', 'egreso': '#e74c3c'})
        st.plotly_chart(fig_mes, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟥 Distribución de Egresos")
            df_egr = df[df['tipo'] == 'egreso']
            if total_egresos_global > 0:
                fig_tree = px.treemap(df_egr, path=['categoria', 'beneficiario'], values='monto',
                                      color='monto', color_continuous_scale='Reds')
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("No hay datos de egresos para mostrar.")

        with col2:
            st.subheader("🟩 Origen de Ingresos")
            df_ing = df[df['tipo'] == 'ingreso']
            if total_ingresos_global > 0:
                fig_sun = px.sunburst(df_ing, path=['categoria', 'beneficiario'], values='monto',
                                      color='monto', color_continuous_scale='Greens')
                st.plotly_chart(fig_sun, use_container_width=True)
            else:
                st.info("No hay datos de ingresos para mostrar.")

        st.subheader("📈 Tendencia del Saldo Acumulado")
        fig_line = px.area(df, x='fecha', y='balance_acumulado', color_discrete_sequence=['#3498db'])
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.error("No se pudo cargar el archivo CSV.")
