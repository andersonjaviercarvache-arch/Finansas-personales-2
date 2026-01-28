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
            df['mes'] = df['fecha'].dt.strftime('%Y-%m') # Columna para agrupar por mes
            
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "N/A"
                df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            df = df.sort_values('fecha')
            df['monto_neto'] = df.apply(lambda x: x['monto'] if x['tipo'].lower() == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_neto'].cumsum()
            return df
        except Exception:
            continue
    return None

df = load_data()

if df is not None:
    # --- SUBMENÚ LATERAL ---
    st.sidebar.title("📌 Navegación")
    seccion = st.sidebar.radio("Ir a:", ["Vista General y Buscador", "Gráficos Interactivos Avanzados"])

    if seccion == "Vista General y Buscador":
        st.title("⚖️ Control Financiero de Precisión")
        
        # Buscador e Indicadores
        busqueda = st.text_input("🔍 Busca por detalle o categoría:", "")
        mask = (df['detalle'].str.contains(busqueda, case=False) | 
                df['beneficiario'].str.contains(busqueda, case=False) |
                df['categoria'].str.contains(busqueda, case=False))
        df_f = df[mask]

        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Ingresos", f"${df_f[df_f['tipo'].lower() == 'ingreso']['monto'].sum():,.2f}")
        c2.metric("🔴 Egresos", f"-${df_f[df_f['tipo'].lower() == 'egreso']['monto'].sum():,.2f}")
        c3.metric("⚖️ Balance", f"${df_f[df_f['tipo'].lower() == 'ingreso']['monto'].sum() - df_f[df_f['tipo'].lower() == 'egreso']['monto'].sum():,.2f}")

        st.dataframe(df_f[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
                     .sort_values('fecha', ascending=False).style.format({"monto": "${:,.2f}", "balance_acumulado": "${:,.2f}"}), 
                     use_container_width=True)

    elif seccion == "Gráficos Interactivos Avanzados":
        st.title("📊 Análisis Visual de Movimientos")
        
        # 1. Gráfico de Barras: Ingresos vs Egresos por Mes
        st.subheader("🗓️ Comparativa Mensual (Entradas vs Salidas)")
        df_mensual = df.groupby(['mes', 'tipo'])['monto'].sum().reset_index()
        fig_mes = px.bar(df_mensual, x='mes', y='monto', color='tipo', barmode='group',
                         color_discrete_map={'ingreso': '#2ecc71', 'egreso': '#e74c3c'},
                         labels={'monto': 'Cantidad ($)', 'mes': 'Mes'})
        st.plotly_chart(fig_mes, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟥 Mapa de Gastos (TreeMap)")
            # Este gráfico muestra el peso visual de cada categoría de gasto
            df_gastos = df[df['tipo'].lower() == 'egreso']
            fig_tree = px.treemap(df_gastos, path=['categoria', 'beneficiario'], values='monto',
                                  color='monto', color_continuous_scale='Reds',
                                  title="Jerarquía de Gastos")
            st.plotly_chart(fig_tree, use_container_width=True)

        with col2:
            st.subheader("🟩 Origen de Ingresos")
            df_in = df[df['tipo'].lower() == 'ingreso']
            fig_sun = px.sunburst(df_in, path=['categoria', 'beneficiario'], values='monto',
                                  color='monto', color_continuous_scale='Greens',
                                  title="Jerarquía de Ingresos")
            st.plotly_chart(fig_sun, use_container_width=True)

        # 2. Línea de tendencia interactiva
        st.subheader("📈 Tendencia del Balance")
        fig_line = px.line(df, x='fecha', y='balance_acumulado', markers=True)
        fig_line.update_traces(line_color='#3498db', fill='tozeroy')
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.error("Error al cargar datos.")
