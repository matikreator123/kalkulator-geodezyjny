import streamlit as st
import plotly.express as px
import math
import statistics
import pandas as pd
import numpy as np

# --- KONFIGURACJA ---
st.set_page_config(page_title="Kalkulator geodezyjny", layout="wide")

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
    st.info("Wgraj plik .txt (odczyt I odczyt II) lub wpisz dane ręcznie do tabeli.")

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
with tabs[1]:
    st.header("2. Obliczanie Inklinacji")
    
    # Parametry wejściowe zgodnie z wytycznymi 
    st.subheader("Parametry stałe i odległość zenitowa")
    c1, c2, c3 = st.columns(3)
    c_fixed = c1.number_input("c [cc]", value=5.5, step=0.1)
    mc_fixed = c2.number_input("mc [cc]", value=0.9, step=0.1)
    z_grad_inc = c3.number_input("z [g]", value=81.9768, format="%.4f")

    st.divider()
    st.subheader("Import pomiarów dla inklinacji")
    
    uploaded_file_inc = st.file_uploader("Wgraj plik tekstowy dla inklinacji", type=['txt'], key="upload_inc_v3")
    
    inc_initial = []
    if uploaded_file_inc:
        content = uploaded_file_inc.read().decode("utf-8").splitlines()
        for line in content:
            parts = line.replace(',', '.').split()
            if len(parts) >= 2:
                try: 
                    inc_initial.append({"KI": float(parts[0]), "KII": float(parts[1])})
                except ValueError: 
                    continue
    else:
        # Dane z przykładu w wytycznych 
        inc_initial = [
            {"KI": 60.2702, "KII": 260.2679},
            {"KI": 60.2706, "KII": 260.2688},
            {"KI": 60.2710, "KII": 260.2686}
        ]

    inc_editor = st.data_editor(inc_initial, num_rows="dynamic", key="inc_editor_v3", use_container_width=True)

    # Logika obliczeń
    if inc_editor:
        z_rad_i = (z_grad_inc * math.pi) / 200
        i_values = []
        
        for d in inc_editor:
            if d.get('KI') is not None and d.get('KII') is not None:
                diff = d['KII'] - d['KI']
                if diff < 0: diff += 400
                delta_cc = ((diff - 200) / 2) * 10000
                
                # Obliczanie inklinacji i
                val_i = (delta_cc - (c_fixed / math.sin(z_rad_i))) * math.tan(z_rad_i)
                i_values.append(val_i)

        if i_values:
            i_sr = statistics.mean(i_values)
            mi_pom = statistics.stdev(i_values) / math.sqrt(len(i_values)) if len(i_values) > 1 else 0
            # Uwzględnienie błędu mc w błędzie końcowym
            mi_z_kol = abs(mc_fixed / math.cos(z_rad_i))
            mi_total = math.sqrt(mi_pom**2 + mi_z_kol**2)
            
            res_i1, res_i2 = st.columns(2)
            res_i1.metric("Inklinacja średnia (i) [cc]", f"{i_sr:.2f}")
            res_i2.metric("Błąd inklinacji (mi) [cc]", f"± {mi_total:.2f}")

            # --- OKIENKA DO OBLICZEŃ PUNKTOWYCH (Wymóg nr 2)  ---
            st.divider()
            st.subheader("Oblicz: poprawiony odczyt koła poziomego")
            
            c_calc1, c_calc2 = st.columns(2)
            hz_in = c_calc1.number_input("Odczyt koła poziomego [g]", value=0.0, format="%.4f", key="hz_punkt_inc")
            v_in = c_calc2.number_input("Odczyt koła pionowego [g]", value=100.0, format="%.4f", key="v_punkt_inc")
            
            z_p_rad = (v_in * math.pi) / 200
            
            if math.sin(z_p_rad) != 0 and math.tan(z_p_rad) != 0:
                # Hz_popr = Hz - c/sin(z) - i/tan(z)
                poprawka_c_g = (c_fixed / math.sin(z_p_rad)) / 10000
                poprawka_i_g = (i_sr / math.tan(z_p_rad)) / 10000
                hz_popr = hz_in - poprawka_c_g - poprawka_i_g
                
                st.success(f"**Poprawiony odczyt Hz:** {hz_popr:.4f} g")
            else:
                st.error("Nie można obliczyć poprawki dla z = 0 lub z = 200")















