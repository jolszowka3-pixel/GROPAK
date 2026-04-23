import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import gspread

# --- 1. STYLIZACJA (CSS) ZACHOWANA ZE STAREGO KODU ---
st.markdown("""
<style>
/* Wspólne ustawienia przycisków */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button { 
    width: 100%; border-radius: 6px; min-height: 32px !important; height: 32px !important; 
    font-size: 12px; font-weight: 600; transition: all 0.2s ease-in-out;
    border: 1px solid #ced4da; padding: 0 10px; line-height: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* PRZYCISKI KOLOROWE */
button:has(div p:contains("WYŚLIJ")), button:contains("WYŚLIJ"), button:has(div p:contains("OK")), button:contains("OK") {
    border: none !important; color: white !important; background-color: #28a745 !important;
}
button:has(div p:contains("ZROBIONE")), button:contains("ZROBIONE"), button:has(div p:contains("GOTOWE")), button:contains("GOTOWE") {
    border: none !important; color: white !important; background-color: #28a745 !important;
}
button:has(div p:contains("X")), button:contains("X") {
    border: none !important; color: white !important; background-color: #dc3545 !important; padding: 0 !important;
}
button:has(div p:contains("Zapisz")), button:contains("Zapisz") {
    border: none !important; color: white !important; background-color: #007bff !important;
}
button:has(div p:contains("RESETUJ")), button:contains("RESETUJ") {
    border: none !important; color: white !important; background-color: #dc3545 !important; font-weight: 900 !important;
}

.main .block-container { padding-top: 2rem; }
.section-header { background-color: #f8f9fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 12px; margin-top: 25px; font-weight: 700; color: #212529; text-transform: uppercase; border-left: 5px solid #2b3035; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* STYL ŻÓŁTEJ KARTKI (POST-IT) */
.note-card { 
    background-color: #ffff88; 
    padding: 20px; 
    margin-bottom: 20px; 
    box-shadow: 5px 5px 10px rgba(0,0,0,0.15); 
    border-radius: 2px; 
    min-height: 120px;
    color: #333;
    border-left: 2px solid #e6e600;
}
.note-meta { font-size: 10px; color: #888; margin-top: 15px; border-top: 1px dashed #d1d13a; padding-top: 5px; }

/* KALENDARZ */
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) { gap: 0px !important; }
[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)):not(:has(> div:nth-child(8))) > div {
    flex: 0 0 calc(100% / 7) !important; min-width: calc(100% / 7) !important; max-width: calc(100% / 7) !important; padding: 0 3px !important;
}
.day-header { text-align: center; border-bottom: 2px solid #343a40; margin-bottom: 8px; padding-bottom: 4px; }
.day-name { font-weight: 700; font-size: 12px; color: #495057; text-transform: uppercase; }
.day-date { font-size: 11px; color: #868e96; }

.cal-entry-out, .cal-entry-ready, .cal-entry-in, .cal-entry-task, .cal-entry-return { font-size: 10px; padding: 4px 6px; margin-bottom: 2px; border-radius: 3px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; cursor: help; }
.cal-entry-out { background: #e7f5ff; color: #0056b3; border-left: 3px solid #0056b3; }
.cal-entry-ready { background: #d4edda; color: #155724; border-left: 3px solid #28a745; }
.cal-entry-return { background: #f3e5f5; color: #7b1fa2; border: 1px solid #7b1fa2; }
.cal-entry-in { background: #f3f9f1; color: #28a745; border-left: 3px solid #28a745; }
.cal-entry-task { background: #fff4e6; color: #d9480f; border-left: 3px solid #d9480f; }

/* TABELE REALIZACJI */
.table-group-header { background-color: #e9ecef; color: #212529; padding: 6px 12px; font-weight: 700; font-size: 12px; border-radius: 4px; margin: 15px 0 8px 0; border-left: 4px solid #007bff; }
.badge-status-prod { background-color: #ffc107; color: #212529; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-ready { background-color: #28a745; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.badge-status-return { background-color: #7b1fa2; color: white; padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: bold; margin-left: 5px; display: inline-block;}
.readonly-text { font-size: 13px; white-space: pre-wrap; color: #495057; line-height: 1.4; padding: 5px; background: #fdfdfd; border-radius: 4px; border: 1px solid #eee; }
.client-hover { cursor: help; border-bottom: 1px dotted #999; }
div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. ZMIENNE UPRAWNIEŃ I ZARZĄDZANIE SESJĄ (Z NOWEGO PROJEKTU) ---
rola = st.session_state.get('rola', 'wgląd')
login = st.session_state.get('login', 'Nieznany')
st.session_state.user = login

is_admin = (rola == "admin")
can_edit = (rola in ["admin", "erp_only", "edycja"])
is_readonly = not can_edit

# --- 3. LOGIKA BAZY DANYCH (NOWY FORMAT POŁĄCZENIA) ---
OPCJE_TRANSPORTU = ["Brak", "Auto 1", "Auto 2", "Transport zewnętrzny", "Odbiór osobisty", "Kurier"]
SHEET_KEY = "1XgDOic0ditZBODS9Gb99wQBcMGRAJnp7TRpYqslJgLE"

@st.cache_resource
def get_gsheet_client():
    try:
        creds_dict = st.secrets["connections"]["gsheets_1"]
        client = gspread.service_account_from_dict(creds_dict)
        return client
    except Exception as e: 
        st.error(f"Błąd połączenia z bazą: {e}")
        return None

def posortuj_dane(dane):
    def sort_key(item):
        pilne = 0 if item.get('pilne') else 1 
        t_val = str(item.get('auto', 'Brak'))
        t_score = OPCJE_TRANSPORTU.index(t_val) if t_val in OPCJE_TRANSPORTU else 99
        k_score = int(item.get('kurs', 1))
        status_score = 1 if item.get('status') == 'Gotowe' else 0 
        try:
            termin = str(item.get('termin', '')).strip()
            if not termin: return (2, 9999, 99, 99, 99, 99, 99, pilne)
            parts = termin.split('.')
            return (0, 2026, int(parts[1]), int(parts[0]), t_score, k_score, status_score, pilne)
        except: return (1, 9999, 99, 99, 99, 99, 99, pilne)
    for k in ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]:
        if k in dane: dane[k].sort(key=sort_key)
    return dane

def auto_przesun_zadania(dane):
    dzis = datetime.now()
    dzis_str = dzis.strftime("%d.%m")
    zmiana = False
    kategorie = ["w_realizacji", "przyjecia", "dyspozycje", "odbiory"]
    
    for kat in kategorie:
        for item in dane.get(kat, []):
            termin_str = str(item.get("termin", "")).strip()
            if termin_str:
                try:
                    parts = termin_str.split('.')
                    d, m = int(parts[0]), int(parts[1])
                    data_item = datetime(2026, m, d)
                    if data_item.date() < dzis.date():
                        item["termin"] = dzis_str
                        zmiana = True
                except: pass
    return dane, zmiana

def wczytaj_dane():
    default_dane = {"w_realizacji": [], "zrealizowane": [], "przyjecia": [], "przyjecia_historia": [], "dyspozycje": [], "dyspozycje_historia": [], "odbiory": [], "odbiory_historia": [], "tablica": []}
    client = get_gsheet_client()
    if not client: return default_dane
    try:
        sh = client.open_by_key(SHEET_KEY)
        ws = sh.get_worksheet(0)
        val = ws.acell('A1').value
        if val:
            d = json.loads(val)
            for k, v in default_dane.items():
                if k not in d: d[k] = v
            d, czy_byla_zmiana = auto_przesun_zadania(d)
            if czy_byla_zmiana: zapisz_dane(d)
            return posortuj_dane(d)
    except: pass
    return default_dane

def zapisz_dane(dane_do_zapisu):
    client = get_gsheet_client()
    if client:
        try:
            sh = client.open_by_key(SHEET_KEY)
            ws = sh.get_worksheet(0)
            ws.update_acell('A1', json.dumps(posortuj_dane(dane_do_zapisu)))
        except: pass

dane = wczytaj_dane()

# --- 4. FUNKCJE POMOCNICZE (DRUK) ---
def generuj_html_do_druku(z):
    auto_val = z.get('auto', 'Brak'); k_val = z.get('kurs', 1); transport_str = f"{auto_val} / Kurs nr {k_val}" if auto_val in ["Auto 1", "Auto 2"] else auto_val
    return f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:30px;}} .card{{border:5px solid black;padding:30px;}} h1{{text-align:center;border-bottom:3px solid black;}} .row{{display:flex;justify-content:space-between;margin-top:20px;font-size:20px;}} .box{{border:1px solid #666;padding:15px;margin-top:20px;min-height:300px;font-size:20px;white-space:pre-wrap;line-height:1.4;}}</style></head><body onload="window.print()"><div class="card"><h1>Karta Zlecenia: {z.get('klient')}</h1><div class="row"><div><b>Termin:</b> {z.get('termin')}</div><div><b>Transport:</b> {transport_str}</div></div><p><b>PRODUKTY / SZCZEGÓŁY:</b></p><div class="box">{z.get('szczegoly')}</div><div style="margin-top:50px;text-align:right;">Podpis: __________________________</div></div></body></html>"""

def generuj_rozpiske_zbiorcza(data_cel, lista_zlecen, lista_odbiorow):
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8"><style>body{{font-family:sans-serif;padding:20px;}} .h1{{text-align:center;border-bottom:4px solid #000;}} .transport-title{{background:#f8f9fa;padding:10px;border:2px solid #000;margin:10px 0;}} table{{width:100%;border-collapse:collapse;}} th, td{{border:1px solid #000;padding:8px;text-align:left;}} .details{{white-space:pre-wrap;}}</style></head><body onload="window.print()"><div class="h1"><h1>PLAN TRANSPORTU - {data_cel}</h1></div>"""
    z_dnia = [z for z in lista_zlecen if z.get('termin') == data_cel]; o_dnia = [o for o in lista_odbiorow if o.get('termin') == data_cel]
    grupy = {}
    for z in z_dnia:
        k = (str(z.get('auto', 'Brak')), str(z.get('kurs', 1)))
        if k not in grupy: grupy[k] = {"prod": [], "odb": []}
        grupy[k]["prod"].append(z)
    for o in o_dnia:
        k = (str(o.get('auto', 'Brak')), str(o.get('kurs', 1)))
        if k not in grupy: grupy[k] = {"prod": [], "odb": []}
        grupy[k]["odb"].append(o)
    if not grupy: html += f"<h2 style='text-align:center;'>Brak zadań na dzień {data_cel}.</h2>"
    else:
        for (tr, kr), content in grupy.items():
            html += f"<div class='transport-title'>🚚 {tr} / KURS {kr}</div><table><tr><th style='width:30%'>KLIENT / DOSTAWCA</th><th>PRODUKTY / UWAGI</th></tr>"
            for it in content["prod"]: html += f"<tr><td><b>{it.get('klient')}</b></td><td class='details'>{it.get('szczegoly')}</td></tr>"
            for it in content["odb"]: html += f"<tr><td><b>🔄 ODBIÓR: {it.get('miejsce')}</b></td><td class='details'>{it.get('towar')}</td></tr>"
            html += "</table>"
    html += "</body></html>"; return html

# --- 5. PANEL BOCZNY ---
with st.sidebar:
    st.markdown("### PANEL STEROWANIA ERP")
    tryb_mobilny = st.toggle("📱 Tryb Mobilny", value=False, key="toggle_mobile_erp")
    st.divider()
    st.write(f"Zalogowany: **{st.session_state.user}**")
    st.divider()

    if can_edit:
        st.markdown('<div class="sidebar-header">➕ NOWY WPIS</div>', unsafe_allow_html=True)
        typ = st.selectbox("Rodzaj:", ["Produkcja", "Odbiór (Powrót)", "Dostawa (PZ)", "Dyspozycja"], key="sb_rodzaj_wpisu")
        with st.form("f_add"):
            kl = st.text_input("Nazwa/Klient")
            tm = st.text_input("Termin (np. 22.04)")
            sz = st.text_area("Szczegóły")
            au = st.selectbox("Auto", OPCJE_TRANSPORTU)
            kr = st.selectbox("Kurs", [1,2,3,4,5])
            pi = st.checkbox("PILNE")
            if st.form_submit_button("Zapisz"):
                key_map = {"Produkcja": "w_realizacji", "Odbiór (Powrót)": "odbiory", "Dostawa (PZ)": "przyjecia", "Dyspozycja": "dyspozycje"}
                item = {"klient": kl, "miejsce": kl, "dostawca": kl, "tytul": kl, "termin": tm, "szczegoly": sz, "towar": sz, "opis": sz, "auto": au, "kurs": int(kr), "pilne": pi, "status": "W produkcji", "data_p": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user}
                dane[key_map[typ]].append(item); zapisz_dane(dane); st.rerun()
    st.divider()
    data_druk = st.text_input("Podaj datę do druku (np. 22.04):", value=datetime.now().strftime("%d.%m"), key="input_print_date")
    st.download_button("📥 Pobierz Rozpiskę Dnia", data=generuj_rozpiske_zbiorcza(data_druk, dane["w_realizacji"], dane["odbiory"]), file_name=f"Plan_{data_druk}.html", mime="text/html", key="btn_download_plan")

# --- 6. TERMINARZ TYGODNIOWY ---
st.markdown('<div class="section-header">Terminarz Tygodniowy</div>', unsafe_allow_html=True)
if "wo" not in st.session_state: st.session_state.wo = 0
cn1, _, cn3 = st.columns([1,4,1])
if cn1.button("← Poprzedni", key="btn_prev_week"): st.session_state.wo -= 7; st.rerun()
if cn3.button("Następny →", key="btn_next_week"): st.session_state.wo += 7; st.rerun()
start = datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=st.session_state.wo)

