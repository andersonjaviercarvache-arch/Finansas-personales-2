import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Financiero Real", layout="wide", page_icon="💰")

def load_data():
    file_name = "Estado de cuenta - 01_01_2026 - 27_01_2026.xlsx - Balance.csv"
    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_name, skiprows=12, sep=None, engine='python', encoding=enc, index_col=False)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Normalización de columnas
            df.columns = (df.columns.str.strip().str.lower()
                          .str.replace('í', 'i').str.replace('ó', 'o')
                          .str.replace('á', 'a').str.replace('é', 'e').str.replace('ú', 'u'))
            
            # Limpieza de montos: eliminamos todo excepto números, puntos, comas y el signo menos
            if 'monto' in df.columns:
                df['monto'] = df['monto'].astype(str).str.replace(r'[^\d.,-]', '', regex=True)
                
                def clean_numeric(val):
                    if not val or val == 'nan': return 0.0
                    # Si el banco usa coma como decimal y punto como miles (ej: 1.200,50)
                    if ',' in val and '.' in val:
                        val = val.replace('.', '').replace(',', '.')
                    elif ',' in val:
                        val = val.replace(',', '.')
                    return float(val)

                df['monto'] = df['monto'].apply(clean_numeric)
            
            df = df.dropna(subset=['fecha'])
            df['fecha'] = pd.to_datetime(df['fecha'], dayfirst=True)
            
            # Normalizar tipos de movimiento
            for col in ['tipo', 'categoria', 'beneficiario', 'detalle']:
                if col in df.columns:
                    df[col] = df[col].fillna('n/a').astype(str).str.strip().str.lower()
            
            return df
        except Exception:
            continue
    return None

# --- ENTRADA DE SALDO REAL ---
st.sidebar.header("⚙️ Ajuste de Saldo")
saldo_inicial = st.sidebar.number_input(
    "Saldo Inicial (Antes del primer movimiento):", 
    value=0.0, 
    step=100.0,
    help="Ingresa el saldo que tenías en tu cuenta el día 01/01/2026"
)

df = load_data()

if df is not None:
    # --- CÁLCULO DE BALANCE REAL ---
    # Ordenamos cronológicamente para el acumulado
    df = df.sort_values('fecha', ascending=True)
    
    # Lógica de signos: Algunos bancos ya traen el Egreso como negativo. 
    # Aquí nos aseguramos de no "doble restar".
    def calcular_neto(row):
        monto = abs(row['monto'])
        return monto if row['tipo'] == 'ingreso' else -monto

    df['monto_neto'] = df.apply(calcular_neto, axis=1)
    
    # El balance acumulado empieza desde el Saldo Inicial que tú pongas
    df['balance_acumulado'] = saldo_inicial + df['monto_neto'].cumsum()

    # --- INTERFAZ ---
    st.title("⚖️ Balance Real de Cuenta")
    
    # Buscador
    busqueda = st.text_input("🔍 Buscar en el historial:", "")
    mask = (df['detalle'].str.contains(busqueda, case=False) | 
            df['beneficiario'].str.contains(busqueda, case=False) |
            df['categoria'].str.contains(busqueda, case=False))
    df_f = df[mask]

    # Métricas
    ing = df_f[df_f['tipo'] == 'ingreso']['monto'].sum()
    egr = df_f[df_f['tipo'] == 'egreso']['monto'].sum()
    saldo_actual = df['balance_acumulado'].iloc[-1] if not df.empty else saldo_inicial

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Total Ingresos", f"${ing:,.2f}")
    c2.metric("🔴 Total Egresos", f"-${egr:,.2f}")
    c3.metric("🏦 Saldo Final Estimado", f"${saldo_actual:,.2f}")

    st.divider()

    # Tabla con el saldo más reciente arriba
    st.subheader("📑 Historial de Movimientos")
    st.dataframe(
        df_f[['fecha', 'tipo', 'monto', 'categoria', 'beneficiario', 'detalle', 'balance_acumulado']]
        .sort_values('fecha', ascending=False)
        .style.format({"monto": "${:,.2f}", "balance_acumulado": "${:,.2f}"}),
        use_container_width=True
    )
else:
    st.error("No se pudo leer el archivo.")
