import streamlit as st
import json
from datetime import datetime
import uuid
import gspread
from google.oauth2 import service_account

# --- 1. OCHRONA DOSTĘPU (TYLKO DLA ADMINA) ---
if not st.session_state.get('zalogowany', False):
    st.warning("Zaloguj się w panelu bocznym na stronie głównej.")
    st.stop()

role_list = st.session_state.get('rola', [])
if isinstance(role_list, str): role_list = [role_list]

if "admin" not in role_list:
    st.error("Brak dostępu. Ta strona jest widoczna tylko dla Administratora.")
    st.stop()

# --- 2. POŁĄCZENIE Z BAZĄ DANYCH ---
GSHEET_NAME = "GROPAK_ERP_DB"

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["db_erp"]
        if "private_key" in creds_dict:
            creds_dict = dict(creds_dict)
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        scoped_credentials = credentials.with_scopes(["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(scoped_credentials)
    except Exception as e:
        st.error(f"🚨 Błąd połączenia z bazą: {e}")
        return None

def wczytaj_zadania():
    client = get_gsheet_client()
    if not client: return []
    try:
        sh = client.open(GSHEET_NAME)
        ws = sh.get_worksheet(0)
        val = ws.acell('A1').value
        if val:
            dane = json.loads(val)
            # Zwracamy tylko szufladkę "moje_zadania" (jeśli jej nie ma, zwracamy pustą listę)
            return dane.get("moje_zadania", [])
    except: pass
    return []

def zapisz_zadania(lista_zadan):
    client = get_gsheet_client()
    if client:
        try:
            sh = client.open(GSHEET_NAME)
            ws = sh.get_worksheet(0)
            val = ws.acell('A1').value
            if val:
                dane = json.loads(val)
            else:
                dane = {}
            # Podmieniamy tylko szufladkę "moje_zadania", reszty ERP nie ruszamy
            dane["moje_zadania"] = lista_zadan
            ws.update_acell('A1', json.dumps(dane))
        except: pass

# --- 3. LOGIKA APLIKACJI TO-DO ---
st.markdown("<h2 style='color: #2b3035;'>✅ Moja prywatna lista zadań</h2>", unsafe_allow_html=True)
st.markdown("Tutaj możesz dodawać szybkie notatki i zadania na dany dzień. Tylko Ty masz do nich dostęp.")
st.divider()

zadania = wczytaj_zadania()

# Formularz dodawania nowego zadania
with st.form("nowe_zadanie_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    nowe_zadanie = col1.text_input("Treść zadania:", placeholder="Wpisz co masz dziś do zrobienia...")
    if col2.form_submit_button("➕ Dodaj", use_container_width=True):
        if nowe_zadanie.strip():
            nowy_wpis = {
                "id": str(uuid.uuid4()), 
                "tresc": nowe_zadanie.strip(), 
                "data": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            zadania.insert(0, nowy_wpis) # Dodaje na samą górę listy
            zapisz_zadania(zadania)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Wyświetlanie listy zadań
if not zadania:
    st.info("Masz czystą kartę! Brak zadań na dziś. ☕")
else:
    for z in zadania:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"**{z['tresc']}**<br><span style='color:gray; font-size:12px;'>Dodano: {z['data']}</span>", unsafe_allow_html=True)
            if c2.button("ZROBIONE ✔️", key=f"zrobione_{z['id']}", use_container_width=True):
                # Usuwanie zadania z listy
                zadania = [zad for zad in zadania if zad['id'] != z['id']]
                zapisz_zadania(zadania)
                st.rerun()