if not tryb_mobilny:
    cols = st.columns(7)
    for i in range(7):
        day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
        with cols[i]:
            st.markdown(f"<div class='day-header'><div class='day-name'>{['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]}</div><div class='day-date'>{d_str}</div></div>", unsafe_allow_html=True)
            day_tasks = [x for x in (dane["w_realizacji"] + dane["odbiory"]) if x.get('termin') == d_str]
            grupy_aut = {}
            for item in day_tasks:
                a_name = str(item.get('auto', 'Brak')).strip()
                k_num = str(item.get('kurs', '1')).strip()
                g_key = f"{a_name}_K{k_num}"
                if g_key not in grupy_aut: grupy_aut[g_key] = {'auto': a_name, 'kurs': k_num, 'tasks': []}
                grupy_aut[g_key]['tasks'].append(item)
            
            for g_id in sorted(grupy_aut.keys()):
                g = grupy_aut[g_id]
                all_done = all(t.get('status') == 'Gotowe' for t in g['tasks'])
                cl = "cal-entry-ready" if all_done else ("cal-entry-return" if g['auto'] == "Odbiór osobisty" else "cal-entry-out")
                names_str = ", ".join([str(t.get('klient') or t.get('miejsce')) for t in g['tasks']])
                display_label = f"{g['auto']}/K{g['kurs']}: {names_str}"
                tt = f"{g['auto']} / KURS {g['kurs']}"
                for t in g['tasks']: 
                    desc = str(t.get('szczegoly') or t.get('towar')).replace("\n", " ").replace("\r", "")
                    tt += f"&#10;• {t.get('klient') or t.get('miejsce')}: {desc}"
                tooltip_html = tt.replace('"', "&quot;").replace("'", "&apos;")
                st.markdown(f"<div class='{cl}' title='{tooltip_html}'>{display_label}</div>", unsafe_allow_html=True)
            for p in dane["przyjecia"]:
                if p.get('termin') == d_str: st.markdown(f"<div class='cal-entry-in' title='{str(p.get('towar')).replace('\\n',' ')}'>P: {p.get('dostawca')}</div>", unsafe_allow_html=True)
            for d in dane["dyspozycje"]:
                if d.get('termin') == d_str: st.markdown(f"<div class='cal-entry-task' title='{str(d.get('opis')).replace('\\n',' ')}'>D: {d.get('tytul')}</div>", unsafe_allow_html=True)
