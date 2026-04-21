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
    st.header("1. Obliczenie Kolimacji")
    
    st.subheader("Import danych z pliku lub tabeli")
    st.info("Wgraj plik .txt (odczytI odczytII) lub wpisz dane ręcznie do tabeli.")

    # --- FUNKCJA IMPORTU Z PLIKU ---
    uploaded_file_col = st.file_uploader("Wybierz plik tekstowy dla kolimacji", type=['txt'], key="upload_kol")
    
    # Przygotowanie listy startowej dla tabeli
    initial_data = []
    
    if uploaded_file_col is not None:
        content = uploaded_file_col.read().decode("utf-8").splitlines()
        for line in content:
            parts = line.replace(',', '.').split() # obsługa przecinków i kropek
            if len(parts) >= 2:
                try:
                    initial_data.append({"KI": float(parts[0]), "KII": float(parts[1])})
                except ValueError:
                    continue
        st.success(f"Zaimportowano {len(initial_data)} wierszy z pliku.")
    else:
        # Przykładowe dane z Twoich wytycznych
        initial_data = [
            {"KI": 101.4598, "KII": 301.4586},
            {"KI": 101.4596, "KII": 301.4588},
            {"KI": 101.4599, "KII": 301.4594}
        ]

    # --- EDYTOR TABELI (Zawsze widoczny) ---
    col_data = st.data_editor(initial_data, num_rows="dynamic", key="kol_editor_v2", use_container_width=True)

    # --- OBLICZENIA STATYSTYCZNE ---
    deltas = []
    for d in col_data:
        if d.get('KI') is not None and d.get('KII') is not None:
            diff = d['KII'] - d['KI']
            # Normalizacja różnicy do zakresu ok. 200g
            if diff < 0: diff += 400
            # Obliczenie delty w cc
            val = ((diff - 200) / 2) * 10000
            deltas.append(val)

    if deltas:
        c_sr = statistics.mean(deltas)
        # Błąd średni kolimacji średniej
        if len(deltas) > 1:
            m_c_sr = statistics.stdev(deltas) / math.sqrt(len(deltas))
        else:
            m_c_sr = 0

        res1, res2 = st.columns(2)
        res1.metric("Kolimacja średnia (c) [cc]", f"{c_sr:.2f}")
        res2.metric("Błąd kolimacji (mc) [cc]", f"± {m_c_sr:.2f}")

        st.divider()

        # --- POPRAWIONY ODCZYT KOŁA POZIOMEGO ---
        st.subheader("Oblicz poprawiony odczyt koła poziomego")
        c_hz, c_v = st.columns(2)
        hz_raw = c_hz.number_input("Odczyt koła poziomego [g]", value=0.0, format="%.4f")
        v_raw = c_v.number_input("Odczyt koła pionowego (z) [g]", value=100.0, format="%.4f")

        z_rad = (v_raw * math.pi) / 200
        if math.sin(z_rad) != 0:
            # Hz_popr = Hz - c/sin(z)
            poprawka_grad = (c_sr / 10000) / math.sin(z_rad)
            hz_popr = hz_raw - poprawka_grad
            st.success(f"**Poprawiony odczyt koła poziomego:** {hz_popr:.4f} g")
        else:
            st.warning("Nie można obliczyć poprawki dla z = 0 lub z = 200.")












# --- ZAKŁADKA 2: INKLINACJA ---
# --- ZAKŁADKA 2: INKLINACJA ---
with tabs[1]:
    st.header("2. Obliczanie Inklinacji")
    
    st.subheader("Parametry stałe serii")
    c1, c2, c3 = st.columns(3)
    c_fixed = c1.number_input("Stała kolimacja c [cc]", value=5.5, step=0.1)
    mc_fixed = c2.number_input("mc [cc]", value=0.9, step=0.1)
    z_grad_inc = c3.number_input("Odległość zenitowa serii z [g]", value=81.9768, format="%.4f")

    st.divider()
    st.subheader("Import danych pomiarowych")
    uploaded_file_inc = st.file_uploader("Wgraj plik .txt dla inklinacji", type=['txt'], key="upload_inc_final")
    
    inc_initial = []
    if uploaded_file_inc is not None:
        content = uploaded_file_inc.read().decode("utf-8").splitlines()
        for line in content:
            parts = line.replace(',', '.').split()
            if len(parts) >= 2:
                try:
                    inc_initial.append({"KI": float(parts[0]), "KII": float(parts[1])})
                except ValueError:
                    continue
    else:
        inc_initial = [
            {"KI": 60.2702, "KII": 260.2679},
            {"KI": 60.2706, "KII": 260.2688},
            {"KI": 60.2710, "KII": 260.2686}
        ]

    inc_editor = st.data_editor(inc_initial, num_rows="dynamic", key="inc_editor_f", use_container_width=True)

    if inc_editor:
        z_rad_i = (z_grad_inc * math.pi) / 200
        i_values = []
        for d in inc_editor:
            if d.get('KI') is not None and d.get('KII') is not None:
                diff = d['KII'] - d['KI']
                if diff < 0: diff += 400
                delta_cc = ((diff - 200) / 2) * 10000
                val_i = (delta_cc - (c_fixed / math.sin(z_rad_i))) * math.tan(z_rad_i)
                i_values.append(val_i)

   if i_values:
            i_sr = statistics.mean(i_values)
            mi_pom = statistics.stdev(i_values) / math.sqrt(len(i_values)) if len(i_values) > 1 else 0
            mi_z_kol = abs(mc_fixed / math.cos(z_rad_i))
            mi_total = math.sqrt(mi_pom**2 + mi_z_kol**2)
            
            res_i1, res_i2 = st.columns(2)
            res_i1.metric("Inklinacja średnia (i) [cc]", f"{i_sr:.2f}")
            res_i2.metric("Błąd inklinacji (mi) [cc]", f"± {mi_total:.2f}")

            # --- NOWA SEKCJA: OKIENKA DO OBLICZEŃ PUNKTOWYCH ---
            st.divider()
            st.subheader("Oblicz poprawiony odczyt koła poziomego")
            st.write("Wpisz dane dla konkretnego punktu, aby zastosować wyznaczoną poprawkę inklinacji.")
            
            c_calc1, c_calc2 = st.columns(2)
            hz_punkt = c_calc1.number_input("Odczyt koła poziomego [g]", value=0.0, format="%.4f", key="hz_p_inc")
            z_punkt = c_calc2.number_input("Odczyt koła pionowego (z) [g]", value=100.0, format="%.4f", key="z_p_inc")
            
            # Przeliczenie na radiany
            z_p_rad = (z_punkt * math.pi) / 200
            
            if math.sin(z_p_rad) != 0 and math.tan(z_p_rad) != 0:
                # Obliczenie poprawki w gradach (dzielimy cc przez 10 000)
                poprawka_c = (c_fixed / math.sin(z_p_rad)) / 10000
                poprawka_i = (i_sr / math.tan(z_p_rad)) / 10000
                
                hz_poprawiony = hz_punkt - poprawka_c - poprawka_i
                
                st.success(f"Poprawiony odczyt koła poziomego: **{hz_poprawiony:.4f} g**")
            else:
                st.error("Nie można obliczyć poprawki dla odczytu pionowego bliskiego 0 lub 200g.")








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
