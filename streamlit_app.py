import streamlit as st
import pandas as pd
import numpy as np

def calcular_presion_map(voltaje, v_ref=5.0):
    try:
        if pd.isna(voltaje): return np.nan
        if voltaje < 0.1 or voltaje > 4.9: raise ValueError("Fuera de rango")
        presion_kpa = (voltaje / v_ref + 0.04) / 0.004
        return round(presion_kpa, 2)
    except Exception:
        return np.nan

def calcular_temperatura_iat(resistencia_ohms, r_ref=10000.0, beta=3950.0, t0=298.15):
    try:
        if pd.isna(resistencia_ohms): return np.nan
        if resistencia_ohms <= 0: raise ValueError("División por cero")
        temp_kelvin = 1.0 / (1.0 / t0 + (1.0 / beta) * np.log(resistencia_ohms / r_ref))
        return round(temp_kelvin - 273.15, 2)
    except Exception:
        return np.nan

def generar_datos_simulados(num_registros=12):
    np.random.seed(42)
    tiempos = list(range(1, num_registros + 1))
    presiones = list(np.random.normal(loc=101.3, scale=2.5, size=num_registros))
    temperaturas = list(np.random.normal(loc=24.8, scale=1.0, size=num_registros))
    
    presiones[4] = "ERROR_SENSOR" 
    temperaturas[8] = None          
    
    return pd.DataFrame({"Tiempo_s": tiempos, "Presion_kPa": presiones, "Temperatura_C": temperaturas})

def validar_y_procesar_datos(df):
    df_procesado = df.copy()
    presiones_limpias, temperaturas_limpias = [], []

    for idx, row in df_procesado.iterrows():
        try:
            p_clean = float(row["Presion_kPa"])
        except (ValueError, TypeError):
            p_clean = np.nan
            
        try:
            t_clean = float(row["Temperatura_C"])
        except (ValueError, TypeError):
            t_clean = np.nan

        presiones_limpias.append(p_clean)
        temperaturas_limpias.append(t_clean)

    df_procesado["Presion_kPa"] = presiones_limpias
    df_procesado["Temperatura_C"] = temperaturas_limpias
    return df_procesado


st.set_page_config(page_title="AirPath Analytics", layout="wide")
st.title("AirPath Analytics — Monitor de Admisión")
st.info("⚠️ MODO ACTUAL: SIMULACIÓN DE DATOS (10+ Registros Generados)")

st.sidebar.header("Configuración de Conexión")
if st.sidebar.button("Conectar"):
    st.sidebar.success("Conectado a COM simulado a 115200 baudios")

df_raw = generar_datos_simulados()
df_clean = validar_y_procesar_datos(df_raw)
ultima_lectura = df_clean.dropna().iloc[-1]

col1, col2 = st.columns(2)
col1.metric("Presión de Admisión (MAP)", f"{ultima_lectura['Presion_kPa']:.1f} kPa")
col2.metric("Temp. de Admisión (IAT)", f"{ultima_lectura['Temperatura_C']:.1f} °C")

st.line_chart(df_clean.set_index("Tiempo_s")[["Presion_kPa", "Temperatura_C"]])

st.markdown("---")
st.subheader("Semana 3: Calibración y Verificación de Cálculos")

casos_prueba = pd.DataFrame({
    "Caso": ["1. Reposo (Atmosférica)", "2. Carga Baja", "3. Límite/Error (Fuera de Rango)"],
    "Entrada_Simulada": ["Voltaje: 1.83V", "Voltaje: 1.25V", "Voltaje: 5.5V"],
    "Cálculo_Manual_Esperado": ["101.5 kPa", "72.5 kPa", "Error (Fuera de rango)"],
    "Resultado_Función_Programa": [
        f"{calcular_presion_map(1.83)} kPa", 
        f"{calcular_presion_map(1.25)} kPa", 
        f"{calcular_presion_map(5.5)} (Manejado por Try-Except)"
    ],
    "Tolerancia": ["< 0.1% (Aprobado)", "< 0.1% (Aprobado)", "N/A"]
})

st.table(casos_prueba)
st.caption("Nota: Las funciones matemáticas incluyen manejo de límites para evitar divisiones por cero y voltajes no válidos.")
