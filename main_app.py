import streamlit as st
import os

# --- 1. GLOBALNA KONFIGURACJA (MUSI BYĆ PIERWSZA) ---
st.set_page_config(page_title="Gropak System", page_icon="🏢", layout="wide")

# --- 2. BAZA UŻYTKOWNIKÓW (HARDCODED Z LISTĄ RÓL) ---
UZYTKOWNICY = {
    "admin": {
        "haslo": "admin123", 
        "rola": ["admin"] # Admin i tak widzi wszystko
    },
    "michal.bryl": {
        "haslo": "gropak2026", 
        "rola": ["erp_only", "wms_szef"] # Marek widzi ERP i WMS, ale nie widzi Panelu Admina
    },
    "michal.bodura": {
        "haslo": "gropak2026", 
        "rola": ["erp_only"] # Widzi tylko pakownię
    },
    "bartek.rudnik": {
        "haslo": "gropak2026", 
        "rola": ["admin"] # Admin i tak widzi wszystko
    },
    "rafal.skazynski": {
        "haslo": "gropak2026", 
        "rola": ["wms_szef"] # Marek widzi ERP i WMS, ale nie widzi Panelu Admina
    },
    "wysylka": {
        "haslo": "gropak2026", 
        "rola": ["wms_only"] # Widzi tylko pakownię
    }
} # <--- Ten nawias zamykający był przyczyną błędu!

# Inicjalizacja sesji
if 'zalogowany' not in st.session_state:
    st.session_state.update({'zalogowany': False, 'rola': [], 'login': 'brak'})

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
        
        # Zamykamy logowanie w formularzu, dzięki czemu działa klawisz ENTER
        with st.form("formularz_logowania"):
            login_input = st.text_input("Login")
            haslo_input = st.text_input("Hasło", type="password")
            
            # Zmieniamy st.button na st.form_submit_button
            if st.form_submit_button("Zaloguj", use_container_width=True):
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
        
        role_tekst = ", ".join(st.session_state['rola']) if isinstance(st.session_state['rola'], list) else st.session_state['rola']
        st.caption(f"Uprawnienia: {role_tekst}")
        
        if st.button("🚪 Wyloguj", use_container_width=True):
            st.session_state.update({'zalogowany': False, 'rola': [], 'login': 'brak'})
            st.rerun()
    st.markdown("---")

# --- 5. DEFINICJE STRON ---
strona_glowna = st.Page("strona_glowna.py", title="Strona Publiczna", icon="🏠")
strona_kalkulator = st.Page("kalkulator.py", title="Kalkulator Wysyłek", icon="🧮")
strona_erp = st.Page("realizacja.py", title="Baza Realizacji (ERP)", icon="📊")
strona_wms = st.Page("pakownia.py", title="System Pakowania (WMS)", icon="📦")

# --- 6. DYNAMICZNE BUDOWANIE MENU (MULTIDOSTĘP) ---
strony_widoczne = [strona_glowna, strona_kalkulator]

role_uzytkownika = st.session_state.get('rola', [])
if isinstance(role_uzytkownika, str):
    role_uzytkownika = [role_uzytkownika]

if "admin" in role_uzytkownika:
    strony_widoczne.extend([strona_erp, strona_wms])
else:
    if "erp_only" in role_uzytkownika:
        if strona_erp not in strony_widoczne:
            strony_widoczne.append(strona_erp)
            
    # ZMIANA: Zakładkę pakowni widzi "wms_only" ORAZ "wms_szef"
    if "wms_only" in role_uzytkownika or "wms_szef" in role_uzytkownika:
        if strona_wms not in strony_widoczne:
            strony_widoczne.append(strona_wms)

# --- 7. URUCHOMIENIE NAWIGACJI ---
pg = st.navigation(strony_widoczne)
pg.run()
