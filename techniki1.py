import streamlit as st
import math
import statistics
import os

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Kalkulator Geodezyjny", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def oblicz_statystyki(lista):
    if not lista: return 0, 0
    srednia = statistics.mean(lista)
    if len(lista) > 1:
        n = len(lista)
        suma_vv = sum((x - srednia)**2 for x in lista)
        blad = math.sqrt(suma_vv / (n * (n - 1)))
    else:
        blad = 0
    return round(srednia, 2), round(blad, 2)

# --- PRZYGOTOWANIE DANYCH (pomiar.txt) ---
if not os.path.exists("pomiar.txt"):
    with open("pomiar.txt", "w") as f:
        f.write("100.0050 300.0070\n100.0040 300.0080\n100.0060 300.0090")

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("📐 Kalkulator Technik Pomiaru")
st.markdown("Obliczanie kolimacji i inklinacji na podstawie pliku `pomiar.txt`.")

# Sidebar - Panel boczny
with st.sidebar:
    st.header("Ustawienia")
    tryb = st.selectbox("Wybierz tryb:", [
        "1. Kolimacja (c)", 
        "2. Inklinacja (i)", 
        "3. Znana Kolimacja -> i", 
        "4. Znana Inklinacja -> c"
    ])
    
    z_grad = st.number_input("Odległość zenitowa z [g]:", value=100.0, step=0.1, format="%.1f")
    
    param_dodatkowy = 0.0
    if "3." in tryb:
        param_dodatkowy = st.number_input("Znana kolimacja c [cc]:", value=0.0)
    elif "4." in tryb:
        param_dodatkowy = st.number_input("Znana inklinacja i [cc]:", value=0.0)

# --- GŁÓWNA LOGIKA ---
try:
    # Wczytanie danych
    pomiary = []
    with open("pomiar.txt", "r") as f:
        for linia in f:
            pomiary.append([float(x) for x in linia.split()])
    
    # Obliczanie delt (odchyleń)
    deltas = [((abs(m[1] - m[0]) - 200) / 2) * 10000 for m in pomiary]
    
    # Przeliczenia kątowe
    z_rad = (z_grad * math.pi) / 200
    tan_z = math.tan(z_rad)
    sin_z = math.sin(z_rad)
    
    wyniki_czastkowe = []
    label = ""

    if "1." in tryb:
        label, wyniki_czastkowe = "Kolimacja (c)", deltas
    elif "2." in tryb:
        label, wyniki_czastkowe = "Inklinacja (i)", [d * tan_z for d in deltas]
    elif "3." in tryb:
        label, wyniki_czastkowe = "Inklinacja (i)", [(d - param_dodatkowy/sin_z) * tan_z for d in deltas]
    elif "4." in tryb:
        label, wyniki_czastkowe = "Kolimacja (c)", [(d - param_dodatkowy/tan_z) * sin_z for d in deltas]

    # Statystyki
    sr, blad = oblicz_statystyki(wyniki_czastkowe)

    # --- WYŚWIETLANIE WYNIKÓW ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label, f"{sr} cc")
    with col2:
        st.metric("Błąd średni", f"± {blad} cc")

    # Tabela z danymi
    st.subheader("Dane z pliku i odchylenia")
    st.table([{"KI": p[0], "KII": p[1], "Delta [cc]": round(d, 2)} for p, d in zip(pomiary, deltas)])

    # Zapis do pliku wynik.txt
    if st.button("Zapisz raport do wynik.txt"):
        with open("wynik.txt", "a") as f:
            f.write(f"Tryb: {label}, Wynik: {sr}, Blad: {blad}, z: {z_grad}g\n")
        st.success("Zapisano pomyślnie!")

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
    st.info("Sprawdź czy plik 'pomiar.txt' ma poprawny format (dwie liczby w linii).")
