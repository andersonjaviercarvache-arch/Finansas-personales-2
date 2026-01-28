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
            
            # Limpieza profunda de nombres de columnas
            df.columns = df.columns.str.strip().str.replace('í', 'i').str.replace('ó', 'o')
            
            # Limpiar datos
            df = df.dropna(subset=['Fecha', 'Monto'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').fillna(0)
            
            # Asegurar que las columnas de texto existan y no tengan nulos
            for col in ['Tipo', 'Categoria', 'Beneficiario', 'Detalle']:
                if col in df.columns:
                    df[col] = df[col].fillna('Sin Clasificar').astype(str).str.strip()
            
            df = df.sort_values('Fecha')
            df['Monto_Signo'] = df.apply(lambda x: x['Monto'] if x['Tipo'] == 'Ingreso' else -x['Monto'], axis=1)
            df['Balance_Acumulado'] = df['Monto_Signo'].cumsum()
            
            return df
        except Exception:
            continue
    return None

st.title("📊 Análisis Financiero con Buscador")

df = load_data()

if df is not None:
    # --- MÉTRICAS ---
    total_in = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
    total_out = df[df['Tipo'] == 'Egreso']['Monto'].sum()
    balance = total_in - total_out

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${total_in:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${total_out:,.2f}")
    c3.metric("⚖️ Balance Neto", f"${balance:,.2f}")

    st.markdown("---")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📉 Gastos", "📈 Ingresos", "🗓️ Evolución"])

    with tab1:
        # Filtrar solo egresos con monto mayor a 0 para el gráfico de pastel
        df_egresos = df[(df['Tipo'] == 'Egreso') & (df['Monto'] > 0)]
        if not df_egresos.empty:
            col_p, col_b = st.columns(2)
            with col_p:
                fig_pie = px.pie(df_egresos, values='Monto', names='Categoria', hole=0.4, title="Gastos por Categoria")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_b:
                top_egresos = df_egresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
                fig_bar = px.bar(top_egresos, x='Monto', y='Beneficiario', orientation='h', title="Top 10 Beneficiarios", color='Monto', color_continuous_scale='Reds')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No se encontraron registros de Egresos para graficar.")

    with tab2:
        df_ingresos = df[(df['Tipo'] == 'Ingreso') & (df['Monto'] > 0)]
        if not df_ingresos.empty:
            col_p_in, col_b_in = st.columns(2)
            with col_p_in:
                fig_pie_in = px.pie(df_ingresos, values='Monto', names='Categoria', hole=0.4, title="Fuentes de Ingresos")
                st.plotly_chart(fig_pie_in, use_container_width=True)
            with col_b_in:
                top_ingresos = df_ingresos.groupby('Beneficiario')['Monto'].sum().sort_values(ascending=False).head(10).reset_index()
                fig_bar_in = px.bar(top_ingresos, x='Monto', y='Beneficiario', orientation='h', title="Principales Origenes", color='Monto', color_continuous_scale='Greens')
                st.plotly_chart(fig_bar_in, use_container_width=True)
        else:
            st.warning("No se encontraron registros de Ingresos para graficar.")

    with tab3:
        st.plotly_chart(px.area(df, x='Fecha', y='Balance_Acumulado', title="Evolución del Saldo"), use_container_width=True)

    st.markdown("---")

    # --- BUSCADOR Y EXPORTACIÓN ---
    st.subheader("🔍 Buscador y Filtros")
    busqueda = st.text_input("Escribe para filtrar (Detalle, Categoria o Beneficiario):", "")

    mask = df['Detalle'].str.contains(busqueda, case=False) | \
           df['Beneficiario'].str.contains(busqueda, case=False) | \
           df['Categoria'].str.contains(busqueda, case=False)
    
    df_filtrado = df[mask].sort_values('Fecha', ascending=False)

    # Botón de Descarga
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Resultados')
    
    st.download_button(
        label="📥 Descargar resultados en Excel",
        data=output.getvalue(),
        file_name="filtro_finanzas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.dataframe(df_filtrado[['Fecha', 'Tipo', 'Monto', 'Categoria', 'Beneficiario', 'Detalle', 'Balance_Acumulado']], use_container_width=True)

else:
    st.error("No se pudo leer el archivo CSV. Revisa el nombre y que esté en la carpeta.")
