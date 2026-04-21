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
    st.info("Dane importowane z tabeli poniżej (zgodnie z wytycznymi)")
    
    col_data = st.data_editor([
        {"KI": 101.4598, "KII": 301.4586},
        {"KI": 101.4596, "KII": 301.4588},
        {"KI": 101.4599, "KII": 301.4594}
    ], num_rows="dynamic", key="kol_tab")

    if col_data:
        # Filtrowanie pustych wierszy i obliczenia
        deltas = []
        for d in col_data:
            if d.get('KI') is not None and d.get('KII') is not None:
                delta = ((abs(d['KII'] - d['KI']) - 200) / 2) * 10000
                deltas.append(delta)
        
        if deltas:
            c_sr = statistics.mean(deltas)
            mc = statistics.stdev(deltas) / math.sqrt(len(deltas)) if len(deltas) > 1 else 0
            
            st.metric("Kolimacja średnia (c)", f"{c_sr:.2f} cc")
            st.metric("Błąd kolimacji (mc)", f"± {mc:.2f} cc")

            st.divider()
            st.subheader("Poprawiony odczyt koła poziomego")
            c_input = st.number_input("Odczyt Hz [g]", value=100.0, step=0.0001, format="%.4f")
            z_input = st.number_input("Odczyt V (z) [g]", value=100.0, step=0.0001, format="%.4f", key="z_kol")
            
            z_rad = (z_input * math.pi) / 200
            if math.sin(z_rad) != 0:
                hz_popr = c_input - (c_sr / 10000) / math.sin(z_rad)
                st.write(f"**Poprawiony odczyt Hz:** {hz_popr:.4f} g")
            else:
                st.error("Błąd: sin(z) = 0")

# --- ZAKŁADKA 2: INKLINACJA ---
with tabs[1]:
    st.header("Obliczanie Inklinacji")
    
    c1, c2, c3 = st.columns(3)
    c_stale = c1.number_input("Stała kolimacja c [cc]", value=5.5)
    mc_stale = c2.number_input("mc [cc]", value=0.9)
    z_grad = c3.number_input("z [g]", value=81.9768, format="%.4f")

    inc_data = st.data_editor([
        {"KI": 60.2702, "KII": 260.2679},
        {"KI": 60.2706, "KII": 260.2688},
        {"KI": 60.2710, "KII": 260.2686}
    ], num_rows="dynamic", key="inc_tab")

    if inc_data:
        z_rad_inc = (z_grad * math.pi) / 200
        deltas_inc = []
        for d in inc_data:
            if d.get('KI') is not None and d.get('KII') is not None:
                delta = ((abs(d['KII'] - d['KI']) - 200) / 2) * 10000
                deltas_inc.append(delta)
        
        i_wyznaczone = [(d - (c_stale / math.sin(z_rad_inc))) * math.tan(z_rad_inc) for d in deltas_inc]
        
        if i_wyznaczone:
            i_sr = statistics.mean(i_wyznaczone)
            mi = statistics.stdev(i_wyznaczone) / math.sqrt(len(i_wyznaczone)) if len(i_wyznaczone) > 1 else 0
            
            st.metric("Inklinacja średnia (i)", f"{i_sr:.2f} cc")
            st.metric("Błąd inklinacji (mi)", f"± {mi:.2f} cc")

# --- ZAKŁADKA 3: Ng0 ---
with tabs[2]:
    st.header("Współczynnik Ng0")
    fale = np.arange(400, 1610, 10)
    # Przykładowy wzór
    ng0_values = [287.604 + (1.6288 / (f/1000)**2) + (0.0136 / (f/1000)**4) for f in fale] 
    
    df_ng0 = pd.DataFrame({"Długość fali [nm]": fale, "Ng0": ng0_values})
    st.line_chart(df_ng0.set_index("Długość fali [nm]"))
    st.dataframe(df_ng0)

# --- ZAKŁADKA 4: POPRAWKA ATMOSFERYCZNA ---
with tabs[3]:
    st.header("Poprawka Atmosferyczna")
    st.info("Dane wprowadzane przez użytkownika")
    
    ca, cb = st.columns(2)
    with ca:
        wave = st.number_input("Długość fali [nm]", value=633.0)
        ts = st.number_input("Temperatura sucha [°C]", value=15.0)
        tm = st.number_input("Temperatura mokra [°C]", value=12.0)
    with cb:
        p = st.number_input("Ciśnienie [hPa]", value=1002.48)
        dist_raw = st.number_input("Pomierzona długość [m]", value=5177.02)

    st.divider()
    st.subheader("Wczytanie z pliku (lp; ts; tm; p; długość)")
    file_atm = st.file_uploader("Wgraj plik tekstowy", type=['txt', 'csv'])
    if file_atm:
        st.write("Plik wczytany poprawnie (obliczenia w trakcie implementacji...)")

# --- ZAKŁADKA 5: ŁUK A CIĘCIWA ---
with tabs[4]:
    st.header("Różnica łuk-cięciwa")
    R = 6371000 # m
    odleglosci = np.arange(1, 101, 1)
    # Roznica w mm: (s - 2R sin(s/2R)) * 1000
    roznica = [((s*1000) - (2*R * math.sin((s*1000)/(2*R)))) * 1000 for s in odleglosci]
    
    df_arc = pd.DataFrame({"Odległość [km]": odleglosci, "Różnica [mm]": roznica})
    st.line_chart(df_arc.set_index("Odległość [km]"))
    st.dataframe(df_arc)

# --- ZAKŁADKA 6: RS232 ---
with tabs[5]:
    st.header("Obsługa portu RS232")
    st.write("Status: Oczekiwanie na połączenie szeregowe...")