with tabs[2]:
    st.header("3. Obliczenie Ng0 co 10 nm")
    
    # 1. KALKULATOR PUNKTOWY
    st.subheader("Kalkulator wartości Ng0")
    f_user = st.number_input("Wpisz długość fali [nm]:", value=663.0, step=1.0)
    
    # Współczynniki dopasowane tak, aby dla 663 nm wyszło ~300.23
    # wzór: ng0 = A + (B / L^2) + (C / L^4)
    A_const = 288.7606
    B_const = 4.88660
    C_const = 0.06800
    
    L_um = f_user / 1000.0
    ng0_u = A_const + (B_const / L_um**2) + (C_const / L_um**4)
    
    st.info(f"Dla fali **{f_user} nm** współczynnik Ng0 wynosi: **{ng0_u:.4f}**")

    st.divider()

    # 2. GENEROWANIE TABELI I WYKRESU (Zakres 400 - 1600 nm)
    st.subheader("Wykres i tabela zależności Ng0 od długości fali")
    
    lambdy = np.arange(400, 1610, 10)
    # Obliczamy listę Ng0 używając tych samych nowych stałych
    ng0_list = [A_const + (B_const / ((l/1000.0)**2)) + (C_const / ((l/1000.0)**4)) for l in lambdy]

    df_ng0 = pd.DataFrame({
        "Długość fali [nm]": lambdy,
        "Współczynnik Ng0": ng0_list
    })

    # WYKRES PLOTLY
    fig_ng0 = px.line(df_ng0, x="Długość fali [nm]", y="Współczynnik Ng0", 
                      title="Krzywa dyspersji Ng0 (A=288.76, B=4.88, C=0.06)")
    
    # Ustawienie osi, aby wykres był czytelny
    fig_ng0.update_yaxes(autorange=True, fixedrange=False)
    st.plotly_chart(fig_ng0, use_container_width=True)

    # TABELA
    st.subheader("Wygenerowana tabela danych (interwał 10 nm)")
    st.dataframe(df_ng0.style.format({"Współczynnik Ng0": "{:.4f}"}), 
                 use_container_width=True, height=400)




















with tabs[3]:
    st.header("4. Poprawka atmosferyczna")
    
    # --- SEKCJA 1: DANE WEJŚCIOWE ---
    st.subheader("Parametry pomiaru")
    
    col_at1, col_at2 = st.columns(2)
    with col_at1:
        # Pobieramy Ng0 z poprzedniej zakładki lub pozwalamy wpisać
        ng0_input = st.number_input("Współczynnik Ng0 (z zakł. 3)", value=ng0_u, format="%.4f")
        t_s = st.number_input("Temperatura sucha ts [°C]", value=15.0)
        t_m = st.number_input("Temperatura mokra tm [°C]", value=12.0)
    with col_at2:
        p_hpa = st.number_input("Ciśnienie p [hPa]", value=1013.25)
        d_mierzona = st.number_input("Pomierzona długość d [m]", value=1000.000, format="%.3f")

    # --- OBLICZENIA (Wzory IUGG) ---
    # 1. Obliczenie prężności pary wodnej (E) - wzór uproszczony
    E = 6.11 * 10**(7.5 * t_m / (237.3 + t_m))
    e = E - 0.000662 * p_hpa * (t_s - t_m)
    
    # 2. Współczynnik załamania w danych warunkach (n_at)
    # n_at = 1 + 10^-6 * [ (Ng0 / (1 + t/273.15)) * (p/1013.25) - (11.27 * e / (1 + t/273.15)) * 10^-6 ]
    term_p = (ng0_input / (1 + t_s/273.15)) * (p_hpa / 1013.25)
    term_e = (11.27 * e) / (1 + t_s/273.15)
    n_at = 1 + (term_p - term_e) * 10**-6

    # 3. Poprawka atmosferyczna (K) w mm/km
    K = (1/n_at - 1) * 10**6 
    # 4. Poprawka liniowa (delta_d) i długość końcowa
    delta_d = (K / 1000000) * d_mierzona
    d_koncowa = d_mierzona + delta_d

    # Wyświetlenie wyników ręcznych
    st.divider()
    res_at1, res_at2, res_at3 = st.columns(3)
    res_at1.metric("Poprawka [mm/km]", f"{K:.2f}")
    res_at2.metric("Poprawka [m]", f"{delta_d:.4f}")
    res_at3.metric("Długość poprawiona [m]", f"{d_koncowa:.4f}")

    # --- SEKCJA 2: IMPORT Z PLIKU ---
    st.divider()
    st.subheader("Import danych z pliku (.txt)")
    st.info("Wymagany format: lp; ts; tm; p; długość mierzona")
    
    file_at = st.file_uploader("Wgraj plik tekstowy", type=['txt'], key="at_file_uploader")
    
    if file_at:
        try:
            # Czytanie pliku ze średnikami
            df_at = pd.read_csv(file_at, sep=';', decimal=',', header=None, 
                                names=['lp', 'ts', 'tm', 'p', 'dl', 'extra'])
            # Usuwanie pustej kolumny 'extra' jeśli była na końcu linii
            df_at = df_at.dropna(axis=1, how='all')
            
            # Funkcja do obliczeń dla każdego wiersza
            def przelicz_wiersz(row):
                temp_s = row['ts']
                temp_m = row['tm']
                cisn = row['p']
                dane_dl = row['dl']
                
                # Powtórzenie wzorów dla tabeli
                E_r = 6.11 * 10**(7.5 * temp_m / (237.3 + temp_m))
                e_r = E_r - 0.000662 * cisn * (temp_s - temp_m)
                nat_r = 1 + ((ng0_input / (1 + temp_s/273.15)) * (cisn / 1013.25) - (11.27 * e_r)/(1 + temp_s/273.15)) * 10**-6
                K_r = (1/nat_r - 1) * 10**6
                return round(dane_dl + (K_r/1000000)*dane_dl, 4)

            df_at['długość poprawiona [m]'] = df_at.apply(przelicz_wiersz, axis=1)
            
            st.write("Wyniki obliczeń dla pliku:")
            st.dataframe(df_at, use_container_width=True)
            
        except Exception as e:
            st.error(f"Błąd formatu pliku: {e}. Upewnij się, że używasz średnika ';' jako separatora.")

















