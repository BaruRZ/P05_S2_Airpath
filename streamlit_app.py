# ==========================================
# IMPORTACIÓN DE LIBRERÍAS (HERRAMIENTAS)
# ==========================================
import streamlit as st # Librería principal para crear la interfaz gráfica (el dashboard web)
import pandas as pd    # Librería para manejar tablas de datos (DataFrames)
import numpy as np     # Librería para operaciones matemáticas y manejar datos nulos (NaN)

# ==========================================
# FUNCIONES SEMANA 3: CÁLCULOS Y LÍMITES
# ==========================================

def calcular_presion_map(voltaje, v_ref=5.0):
    """
    Convierte el voltaje leído por el ESP32 a Presión Absoluta (kPa).
    Utiliza la ecuación de transferencia de un sensor MAP típico (ej. MPX4250AP).
    """
    try:
        # 1. Tratamiento de límites: Si el dato está vacío, devuelve 'NaN' (Not a Number)
        if pd.isna(voltaje): 
            return np.nan
            
        # 2. Tratamiento de límites: Verifica que el voltaje esté dentro del rango lógico (0.1V a 4.9V)
        if voltaje < 0.1 or voltaje > 4.9: 
            raise ValueError("Fuera de rango") # Si sale del rango, provoca un error controlado
            
        # 3. Ecuación matemática: Despeje de la presión en kPa
        presion_kpa = (voltaje / v_ref + 0.04) / 0.004
        
        # Devuelve el resultado redondeado a 2 decimales
        return round(presion_kpa, 2)
        
    except Exception:
        # Si ocurre CUALQUIER error (como un texto en vez de un número), no colapsa, solo devuelve NaN
        return np.nan

def calcular_temperatura_iat(resistencia_ohms, r_ref=10000.0, beta=3950.0, t0=298.15):
    """
    Convierte la resistencia eléctrica del termistor (NTC) a Temperatura en grados Celsius (°C).
    Utiliza la Ecuación Beta.
    """
    try:
        if pd.isna(resistencia_ohms): 
            return np.nan
            
        # 1. Tratamiento de límites: Evita la división por cero matemática (si la resistencia es 0 o negativa)
        if resistencia_ohms <= 0: 
            raise ValueError("División por cero")
            
        # 2. Ecuación Beta: Calcula la temperatura en grados Kelvin
        temp_kelvin = 1.0 / (1.0 / t0 + (1.0 / beta) * np.log(resistencia_ohms / r_ref))
        
        # 3. Convierte de Kelvin a Celsius restando 273.15 y redondea
        return round(temp_kelvin - 273.15, 2)
        
    except Exception:
        return np.nan

# ==========================================
# FUNCIONES SEMANA 2: SIMULACIÓN DE DATOS
# ==========================================

def generar_datos_simulados(num_registros=12):
    """
    Genera una tabla (DataFrame) con datos inventados para poder probar el dashboard
    sin necesidad de tener el ESP32 conectado aún.
    """
    np.random.seed(42) # Fija los números aleatorios para que siempre salgan los mismos al probar
    
    # Genera una lista de tiempos (1, 2, 3... 12)
    tiempos = list(range(1, num_registros + 1))
    
    # Genera datos aleatorios simulando la presión (rondando los 101.3 kPa) y temperatura (24.8 °C)
    presiones = list(np.random.normal(loc=101.3, scale=2.5, size=num_registros))
    temperaturas = list(np.random.normal(loc=24.8, scale=1.0, size=num_registros))
    
    # INYECCIÓN DE ERRORES INTENCIONALES (Para cumplir la rúbrica de probar fallos)
    presiones[4] = "ERROR_SENSOR" # Metemos un texto en lugar de un número (Dato inválido)
    temperaturas[8] = None          # Metemos un dato vacío/ausente
    
    # Empaqueta todo en una tabla de Pandas y la devuelve
    return pd.DataFrame({"Tiempo_s": tiempos, "Presion_kPa": presiones, "Temperatura_C": temperaturas})

def validar_y_procesar_datos(df):
    """
    Toma la tabla cruda, revisa dato por dato y limpia los errores (como el "ERROR_SENSOR")
    para que la gráfica no explote al intentar dibujar un texto.
    """
    df_procesado = df.copy()
    presiones_limpias, temperaturas_limpias = [], []

    # Recorre fila por fila la tabla
    for idx, row in df_procesado.iterrows():
        #
