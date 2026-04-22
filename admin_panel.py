import streamlit as st
import json
import os

# --- KONFIGURACJA PLIKU ---
PLIK_USEROW = "uzytkownicy.json"

def wczytaj_uzytkownikow():
    if os.path.exists(PLIK_USEROW):
        with open(PLIK_USEROW, "r", encoding="utf-8") as f:
            return json.load(f)
    # Jeśli pliku nie ma, zwracamy domyślnego szefa
    return {"szef": {"haslo": "admin123", "rola": "admin"}}

def zapisz_uzytkownikow(dane):
    with open(PLIK_USEROW, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4, ensure_ascii=False)

# --- INTERFEJS ---
st.title("⚙️ Zarządzanie Użytkownikami")
st.write("Tutaj możesz dodawać i usuwać dostęp dla pracowników.")

userzy = wczytaj_uzytkownikow()

# --- FORMULARZ DODAWANIA ---
with st.container(border=True):
    st.subheader("➕ Dodaj nowego pracownika")
    col1, col2, col3 = st.columns(3)
    with col1:
        nowy_login = st.text_input("Login", key="new_login_input")
    with col2:
        nowe_haslo = st.text_input("Hasło", key="new_pass_input")
    with col3:
        nowa_rola = st.selectbox("Uprawnienia", ["admin", "erp_only", "wms_only"], key="new_role_select")
    
    if st.button("ZAPISZ I DODAJ", type="primary", use_container_width=True):
        if nowy_login and nowe_haslo:
            # Dodajemy do słownika
            userzy[nowy_login] = {"haslo": nowe_haslo, "rola": nowa_rola}
            zapisz_uzytkownikow(userzy)
            st.success(f"Użytkownik {nowy_login} został dodany!")
            st.rerun()
        else:
            st.warning("Uzupełnij login i hasło!")

st.divider()

# --- LISTA UŻYTKOWNIKÓW ---
st.subheader("👥 Aktualna lista dostępu")

# Nagłówki tabeli
h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
h1.write("**Login**")
h2.write("**Rola**")
h3.write("**Hasło**")
h4.write("**Usuń**")

# Wyświetlanie każdego użytkownika
for u_login, info in list(userzy.items()):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    c1.write(u_login)
    c2.code(info['rola'])
    c3.write("********" if u_login != st.session_state.get('login') else info['haslo'])
    
    # Przycisk usuwania (nie pozwalamy usunąć samego siebie)
    if u_login != st.session_state.get('login'):
        if c4.button("🗑️", key=f"del_{u_login}"):
            del userzy[u_login]
            zapisz_uzytkownikow(userzy)
            st.rerun()
    else:
        c4.write("⭐ Ty")

st.info("""
**Wyjaśnienie uprawnień:**
- **admin**: Pełny dostęp do wszystkiego.
- **erp_only**: Tylko Baza Realizacji (ERP).
- **wms_only**: Tylko System Pakowania (WMS).
""")