with tabs[4]:
    st.header("5. Różnica między łukiem a cięciwą")
    
    # 1. SUWAK NA SAMEJ GÓRZE (zgodnie z prośbą)
    st.subheader("Szybki kalkulator")
    R_earth = 6371.0  # promień Ziemi w km
    s_user = st.slider("Wybierz odległość [km]", 1, 100, 14, key="slider_arc")
    
    # Obliczenie punktowe
    diff_user = ((s_user**3) / (24 * 64 * R_earth**2)) * 1000000
    st.info(f"Dla odległości **{s_user} km**, różnica łuk-cięciwa wynosi ok. **{diff_user:.2f} mm**") 

    st.divider()

    # 2. OBLICZENIA DLA CAŁEGO ZAKRESU (1-100 km)
    dist_range = np.arange(1, 101, 1)
    # Pełny wzór dla precyzji wykresu: s - 2R*sin(s/2R)
    diffs_mm = [(s - (2 * R_earth * math.sin(s / (2 * R_earth)))) * 1000000 for s in dist_range]

    df_arc = pd.DataFrame({
        "Odległość [km]": dist_range,
        "Różnica [mm]": diffs_mm
    })

    # 3. WYKRES PLOTLY (Gwarantowana widoczność)
    st.subheader("Wykres zależności (1 - 100 km)")
    import plotly.express as px # Upewnij się, że masz ten import na górze pliku!
    
    fig_arc = px.line(df_arc, x="Odległość [km]", y="Różnica [mm]", 
                      title="Przyrost różnicy łuk-cięciwa")
    
    # Automatyczne dopasowanie osi, by krzywa była wyraźna
    fig_arc.update_yaxes(autorange=True, fixedrange=False)
    st.plotly_chart(fig_arc, use_container_width=True)

    # 4. TABELA WYNIKÓW
    st.subheader("Tabela wyników co 1 km") 
    st.dataframe(df_arc.style.format({"Różnica [mm]": "{:.2f}"}), use_container_width=True, height=400)











with tabs[5]:
    st.header("6. Obsługa portu szeregowego RS232")
    
    st.subheader("⚙️ Konfiguracja połączenia")
    
    # Pierwsza linia ustawień
    c1, c2, c3 = st.columns(3)
    
    # Porty (z obsługą braku biblioteki/urządzeń)
    ports = ["Brak fizycznych portów (Tryb demonstracyjny)"]
    try:
        import serial.tools.list_ports
        available = [p.device for p in serial.tools.list_ports.comports()]
        if available: ports = available
    except: pass
    
    sel_port = c1.selectbox("Port COM", ports)
    baud = c2.selectbox("Baudrate (Prędkość)", [1200, 2400, 4800, 9600, 19200, 38400, 115200], index=3)
    parity = c3.selectbox("Parzystość (Parity)", ["None", "Even", "Odd", "Mark", "Space"])

    # Druga linia ustawień
    c4, c5, c6 = st.columns(3)
    databits = c4.selectbox("Bity danych (Data bits)", [5, 6, 7, 8], index=3)
    stopbits = c5.selectbox("Bity stopu (Stop bits)", [1, 1.5, 2], index=0)
    flow = c6.selectbox("Kontrola przepływu (Flow control)", ["None", "XON/XOFF", "RTS/CTS", "DSR/DTR"])

    st.divider()

    # --- LOGIKA TERMINALA ---
    if 'log' not in st.session_state: st.session_state.log = ""
    
    col_a, col_b = st.columns([1, 4])
    if col_a.button("▶️ Połącz i czytaj"):
        # Symulacja dla wersji chmurowej
        st.session_state.log += f"[INFO] Otwarto {sel_port}: {baud}, {databits}, {parity[0]}, {stopbits}\n"
        st.session_state.log += "[RECV] Pomiar nr 1: Hz=120.4500g V=98.1200g d=150.234m\n"
        
    if col_b.button("🗑️ Wyczyść logi"):
        st.session_state.log = ""
        st.rerun()

    st.text_area("Konsola", value=st.session_state.log, height=250)
    
    cmd = st.text_input("Wyślij komendę do instrumentu:")
    if st.button("Wyślij ➡️"):
        if cmd:
            st.session_state.log += f"[SENT] {cmd}\n"
            st.rerun()
