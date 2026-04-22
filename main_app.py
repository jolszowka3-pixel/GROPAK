import streamlit as st
import os

# --- 1. GLOBALNA KONFIGURACJA (MUSI BYĆ PIERWSZA) ---
st.set_page_config(page_title="Gropak System", page_icon="🏢", layout="wide")

# --- 2. BAZA UŻYTKOWNIKÓW (HARDCODED) ---
# Tutaj zarządzasz dostępem. Dodaj nowych pracowników według wzoru poniżej.
UZYTKOWNICY = {
    "szef": {
        "haslo": "admin123", 
        "rola": "admin"
    },
    "kierownik": {
        "haslo": "erp2026", 
        "rola": "erp_only"
    },
    "magazynier": {
        "haslo": "paka777", 
        "rola": "wms_only"
    }
}

# Inicjalizacja sesji
if 'zalogowany' not in st.session_state:
    st.session_state.update({'zalogowany': False, 'rola': 'brak', 'login': 'brak'})

# --- 3. GLOBALNE LOGO NA PASKU BOCZNYM ---
logo_path = "logo.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.title("🏢 GROPAK")
st.sidebar.markdown("---")

# --- 4. SYSTEM LOGOWANIA W PASKU BOCZNYM ---
with st.sidebar:
    if not st.session_state['zalogowany']:
        st.markdown("### 🔒 Zaloguj się")
        login_input = st.text_input("Login")
        haslo_input = st.text_input("Hasło", type="password")
        
        if st.button("Zaloguj", use_container_width=True):
            if login_input in UZYTKOWNICY and str(UZYTKOWNICY[login_input]["haslo"]) == haslo_input:
                st.session_state.update({
                    'zalogowany': True, 
                    'rola': UZYTKOWNICY[login_input]["rola"], 
                    'login': login_input
                })
                st.success("Zalogowano!")
                st.rerun()
            else:
                st.error("Błędne dane!")
    else:
        st.success(f"👤 Zalogowany: **{st.session_state['login']}**")
        st.caption(f"Uprawnienia: {st.session_state['rola']}")
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.update({'zalogowany': False, 'rola': 'brak', 'login': 'brak'})
            st.rerun()
    st.markdown("---")

# --- 5. DEFINICJE STRON ---
# Pliki muszą znajdować się w tym samym folderze co main_app.py na GitHubie
strona_glowna = st.Page("strona_glowna.py", title="Strona Publiczna", icon="🏠")
strona_kalkulator = st.Page("kalkulator.py", title="Kalkulator Wysyłek", icon="🧮")
strona_erp = st.Page("realizacja.py", title="Baza Realizacji (ERP)", icon="📊")
strona_wms = st.Page("pakownia.py", title="System Pakowania (WMS)", icon="📦")

# --- 6. DYNAMICZNE BUDOWANIE MENU ---
strony_widoczne = [strona_glowna, strona_kalkulator]

rola = st.session_state['rola']

if rola == "admin":
    # Admin widzi wszystko (bez Panelu Admina, bo zarządzasz kodem)
    strony_widoczne.extend([strona_erp, strona_wms])
elif rola == "erp_only":
    strony_widoczne.append(strona_erp)
elif rola == "wms_only":
    strony_widoczne.append(strona_wms)

# --- 7. URUCHOMIENIE NAWIGACJI ---
pg = st.navigation(strony_widoczne)
pg.run()