else:
    for i in range(7):
        day = start + timedelta(days=i); d_str = day.strftime('%d.%m')
        tasks = [z for z in (dane["w_realizacji"] + dane["odbiory"]) if z.get('termin') == d_str]
        if tasks:
            with st.expander(f"📅 {['Pon','Wt','Śr','Czw','Pt','Sob','Nd'][i]} ({d_str})"):
                for t in tasks: st.write(f"📦 **{t.get('klient') or t.get('miejsce')}** - {t.get('auto')} (K{t.get('kurs')})")

# --- 7. TABELE REALIZACJI I TABLICA OGŁOSZEŃ ---
st.markdown('<div class="section-header">Listy Realizacji</div>', unsafe_allow_html=True)
search = st.text_input("🔍 Szukaj we wszystkich wpisach...", "", key="search_erp_global").lower()
tabs = st.tabs(["🏭 Produkcja", "🔄 Odbiory", "🚚 Przyjęcia PZ", "📋 Dyspozycje", "📌 Tablica Ogłoszeń"])

def renderuj_tabele_ujednolicona(lista_zrodlowa, klucz_nazwa, klucz_szczegoly, klucz_id, typ_sekcji):
    if not lista_zrodlowa: 
        st.info("Brak aktywnych wpisów.")
        return
    last_date = None
    for i, item in enumerate(lista_zrodlowa):
        ma_termin = bool(str(item.get('termin','')).strip())
        if typ_sekcji == "produkcja" and not ma_termin: continue
        if typ_sekcji == "plan" and ma_termin: continue
        if search and search not in str(item).lower(): continue
        curr_date = item.get('termin', '---')
        if curr_date != last_date and typ_sekcji != "plan":
            st.markdown(f"<div class='table-group-header'>📅 TERMIN: {curr_date}</div>", unsafe_allow_html=True)
            last_date = curr_date
        status = item.get('status','W toku')
        badge = '<span class="badge-status-ready">✅ GOTOWE</span>' if status=='Gotowe' else '<span class="badge-status-prod">⏳ W TOKU</span>'
        if klucz_id == "odb": badge = '<span class="badge-status-return">🔄 ODBIÓR</span>'
        szczeg_safe = str(item.get(klucz_szczegoly, "Brak opisu")).replace('"', "&quot;").replace("'", "&apos;").replace("\n", " ")
        u_id = f"{klucz_id}_{i}_{item.get('data_p','')}".replace(':','').replace(' ','_').replace('.','_')
        st.markdown("<div style='padding:10px 0; border-bottom:1px solid #eee;'>", unsafe_allow_html=True)
        
        if not tryb_mobilny:
            c = st.columns([2.0, 1.2, 5.0, 1.2, 0.6])
            c[0].markdown(f"<span class='client-hover' title='{szczeg_safe}'>**{item.get(klucz_nazwa)}**</span><br>{badge}", unsafe_allow_html=True)
            c[1].write(item.get('termin', '---'))
            if is_readonly: 
                c[2].markdown(f"<div class='readonly-text'>{item.get(klucz_szczegoly,'-')}</div>", unsafe_allow_html=True)
            else:
                with c[2].popover("Edytuj"):
                    if klucz_id == "prod": st.download_button("🖨️ Karta A4", generuj_html_do_druku(item), f"Karta_{u_id}.html", "text/html", key=f"dl_{u_id}")
                    new_t = st.text_input("Termin", item.get('termin'), key=f"t_{u_id}")
                    new_s = st.text_area("Szczegóły", item.get(klucz_szczegoly), key=f"s_{u_id}")
                    new_au = st.selectbox("Auto", OPCJE_TRANSPORTU, OPCJE_TRANSPORTU.index(item.get('auto','Brak')), key=f"au_{u_id}")
                    new_kr = st.selectbox("Kurs", [1,2,3,4,5], int(item.get('kurs',1))-1, key=f"kr_{u_id}")
                    if st.button("Zapisz", key=f"sv_{u_id}"): 
                        item.update({"termin":new_t, klucz_szczegoly:new_s, "auto":new_au, "kurs":int(new_kr)})
                        zapisz_dane(dane)
                        st.rerun()
            if not is_readonly:
                if status != "Gotowe" and c[3].button("ZROBIONE" if klucz_id != "pz" else "OK", key=f"ok_{u_id}"): 
                    item['status'] = "Gotowe"; zapisz_dane(dane); st.rerun()
                elif status == "Gotowe" and c[3].button("WYŚLIJ", key=f"send_{u_id}"):
                    h_map = {"prod":"zrealizowane", "odb":"odbiory_historia", "pz":"przyjecia_historia", "dysp":"dyspozycje_historia"}
                    dane[h_map.get(klucz_id)].append(lista_zrodlowa.pop(i)); zapisz_dane(dane); st.rerun()
                if c[4].button("X", key=f"del_{u_id}"): 
                    lista_zrodlowa.pop(i); zapisz_dane(dane); st.rerun()
        else:
            c1, c2 = st.columns([3.5, 1.5])
            c1.markdown(f"**{item.get(klucz_nazwa)}**<br>{badge}", unsafe_allow_html=True)
            with c2.popover("Akcje"):
                if not is_readonly:
                    if status != "Gotowe" and st.button("ZROBIONE", key=f"mok_{u_id}"): 
                        item['status']="Gotowe"; zapisz_dane(dane); st.rerun()
                    if status == "Gotowe" and st.button("WYŚLIJ", key=f"msnd_{u_id}"):
                        h_map = {"prod":"zrealizowane", "odb":"odbiory_historia", "pz":"przyjecia_historia", "dysp":"dyspozycje_historia"}
                        dane[h_map.get(klucz_id)].append(lista_zrodlowa.pop(i)); zapisz_dane(dane); st.rerun()
                    if st.button("USUŃ", key=f"mdel_{u_id}"): 
                        lista_zrodlowa.pop(i); zapisz_dane(dane); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with tabs[0]:
    s1, s2, s3 = st.tabs(["Aktywne", "📂 Do zaplanowania", "Historia"])
    with s1: renderuj_tabele_ujednolicona(dane["w_realizacji"], "klient", "szczegoly", "prod", "produkcja")
    with s2: renderuj_tabele_ujednolicona(dane["w_realizacji"], "klient", "szczegoly", "prod", "plan")
    with s3: st.dataframe(dane["zrealizowane"][::-1], use_container_width=True)
