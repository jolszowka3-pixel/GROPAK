import streamlit as st
import json
import os

# --- 1. GLOBALNA KONFIGURACJA (MUSI BYĆ PIERWSZA) ---
st.set_page_config(page_title="Gropak System", page_icon="🏢", layout="wide")

# --- 2. OBSŁUGA BAZY UŻYTKOWNIKÓW (JSON) ---
PLIK_USEROW = "uzytkownicy.json"

def wczytaj_uzytkownikow():
    if os.path.exists(PLIK_USEROW):
        with open(PLIK_USEROW, "r", encoding="utf-8") as f:
            return json.load(f)
    # Domyślne dane, jeśli plik nie istnieje
    return {"szef": {"haslo": "admin123", "rola": "admin"}}

# Inicjalizacja sesji
if 'zalogowany' not in st.session_state:
    st.session_state.update({'zalogowany': False, 'rola': 'brak', 'login': 'brak'})

UZYTKOWNICY = wczytaj_uzytkownikow()

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
# Zakładamy, że wszystkie pliki są w tym samym folderze co main_app.py
strona_glowna = st.Page("strona_glowna.py", title="Strona Publiczna", icon="🏠")
strona_kalkulator = st.Page("kalkulator.py", title="Kalkulator Wysyłek", icon="🧮")
strona_erp = st.Page("realizacja.py", title="Baza Realizacji (ERP)", icon="📊")
strona_wms = st.Page("pakownia.py", title="System Pakowania (WMS)", icon="📦")
strona_admin = st.Page("admin_panel.py", title="Panel Admina", icon="⚙️")

# --- 6. DYNAMICZNE BUDOWANIE MENU ---
# Strony dostępne dla każdego
strony_widoczne = [strona_glowna, strona_kalkulator]

rola = st.session_state['rola']

# Dodawanie stron na podstawie roli
if rola == "admin":
    strony_widoczne.extend([strona_erp, strona_wms, strona_admin])
elif rola == "erp_only":
    strony_widoczne.append(strona_erp)
elif rola == "wms_only":
    strony_widoczne.append(strona_wms)

# --- 7. URUCHOMIENIE NAWIGACJI ---
pg = st.navigation(strony_widoczne)
pg.run()