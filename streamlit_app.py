import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Intentar importar pyserial para conexión física local
try:
    import serial
    SERIAL_DISPONIBLE = True
except ImportError:
    SERIAL_DISPONIBLE = False

# ==============================================================================
# MÓDULO 1: PROCESAMIENTO Y CÁLCULOS (Matemáticas y Validación)
# ==============================================================================
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
        if pd.isna(resistencia_ohms) or resistencia_ohms <= 0: return np.nan
        temp_kelvin = 1.0 / (1.0 / t0 + (1.0 / beta) * np.log(resistencia_ohms / r_ref))
        return round(temp_kelvin - 273.15, 2)
    except Exception:
        return np.nan

def procesar_trama(trama_cruda):
    """
    Formato de trama acordado: "CONTADOR,V_MAP,R_IAT" (Ej: "15,1.83,10000")
    Retorna un diccionario con el estado de la lectura.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    if not trama_cruda or trama_cruda.strip() == "":
        return {"Tiempo": timestamp, "Contador": np.nan, "Presion_kPa": np.nan, "Temperatura_C": np.nan, "Estado": "AUSENCIA_DATOS"}
    
    partes = trama_cruda.strip().split(",")
    if len(partes) != 3:
        return {"Tiempo": timestamp, "Contador": np.nan, "Presion_kPa": np.nan, "Temperatura_C": np.nan, "Estado": "TRAMA_INCOMPLETA"}
    
    try:
        contador = int(partes[0])
        v_map = float(partes[1])
        r_iat = float(partes[2])
        
        presion = calcular_presion_map(v_map)
        temperatura = calcular_temperatura_iat(r_iat)
        
        if pd.isna(presion) or pd.isna(temperatura):
            estado = "DATO_FUERA_RANGO"
        else:
            estado = "OK"
            
        return {"Tiempo": timestamp, "Contador": contador, "Presion_kPa": presion, "Temperatura_C": temperatura, "Estado": estado}
    except ValueError:
        return {"Tiempo": timestamp, "Contador": np.nan, "Presion_kPa": np.nan, "Temperatura_C": np.nan, "Estado": "DATO_CORRUPTO"}

# ==============================================================================
# MÓDULO 2: ADQUISICIÓN (Reproducción Simulada y Hardware Serial)
# ==============================================================================
def obtener_trama_simulada(paso):
    """Genera tramas en el formato acordado, inyectando fallos de comunicación cada 5 pasos."""
    if paso % 7 == 0:
        return ""  # Simula pérdida de conexión / ausencia de datos
    if paso % 5 == 0:
        return f"{paso},1.85"  # Simula mensaje incompleto
    if paso % 6 == 0:
        return f"{paso},5.80,10000"  # Simula dato inválido (voltaje fuera de rango)
    
    v_sim = round(np.random.normal(1.83, 0.05), 2)
    r_sim = round(np.random.normal(10000, 200), 1)
    return f"{paso},{v_sim},{r_sim}"

def leer_serial_esp32(puerto, baudios):
    if not SERIAL_DISPONIBLE:
        return None
    try:
        with serial.Serial(puerto, baudios, timeout=1) as ser:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            return linea
    except Exception:
        return None

# ==============================================================================
# MÓDULO 3: REGISTRO EN MEMORIA Y EXPORTACIÓN CSV
# ==============================================================================
if "historial_datos" not in st.session_state:
    st.session_state.historial_datos = pd.DataFrame(columns=["Tiempo", "Contador", "Presion_kPa", "Temperatura_C", "Estado"])
if "paso_sim" not in st.session_state:
    st.session_state.paso_sim = 1

# ==============================================================================
# MÓDULO 4: PRESENTACIÓN (Interfaz Gráfica Streamlit)
# ==============================================================================
st.set_page_config(page_title="AirPath Analytics - Semana 4", layout="wide")
st.title("AirPath Analytics — Adquisición e Interfaz (Semana 4)")

# Barra lateral: Configuración de fuente de datos
st.sidebar.header("1. Fuente de Adquisición")
fuente = st.sidebar.radio(
    "Selecciona el origen:",
    ["Reproducción / Simulación (Hardware Pendiente)", "Hardware Físico (ESP32 Serial)"]
)

puerto_com = st.sidebar.text_input("Puerto Serial (ej. COM3 o /dev/ttyUSB0)", value="COM3")
baudios = st.sidebar.selectbox("Baudios", [115200, 9600], index=0)

st.sidebar.header("2. Control de Captura")
if st.sidebar.button("Capturar Siguiente Muestra"):
    if fuente == "Reproducción / Simulación (Hardware Pendiente)":
        trama = obtener_trama_simulada(st.session_state.paso_sim)
        st.session_state.paso_sim += 1
    else:
        trama = leer_serial_esp32(puerto_com, baudios)
    
    registro = procesar_trama(trama)
    nuevo_df = pd.DataFrame([registro])
    st.session_state.historial_datos = pd.concat([st.session_state.historial_datos, nuevo_df], ignore_index=True)

if st.sidebar.button("Generar Lote de Prueba (10 muestras)"):
    for _ in range(10):
        trama = obtener_trama_simulada(st.session_state.paso_sim)
        st.session_state.paso_sim += 1
        registro = procesar_trama(trama)
        st.session_state.historial_datos = pd.concat([st.session_state.historial_datos, pd.DataFrame([registro])], ignore_index=True)

if st.sidebar.button("Limpiar Registro"):
    st.session_state.historial_datos = pd.DataFrame(columns=["Tiempo", "Contador", "Presion_kPa", "Temperatura_C", "Estado"])
    st.session_state.paso_sim = 1

# Banner de declaración de estado de integración física
if fuente == "Reproducción / Simulación (Hardware Pendiente)":
    st.warning("⚠️ MODO REPRODUCCIÓN ACTIVO: Integración física en curso. Los datos incluyen simulación de fallos de comunicación para validar el software.")
else:
    st.info(f"🔌 MODO FÍSICO ACTIVO: Escuchando puerto {puerto_com} a {baudios} baudios.")

# Indicadores principales (KPIs) - NUNCA muestran valores viejos si la última lectura falló
df_hist = st.session_state.historial_datos

if not df_hist.empty:
    ultima = df_hist.iloc[-1]
    estado_actual = ultima["Estado"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Si la lectura actual falló, muestra "--" en lugar de repetir el dato anterior
    val_presion = f"{ultima['Presion_kPa']} kPa" if pd.notna(ultima['Presion_kPa']) else "---"
    val_temp = f"{ultima['Temperatura_C']} °C" if pd.notna(ultima['Temperatura_C']) else "---"
    val_cont = f"#{int(ultima['Contador'])}" if pd.notna(ultima['Contador']) else "N/A"
    
    col1.metric("Presión Admisión (MAP)", val_presion)
    col2.metric("Temp. Admisión (IAT)", val_temp)
    col3.metric("Muestra / Tiempo", f"{val_cont} ({ultima['Tiempo']})")
    col4.metric("Estado de Enlace", estado_actual)

    # Gráfica en tiempo real
    st.subheader("Tendencia de Variables Válidas")
    st.line_chart(df_hist.set_index("Tiempo")[["Presion_kPa", "Temperatura_C"]])

    # Tabla de registro y botón de exportación CSV
    st.subheader("Registro de Datos y Manejo de Errores")
    st.dataframe(df_hist.tail(15), use_container_width=True)
    
    csv_data = df_hist.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Registro a CSV",
        data=csv_data,
        file_name=f"airpath_datos_S4_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
else:
    st.info("Presiona 'Capturar Siguiente Muestra' o 'Generar Lote de Prueba' en el menú izquierdo para iniciar la adquisición.")