with tabs[1]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: renderuj_tabele_ujednolicona(dane["odbiory"], "miejsce", "towar", "odb", "active")
    with s2: st.dataframe(dane["odbiory_historia"][::-1], use_container_width=True)
with tabs[2]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: renderuj_tabele_ujednolicona(dane["przyjecia"], "dostawca", "towar", "pz", "active")
    with s2: st.dataframe(dane["przyjecia_historia"][::-1], use_container_width=True)
with tabs[3]:
    s1, s2 = st.tabs(["Aktywne", "Historia"])
    with s1: renderuj_tabele_ujednolicona(dane["dyspozycje"], "tytul", "opis", "dysp", "active")
    with s2: st.dataframe(dane["dyspozycje_historia"][::-1], use_container_width=True)

# --- TABLICA OGŁOSZEŃ ---
with tabs[4]:
    st.markdown('<div class="section-header">📌 Tablica Ogłoszeń</div>', unsafe_allow_html=True)
    if can_edit:
        with st.form("bottom_note", clear_on_submit=True):
            nowa_tresc = st.text_area("Dodaj ogłoszenie:")
            if st.form_submit_button("➕ Opublikuj"):
                if nowa_tresc: 
                    dane["tablica"].append({"tresc": nowa_tresc, "data": datetime.now().strftime("%d.%m %H:%M"), "autor": st.session_state.user})
                    zapisz_dane(dane); st.rerun()
    
    if not dane["tablica"]:
        st.info("Brak aktywnych ogłoszeń.")
    else:
        nc = st.columns(3)
        for i, note in enumerate(reversed(dane["tablica"])):
            ridx = len(dane["tablica"])-1-i
            with nc[i % 3]:
                st.markdown(f"<div class='note-card'>{note['tresc']}<div class='note-meta'>{note['data']} | {note['autor']}</div></div>", unsafe_allow_html=True)
                if can_edit and st.button("Usuń", key=f"dn_{ridx}"):
                    dane["tablica"].pop(ridx); zapisz_dane(dane); st.rerun()
