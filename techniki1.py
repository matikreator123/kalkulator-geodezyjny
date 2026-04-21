import streamlit as st
import math
import statistics

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

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("📐 Interaktywny Kalkulator Technik Pomiaru")
st.markdown("Wpisz odczyty KI i KII bezpośrednio do tabeli. Wyniki przeliczą się automatycznie.")

# Sidebar - Panel boczny
with st.sidebar:
    st.header("⚙️ Ustawienia")
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

# --- EDYTOWALNA TABELA (Wpisywanie na stronie) ---
st.subheader("📝 Dane pomiarowe")
default_data = [
    {"KI": 100.0050, "KII": 300.0070},
    {"KI": 100.0040, "KII": 300.0080},
    {"KI": 100.0060, "KII": 300.0090}
]

# Edytor tabeli - pozwala dodawać wiersze przyciskiem "+" pod tabelą
edited_data = st.data_editor(
    default_data, 
    num_rows="dynamic", 
    use_container_width=True,
    key="data_editor"
)

# --- GŁÓWNA LOGIKA ---
try:
    # Pobranie danych z edytora
    pomiary = [[row["KI"], row["KII"]] for row in edited_data if row["KI"] is not None and row["KII"] is not None]
    
    if pomiary:
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
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label, f"{sr} cc")
        with col2:
            st.metric("Błąd średni", f"± {blad} cc")

        # Wykres rozrzutu wyników
        st.bar_chart(wyniki_czastkowe)

        # --- POBIERANIE RAPORTU ---
        st.subheader("💾 Eksport wyników")
        
        # Przygotowanie tekstu raportu
        raport_text = f"RAPORT Z POMIARU\n"
        raport_text += f"-----------------\n"
        raport_text += f"Tryb obliczeń: {tryb}\n"
        raport_text += f"Odległość zenitowa z: {z_grad} g\n"
        raport_text += f"WYNIK ŚREDNI: {sr} cc\n"
        raport_text += f"BŁĄD ŚREDNI: ± {blad} cc\n\n"
        raport_text += f"Liczba pomiarów: {len(pomiary)}"

        st.download_button(
            label="Pobierz raport jako TXT",
            data=raport_text,
            file_name="wyniki_geodezja.txt",
            mime="text/plain"
        )
    else:
        st.info("Tabela jest pusta. Wpisz dane, aby zobaczyć wyniki.")

except Exception as e:
    st.error(f"Wystąpił błąd podczas obliczeń: {e}")
