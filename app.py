import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# --- 1. CARGA DE BASE DE DATOS (CSV) ---
def cargar_datos():
    if os.path.exists('paneles.csv'):
        return pd.read_csv('paneles.csv')
    else:
        st.error("⚠️ Archivo 'paneles.csv' no encontrado. Por favor, cárguelo en el directorio.")
        return None

df_paneles = cargar_datos()

# --- 2. BASE DE DATOS TÉCNICA CIUDADES ---
CIUDADES_EC = {
    "Quito": {"hsp_anual": 4.82, "t_max": 22, "t_min": 8.0, "mensual": [4.5, 4.4, 4.6, 4.7, 4.8, 5.2, 5.5, 5.6, 5.4, 5.1, 4.8, 4.6]},
    "Guayaquil": {"hsp_anual": 4.55, "t_max": 33, "t_min": 19.0, "mensual": [4.2, 4.1, 4.4, 4.6, 4.8, 4.3, 4.1, 4.2, 4.5, 4.6, 4.7, 4.4]},
    "Cuenca": {"hsp_anual": 4.95, "t_max": 21, "t_min": 7.0, "mensual": [4.6, 4.5, 4.7, 4.8, 4.9, 5.1, 5.2, 5.3, 5.4, 5.2, 5.0, 4.7]},
    "Manta": {"hsp_anual": 4.68, "t_max": 31, "t_min": 19.0, "mensual": [4.3, 4.4, 4.8, 5.0, 4.9, 4.4, 4.2, 4.3, 4.5, 4.7, 4.6, 4.4]},
    "Loja": {"hsp_anual": 5.15, "t_max": 24, "t_min": 9.0, "mensual": [4.8, 4.7, 4.9, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.4, 5.2, 4.9]}
}

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PV Engineering Ecuador", layout="wide", page_icon="⚡")
st.title("⚡ PV Design Pro: Multi-Marca & Ajuste Climático")

if df_paneles is not None:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("📍 Ubicación")
        ciudad_sel = st.selectbox("Selecciona Ciudad:", list(CIUDADES_EC.keys()))
        consumo_mensual = st.number_input("Consumo (kWh/mes):", min_value=1, value=500)
        
        st.divider()
        st.header("📦 Selección de Módulo")
        marca_sel = st.selectbox("Marca:", df_paneles['Marca'].unique())
        modelos_filt = df_paneles[df_paneles['Marca'] == marca_sel]['Modelo'].tolist()
        modelo_sel = st.selectbox("Modelo:", modelos_filt)
        
        # Obtener parámetros del panel seleccionado
        p = df_paneles[df_paneles['Modelo'] == modelo_sel].iloc[0]
        
        st.divider()
        st.header("⚙️ Parámetros Automáticos")
        clima = CIUDADES_EC[ciudad_sel]
        
        # Cálculo de Pérdida por Temperatura
        t_celda_estimada = clima["t_max"] + 25
        perdida_temp_auto = max(0.0, (t_celda_estimada - 25) * abs(p["kPmax"]))
        
        p_otros = 8.0 # Inversor, cables, suciedad
        PR = (1 - perdida_temp_auto/100) * (1 - p_otros/100)
        
        st.write(f"**T. Máx Ambiente:** {clima['t_max']}°C")
        st.write(f"**Coef. Temp (Pmax):** {p['kPmax']}%/°C")
        st.info(f"PR calculado: **{PR*100:.1f}%**")

    # --- MOTOR DE CÁLCULO ---
    hsp_anual = clima["hsp_anual"]
    potencia_kwp = (consumo_mensual / 30) / (hsp_anual * PR)
    n_paneles = int(np.ceil((potencia_kwp * 1000) / p["Pmax"]))
    potencia_instalada = (n_paneles * p["Pmax"]) / 1000

    # --- VISUALIZACIÓN ---
    st.header(f"📊 Análisis Técnico: {marca_sel} {modelo_sel}")
    col_tech, col_graf = st.columns([1, 2])

    with col_tech:
        st.subheader("Especificaciones STC")
        st.write(f"**Voc:** {p['Voc']} V | **Vmp:** {p['Vmp']} V")
        st.write(f"**Isc:** {p['Isc']} A | **Imp:** {p['Imp']} A")
        st.write(f"**Eficiencia:** {p['Eficiencia']}%")
        
        fig_pie = px.pie(values=[PR*100, perdida_temp_auto, p_otros], 
                         names=['Energía Útil', 'Pérdida Térmica', 'Otras Pérdidas'],
                         hole=0.4, 
                         color_discrete_sequence=['#22C55E', '#EF4444', '#F59E0B'])
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graf:
        st.subheader(f"Recurso Solar Mensual: {ciudad_sel}")
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        df_hsp = pd.DataFrame({"Mes": meses, "HSP": clima["mensual"]})
        fig_hsp = px.bar(df_hsp, x="Mes", y="HSP", color="HSP", color_continuous_scale="Solar")
        st.plotly_chart(fig_hsp, use_container_width=True)

    # --- ANÁLISIS ECONÓMICO Y GENERACIÓN ---
    st.divider()
    st.header("💰 Generación y Ahorro Estimado")
    gen_anual = potencia_instalada * hsp_anual * 365 * PR
    ahorro_anual = gen_anual * 0.10

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Paneles Necesarios", f"{n_paneles} u.")
        st.write(f"Capacidad Total: **{potencia_instalada:.2f} kWp**")
    with c2:
        st.metric("Generación Anual", f"{gen_anual:,.0f} kWh")
        st.write(f"Promedio: **{gen_anual/12:.1f} kWh/mes**")
    with c3:
        st.metric("Ahorro Anual (0.10 ctvs)", f"${ahorro_anual:,.2f}")
        st.write(f"Ahorro mensual: **${ahorro_anual/12:.2f}**")

    # --- NOTA TÉCNICA DE SEGURIDAD ---
    # Voc corregido por temperatura mínima
    voc_frio = p["Voc"] * (1 + (p["kVoc"]/100) * (clima["t_min"] - 25))
    
    st.divider()
    col_warn1, col_warn2 = st.columns(2)
    with col_warn1:
        st.warning(f"⚠️ **Seguridad Eléctrica:** En {ciudad_sel} ({clima['t_min']}°C), el Voc del panel sube a **{voc_frio:.2f}V**. Verifique su inversor.")
    with col_warn2:
        if p['Imp'] > 15:
            st.error(f"🚨 **Alta Corriente:** Este panel entrega {p['Imp']}A. Requiere conductores y protecciones para alta corriente.")



### Mejoras clave en esta combinación:
* **Lectura Dinámica:** Al seleccionar una marca en el Sidebar, el sistema filtra los modelos disponibles en tiempo real desde tu CSV.
* **Ficha Técnica Instantánea:** Al elegir el panel, se despliegan sus parámetros `Voc`, `Imp` y `Eficiencia` bajo el encabezado principal.
* **Cálculo de Seguridad Voc:** Utiliza el valor de `kVoc` y `t_min` de la ciudad para advertirte sobre picos de voltaje en las madrugadas frías.
* **Alertas de Instalación:** Si el panel es de alta corriente (como los Jinko de 720W), el sistema añade una alerta roja automática.



**¿Te gustaría que añadamos un cálculo automático de metros cuadrados de superficie necesaria basándonos en la eficiencia del panel seleccionado?**
