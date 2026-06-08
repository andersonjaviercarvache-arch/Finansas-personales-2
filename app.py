
import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Filtro de Estado de Cuenta", page_icon="📊", layout="wide")

st.title("📊 Analizador de Estados de Cuenta")
st.write("Sube tu estado de cuenta bancario para filtrar las transacciones rápidamente.")

# 1. Carga de archivo
archivo_subido = st.file_uploader("Sube tu archivo (CSV o Excel)", type=["csv", "xlsx"])

if archivo_subido is not None:
    try:
        # Leer el archivo dependiendo de su formato
        if archivo_subido.name.endswith('.csv'):
            df = pd.read_csv(archivo_subido)
        else:
            df = pd.read_excel(archivo_subido)
            
        st.success("Archivo cargado correctamente.")

        st.divider()
        st.subheader("🔍 Configuración y Filtros")
        
        # 2. Selección dinámica de columnas
        # Los bancos usan diferentes nombres para sus columnas, esto lo hace flexible
        col_opciones = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            col_beneficiario = st.selectbox("Columna de Beneficiario / Descripción:", col_opciones)
        with col2:
            col_monto = st.selectbox("Columna de Monto:", col_opciones)

        # 3. Controles de Filtro
        col3, col4 = st.columns(2)
        with col3:
            buscar_beneficiario = st.text_input("🔎 Filtrar por nombre de beneficiario:", "")
            
        with col4:
            # Aseguramos que la columna de monto sea numérica para el slider
            df[col_monto] = pd.to_numeric(df[col_monto], errors='coerce')
            min_monto = float(df[col_monto].min())
            max_monto = float(df[col_monto].max())
            
            rango_monto = st.slider(
                "💰 Rango de Monto:", 
                min_value=min_monto, 
                max_value=max_monto, 
                value=(min_monto, max_monto)
            )

        # 4. Aplicar Filtros
        df_filtrado = df.copy()

        # Filtrar por texto (ignora mayúsculas/minúsculas)
        if buscar_beneficiario:
            df_filtrado = df_filtrado[df_filtrado[col_beneficiario].astype(str).str.contains(buscar_beneficiario, case=False, na=False)]

        # Filtrar por monto
        df_filtrado = df_filtrado[(df_filtrado[col_monto] >= rango_monto[0]) & (df_filtrado[col_monto] <= rango_monto[1])]

        # 5. Mostrar Resultados
        st.divider()
        st.subheader(f"📑 Resultados: {len(df_filtrado)} transacciones encontradas")
        st.dataframe(df_filtrado, use_container_width=True)

        # 6. Opción de Descarga
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv,
            file_name='estado_cuenta_filtrado.csv',
            mime='text/csv',
        )

    except Exception as e:
        st.error(f"Hubo un error al procesar el documento. Asegúrate de que sea un archivo válido. Detalles: {e}")
