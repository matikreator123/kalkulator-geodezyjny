import streamlit as st
import math
import statistics
import pandas as pd
import numpy as np

# --- KONFIGURACJA ---
st.set_page_config(page_title="Projekt ETP GI", layout="wide")

# --- ZAKŁADKI ---
tabs = st.tabs([
    "1. Kolimacja", 
    "2. Inklinacja", 
    "3. Ng0 (Wykres/Tabela)", 
    "4. Poprawka atmosferyczna", 
    "5. Łuk a cięciwa",
    "6. RS232"
])

# --- ZAKŁADKA 1: KOLIMACJA ---
with tabs[0]:
    st.header("Obliczanie Kolimacji")
    st.info("Dane importowane z tabeli poniżej (zgodnie z wytycznymi)") [cite: 1]
    
    col_data = st.data_editor([
        {"KI": 101.4598, "KII": 301.4586},
        {"KI": 101.4596, "KII": 301.4588},
        {"KI": 101.4599, "KII": 301.4594}
    ], num_rows="dynamic", key="kol_tab") [cite: 1]

    if col_data:
        deltas = [((abs(d['KII'] - d['KI']) - 200) / 2) * 10000 for d in col_data if d['KI'] and d['KII']]
        if deltas:
            c_sr = statistics.mean(deltas)
            mc = statistics.stdev(deltas) / math.sqrt(len(deltas)) if len(deltas) > 1 else 0
            
            st.metric("Kolimacja średnia (c)", f"{c_sr:.2f} cc") [cite: 1]
            st.metric("Błąd kolimacji (mc)", f"± {mc:.2f} cc") [cite: 1]

            st.divider()
            st.subheader("Poprawiony odczyt koła poziomego") [cite: 1]
            c_input = st.number_input("Odczyt Hz [g]", value=100.0, step=0.0001, format="%.4f")
            z_input = st.number_input("Odczyt V (z) [g]", value=100.0, step=0.0001, format="%.4f", key="z_kol")
            
            z_rad = (z_input * math.pi) / 200
            hz_popr = c_input - (c_sr / 10000) / math.sin(z_rad)
            st.write(f"**Poprawiony odczyt Hz:** {hz_popr:.4f} g") [cite: 1]

# --- ZAKŁADKA 2: INKLINACJA ---
with tabs[1]:
    st.header("Obliczanie Inklinacji")
    
    c1, c2, c3 = st.columns(3)
    c_stale = c1.number_input("Stała kolimacja c [cc]", value=5.5) [cite: 1]
    mc_stale = c2.number_input("mc [cc]", value=0.9) [cite: 1]
    z_grad = c3.number_input("z [g]", value=81.9768, format="%.4f") [cite: 1]

    inc_data = st.data_editor([
        {"KI": 60.2702, "KII": 260.2679},
        {"KI": 60.2706, "KII": 260.2688},
        {"KI": 60.2710, "KII": 260.2686}
    ], num_rows="dynamic", key="inc_tab") [cite: 1]

    if inc_data:
        z_rad_inc = (z_grad * math.pi) / 200
        # Obliczanie delty i wyciąganie inklinacji i
        deltas_inc = [((abs(d['KII'] - d['KI']) - 200) / 2) * 10000 for d in inc_data if d['KI'] and d['KII']]
        i_wyznaczone = [(d - (c_stale / math.sin(z_rad_inc))) * math.tan(z_rad_inc) for d in deltas_inc]
        
        if i_wyznaczone:
            i_sr = statistics.mean(i_wyznaczone)
            mi = statistics.stdev(i_wyznaczone) / math.sqrt(len(i_wyznaczone)) if len(i_wyznaczone) > 1 else 0
            
            st.metric("Inklinacja średnia (i)", f"{i_sr:.2f} cc") [cite: 1]
            st.metric("Błąd inklinacji (mi)", f"± {mi:.2f} cc") [cite: 1]

# --- ZAKŁADKA 3: Ng0 ---
with tabs[2]:
    st.header("Współczynnik Ng0") [cite: 1]
    # Przykładowy uproszczony wzór Cauchy'ego dla demonstracji wymagań
    fale = np.arange(400, 1610, 10) [cite: 2]
    # Przykładowe obliczenie (należy podstawić właściwy wzór geodezyjny)
    ng0_values = [287.604 + (1.6288 / (f/1000)**2) + (0.0136 / (f/1000)**4) for f in fale] 
    
    df_ng0 = pd.DataFrame({"Długość fali [nm]": fale, "Ng0": ng0_values})
    st.line_chart(df_ng0.set_index("Długość fali [nm]")) [cite: 2]
    st.dataframe(df_ng0) [cite: 2]

# --- ZAKŁADKA 4: POPRAWKA ATMOSFERYCZNA ---
with tabs[3]:
    st.header("Poprawka Atmosferyczna") [cite: 1]
    c1, c2 = st.columns(2)
    with c1:
        wave = st.number_input("Długość fali [nm]", value=633.0) [cite: 3]
        ts = st.number_input("Temperatura sucha [°C]", value=15.0) [cite: 3]
        tm = st.number_input("Temperatura mokra [°C]", value=12.0) [cite: 3]
    with c2:
        p = st.number_input("Ciśnienie [hPa]", value=1013.25) [cite: 3]
        dist = st.number_input("Pomierzona długość [m]", value=500.0) [cite: 3]
    
    # Miejsce na Twoje wzory poprawek
    st.info("Tutaj należy zaimplementować wzory Barrella i Searsa lub podobne.") [cite: 3]
    st.write("**Poprawka na km:** 0.00 mm") [cite: 3]
    st.write("**Długość poprawiona:** 0.0000 m") [cite: 3]

# --- ZAKŁADKA 5: ŁUK A CIĘCIWA ---
with tabs[4]:
    st.header("Różnica łuk-cięciwa") [cite: 1]
    R = 6371000 # Promień Ziemi w m
    odleglosci = np.arange(1, 101, 1) # od 1 do 100 km [cite: 5]
    
    # d = s - 2R * sin(s/2R)
    roznica = [( (s*1000) - (2*R * math.sin((s*1000)/(2*R))) ) * 1000 for s in odleglosci]
    
    df_arc = pd.DataFrame({"Odległość [km]": odleglosci, "Różnica [mm]": roznica})
    st.line_chart(df_arc.set_index("Odległość [km]")) [cite: 5]
    st.table(df_arc) [cite: 5]

# --- ZAKŁADKA 6: RS232 ---
with tabs[5]:
    st.header("Obsługa Portu RS232") [cite: 1]
    st.warning("Obsługa portu szeregowego w przeglądarce (Streamlit Cloud) jest ograniczona. Lokalne działanie wymaga biblioteki `pyserial`.")
