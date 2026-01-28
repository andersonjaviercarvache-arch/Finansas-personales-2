import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Finanzas", layout="wide", page_icon="🏦")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            # Saltamos 12 filas. El archivo tiene una coma al inicio, index_col=False la ignora.
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            
            # 1. Eliminar columnas que sean todas nulas o "Unnamed"
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df = df.dropna(how='all', axis=1)
            
            # 2. LIMPIEZA CRÍTICA DE COLUMNAS: Quitamos tildes y espacios para evitar el ValueError
            df.columns = df.columns.str.strip().str.replace('í', 'i').str.replace('ó', 'o')
            
            # 3. Limpiar filas vacías
            df = df.dropna(subset=['Fecha', 'Monto'])
            
            # 4. Formatear datos
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
            df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce').abs() # .abs() asegura valores positivos para el gráfico
            
            return df
        except Exception:
            continue
    return None

st.title("💰 Mi Estado de Cuenta Interactivo")

df = load_data()

if df is not None:
    # Definimos los nombres de columnas limpios que usaremos
    col_categoria = "Categoria" # Sin tilde por la limpieza que hicimos arriba
    col_monto = "Monto"
    col_tipo = "Tipo"

    # --- MÉTRICAS ---
    ingresos = df[df[col_tipo] == 'Ingreso'][col_monto].sum()
    egresos = df[df[col_tipo] == 'Egreso'][col_monto].sum()
    balance = ingresos - egresos

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos", f"${ingresos:,.2f}")
    c2.metric("Gastos", f"-${egresos:,.2f}")
    c3.metric("Balance", f"${balance:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Gastos por Categoría")
        df_gastos = df[(df[col_tipo] == 'Egreso') & (df[col_monto] > 0)]
        
        if not df_gastos.empty:
            # Usamos los nombres de columna ya limpios
            fig_pie = px.pie(df_gastos, values=col_monto, names=col_categoria, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos de gastos suficientes.")

    with col_b:
        st.subheader("Movimientos en el Tiempo")
        fig_bar = px.bar(df.sort_values('Fecha'), x='Fecha', y=col_monto, color=col_tipo, barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📑 Listado de Movimientos")
    st.dataframe(df, use_container_width=True)
else:
    st.error("No se pudo cargar el archivo. Verifica el nombre y formato.")
    
