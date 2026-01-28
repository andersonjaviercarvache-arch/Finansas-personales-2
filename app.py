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
            df = df.dropna(how='all', axis=1)
            
            # Normalización de columnas
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            df = df.dropna(subset=['fecha', 'monto'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # Asegurar columnas de texto
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col not in df.columns: df[col] = "N/A"
                df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            # Cálculo de Balance
            df = df.sort_values('fecha')
            df['monto_signo'] = df.apply(lambda x: x['monto'] if x['tipo'].lower() == 'ingreso' else -x['monto'], axis=1)
            df['balance_acumulado'] = df['monto_signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Control de Finanzas con Montos Detallados")

df = load_data()

if df is not None:
    # --- MÉTRICAS ---
    total_in = df[df['tipo'].str.lower() == 'ingreso']['monto'].sum()
    total_out = df[df['tipo'].str.lower() == 'egreso']['monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📉 Egresos", "📈 Ingresos", "🗓️ Evolución"])

    with tab1:
        df_egresos = df[(df['tipo'].str.lower() == 'egreso') & (df['monto'] > 0)]
        if not df_egresos.empty:
            col_p, col_b = st.columns(2)
            with col_p:
                st.plotly_chart(px.pie(df_egresos, values='monto', names='categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
            with col_b:
                top_egresos = df_egresos.groupby('beneficiario')['monto'].sum().sort_values(ascending=False).head(10).reset_index()
                # text_auto='.2s' añade los valores sobre las barras
                fig_bar = px.bar(top_egresos, x='monto', y='beneficiario', orientation='h', title="Top 10 Egresos", color='monto', color_continuous_scale='Reds', text_auto='.2s')
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        df_ingresos = df[(df['tipo'].str.lower() == 'ingreso') & (df['monto'] > 0)]
        if not df_ingresos.empty:
            col_p_in, col_b_in = st.columns(2)
            with col_p_in:
                st.plotly_chart(px.pie(df_ingresos, values='monto', names='categoria', hole=0.4, title="Fuentes de Ingresos"), use_container_width=True)
            with col_b_in:
                top_ingresos = df_ingresos.groupby('beneficiario')['monto'].sum().sort_values(ascending=False).head(10).reset_index()
                fig_bar_in = px.bar(top_ingresos, x='monto', y='beneficiario', orientation='h', title="Principales Orígenes", color='monto', color_continuous_scale='Greens', text_auto='.2s')
                st.plotly_chart(fig_bar_in, use_container_width=True)

    with tab3:
        st.plotly_chart(px.area(df, x='fecha', y='balance_acumulado', title="Saldo Acumulado en el Tiempo"), use_container_width=True)

    st.markdown("---")

    # --- BUSCADOR Y TABLA FORMATEADA ---
    st.subheader("🔍 Buscador de Transacciones")
    busqueda = st.text_input("Filtrar movimientos:", "")

    mask = (df['detalle'].str.contains(busqueda, case=False) | 
            df['beneficiario'].str.contains(busqueda, case=False) |
            df['categoria'].str.contains(busqueda, case=False))
    
    df_filtrado = df[mask].sort_values('fecha', ascending=False)

    # Aplicamos formato de moneda a las columnas numéricas de la tabla
    st.dataframe(
        df_filtrado[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
        .style.format({
            "monto": "${:,.2f}",
            "balance_acumulado": "${:,.2f}"
        }), 
        use_container_width=True
    )

else:
    st.error("No se pudo cargar el archivo.")

