import streamlit as st
import tempfile
import os
from datetime import datetime

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 1. Konfiguracja strony
st.set_page_config(
    page_title="USGVet Scans - Raporty", 
    layout="wide", 
    page_icon="🩺",
    initial_sidebar_state="expanded"
)

# === INICJALIZACJA SESSION STATE ===
if "editable_report_area" not in st.session_state: st.session_state["editable_report_area"] = ""
if "reports_history" not in st.session_state: st.session_state["reports_history"] = []
if "plec_pacjenta" not in st.session_state: st.session_state["plec_pacjenta"] = "Suka (kastrowana / kikut)"
if "last_mode2_hash" not in st.session_state: st.session_state["last_mode2_hash"] = ""
if "last_mode3_hash" not in st.session_state: st.session_state["last_mode3_hash"] = ""
if "processed_audio_size" not in st.session_state: st.session_state["processed_audio_size"] = 0

# === ODCZYT KLUCZA Z SECRETS ===
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip().strip('"').strip("'")

client = None
if HAS_OPENAI and api_key:
    try: client = OpenAI(api_key=api_key)
    except Exception: client = None

# ==========================================
# 2. ZAAWANSOWANA STYLIZACJA CSS
# ==========================================
st.markdown("""
    <style>
    /* Definiowanie kolorów marki */
    :root {
        --color-pink: #f49ac1;
        --color-dark-teal: #135c7e;
        --color-btn-teal: #237a9f;
        --color-bg: #f9fbfb;
    }

    /* Zmiana tła aplikacji na delikatniutki szaro-niebieski ze strony */
    .stApp {
        background-color: var(--color-bg);
    }

    /* NAGŁÓWEK STYLIZOWANY NA LOGO ZDJĘCIA */
    .custom-header {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid var(--color-pink);
    }
    .custom-header .usg { color: var(--color-pink); font-weight: 900; font-size: 2.8rem; font-family: 'Arial', sans-serif;}
    .custom-header .scans { color: var(--color-dark-teal); font-weight: 900; font-size: 2.8rem; font-family: 'Arial', sans-serif;}
    .custom-header p { color: #666; font-size: 1.1rem; margin-top: 5px; font-weight: 500;}

    /* PRZYCISKI - Stylizacja zaokrąglona jak "Zaloguj" */
    div.stButton > button {
        background-color: var(--color-btn-teal);
        color: white;
        border-radius: 25px !important;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: var(--color-dark-teal);
        box-shadow: 0 4px 10px rgba(19, 92, 126, 0.3);
        color: white;
    }
    
    /* Zmiana przycisków w Sidebar na różowe dla odróżnienia akcji */
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: white;
        color: var(--color-pink);
        border: 1px solid var(--color-pink);
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background-color: var(--color-pink);
        color: white;
    }

    /* CHECKBOXY - Karty z białym tłem */
    .stCheckbox > label {
        background-color: white !important;
        padding: 12px 18px !important;
        border-radius: 10px !important;
        border: 1px solid #eef1f2 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }
    .stCheckbox > label:hover {
        border-color: var(--color-btn-teal) !important;
        box-shadow: 0 4px 8px rgba(35, 122, 159, 0.1) !important;
    }

    /* KARTY TRYBÓW PRACY - WYRÓWNANE DO TEJ SAMEJ WIELKOŚCI */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 15px;
        justify-content: center;
        background: transparent !important;
        width: 100%;
    }
    div[role="radiogroup"] > label {
        background-color: white !important;
        border: 2px solid #e0e6e8 !important;
        border-radius: 15px !important;
        padding: 15px 10px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        flex: 1 1 0px !important; /* Wymusza jednakową szerokość */
        min-height: 90px !important; /* Wymusza jednakową, stałą wysokość */
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 !important;
    }
    /* Ukrycie kropki z Radio */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important; 
    }
    /* Tekst na karcie */
    div[role="radiogroup"] > label p {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: var(--color-dark-teal) !important;
        margin: 0 !important;
        line-height: 1.3 !important;
    }
    /* Aktywna Karta (Wybrany Tryb) */
    div[role="radiogroup"] > label[data-checked="true"] {
        border-color: var(--color-pink) !important;
        background-color: #fffafb !important;
        box-shadow: 0 8px 16px rgba(244, 154, 193, 0.15) !important;
        transform: translateY(-3px);
    }
    
    /* Pola tekstowe i Selectbox */
    .stTextArea textarea, .stTextInput input, .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1px solid #dce4e6 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox > div > div:focus {
        border-color: var(--color-btn-teal) !important;
        box-shadow: 0 0 0 1px var(--color-btn-teal) !important;
    }
    </style>
""", unsafe_allow_html=True)

# GŁÓWNY NAGŁÓWEK (Naśladujący logo)
st.markdown("""
    <div class="custom-header">
        <span class="usg">USGVet</span> <span class="scans">Scans</span>
        <p>System Generowania Raportów Ultrasonograficznych</p>
    </div>
""", unsafe_allow_html=True)

# Funkcja pomocnicza do zapisywania w historii
def add_to_history(report_text):
    if report_text and report_text.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        snippet = report_text[:35].replace("\n", " ") + "..."
        entry = {"time": timestamp, "snippet": snippet, "text": report_text}
        st.session_state["reports_history"].insert(0, entry)
        st.session_state["reports_history"] = st.session_state["reports_history"][:10]

# GŁÓWNA FUNKCJA DOPASOWUJĄCA UKŁAD ROZRODCZY
def get_rodne_text(plec_wybor):
    p = str(plec_wybor).lower()
    if "niekastrowany" in p: return "Gruczoł krokowy niepowiększony, wielkości ok. ... cm x ... cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia."
    elif "samiec kastrowany" in p: return "Gruczoł krokowy obkurczony, hipoechogenny, bez zmian w budowie, typowy obraz pokastracyjny."
    elif "cała" in p: return "Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
    else: return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

# ==========================================
# SIDEBAR: USTAWIENIA GÓRNE 
# ==========================================
with st.sidebar:
    st.header("⚙️ Konfiguracja Pacjenta")
    plec = st.selectbox(
        "Wybierz płeć i stan fizjologiczny:",
        ["Suka (kastrowana / kikut)", "Suka (cała)", "Pies (samiec niekastrowany)", "Pies (samiec kastrowany)"],
        key="plec_pacjenta"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    dodaj_tarczyce = st.checkbox("Dodaj badanie tarczycy", value=False)

# ==========================================
# WYBÓR TRYBU PRACY 
# ==========================================
tryb = st.radio(
    "Wybierz tryb pracy:",
    [
        "🎙️ TRYB 1: Dyktowanie (AI)", 
        "📏 TRYB 2: Tabela Wymiarów", 
        "📝 TRYB 3: Wybór Zmian"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# TRYB 1: DYKTOWANIE Z PEŁNYM ŚCISŁYM SZABLONEM
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie (AI)":
    st.subheader("Wypowiedz obserwacje, AI stworzy gotowy raport")
    st.info("💡 Nagraj notatkę. AI wstawi wymiary i patologie do pełnych szablonów medycznych.")

    audio_recorded = st.audio_input("Nagraj notatkę głosową USG", key="audio_input_widget")

    if audio_recorded is not None:
        current_audio_size = len(audio_recorded.getvalue())
        if current_audio_size != st.session_state["processed_audio_size"]:
            st.session_state["processed_audio_size"] = current_audio_size
            
            if client is not None:
                tmp_path = None
                raw_transcript = ""
                
                with st.spinner("🧠 KROK 1/2: Rozpoznawanie mowy (Whisper)..."):
                    try:
                        file_ext = ".wav"
                        if hasattr(audio_recorded, "name") and audio_recorded.name:
                            ext = os.path.splitext(audio_recorded.name)[1]
                            if ext: file_ext = ext

                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                            tmp_file.write(audio_recorded.getvalue())
                            tmp_path = tmp_file.name

                        with open(tmp_path, "rb") as audio_file:
                            prompt_vet = "Transkrypcja opisu badania USG weterynaryjnego. Słownictwo: wątroba, śledziona, nerki, trzustka, pęcherz moczowy, jelita, dwunastnica, żołądek, okrężnica, nadnercza, prostata, macica, jajniki, polipy, miedniczki, mineralizacje, zachyłki, jelito czcze, BŚO."
                            res = client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="pl", prompt=prompt_vet)
                            raw_transcript = res.text.strip() if res.text else ""
                    except Exception as e: st.error(f"❌ Błąd transkrypcji: {e}")
                    finally:
                        if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)

                if raw_transcript and len(raw_transcript) > 2:
                    with st.spinner("🩺 KROK 2/2: Generowanie pełnych akapitów opisu USG..."):
                        try:
                            szablon_rozrodczy = get_rodne_text(st.session_state["plec_pacjenta"])
                            system_prompt = f"""
Jesteś profesjonalnym edytorem raportów USG weterynaryjnego. Przekształć notatkę w PEŁNE AKAPITY MEDYCZNE wg wzorców.
KRYTYCZNA ZASADA PŁCI (Pacjent: {st.session_state["plec_pacjenta"]}):
Dla układu rozrodczego / prostaty MUSISZ UŻYĆ DOKŁADNIE PONIŻSZEGO WZORCA: "{szablon_rozrodczy}"

MATRYCE AKAPITÓW DLA POZOSTAŁYCH NARZĄDÓW:
PĘCHERZ MOCZOWY: "Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. [WYMIAR] mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
NERKI: "Nerki prawidłowego kształtu i wielkości około [DODAJ WYMIARY], kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
NADNERCZA: "Nadnercza prawidłowej wielkości i kształtu, grubości około [WYMIAR] mm, bez uchwytnych zmian w budowie."
ŚLEDZIONA: "Śledziona prawidłowej wielkości, grubości około [WYMIAR] cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
ŻOŁĄDEK: "Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. [WYMIAR] mm, okolica odźwiernika bez zmian, ściana gr. ok. [WYMIAR] mm, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."
JELITA I DWUNASTNICA: "Ściana dwunastnicy niepogrubiała, ok. [WYMIAR] mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. [WYMIAR] mm, okrężnica wypełniona uformowanymi masami kałowymi."
WĄTROBA I PĘCHERZYK ŻÓŁCIOWY: "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. [WYMIAR] mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
TRZUSTKA: "Trzustka prawidłowej wielkości i kształtu, gr. ok. [WYMIAR] mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."
WĘZŁY CHŁONNE: "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie."
WOLNY PŁYN: "Brak wolnego płynu w jamie brzusznej."
{( 'TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.' if dodaj_tarczyce else '' )}
ZASADY WYLOTOWE: Oddzielaj narządy nową linią. Zwracaj WYŁĄCZNIE czysty tekst opisu medycznego.
"""
                            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Podyktowane:\n{raw_transcript}"}], temperature=0.0)
                            st.session_state["editable_report_area"] = response.choices[0].message.content.strip()
                            st.success("✅ Wzorcowy raport medyczny wygenerowany!")
                        except Exception as e:
                            st.session_state["editable_report_area"] = raw_transcript
                            st.warning(f"⚠️ Błąd generatora: {e}")
            else: st.error("⚠️ Brak aktywnego klienta OpenAI API.")
    else: st.session_state["processed_audio_size"] = 0 

    st.markdown("---")
    
    st.text_area("Edytor Raportu (Ostatnie poprawki):", key="editable_report_area", height=350)
    if st.button("💾 Zapisz ten opis do historii", key="save_btn_tab1"):
        add_to_history(st.session_state["editable_report_area"])
        st.success("Zapisano badanie do paska bocznego!")

# ==========================================
# TRYB 2: TABELA WYMIARÓW + SZYBKIE PATOLOGIE
# ==========================================
elif tryb == "📏 TRYB 2: Tabela Wymiarów":
    st.subheader("Wpisz wymiary i zaznacz odchylenia z bazy")
    st.caption("Uzupełnienie tabeli automatycznie buduje pełen opis medyczny. Zostawienie pustego pola wstawi '(...)'.")
    
    with st.container(border=True):
        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            dim_pecherz = st.text_input("Pęcherz ściana (mm)", placeholder="np. 1.1")
            dim_nerka_l = st.text_input("Nerka lewa (cm)", placeholder="np. 4.9 x 2.9")
            dim_nerka_p = st.text_input("Nerka prawa (cm)", placeholder="np. 4.8 x 2.8")
        with tm2:
            dim_spleen = st.text_input("Śledziona gr. (cm)", placeholder="np. 1.3")
            dim_zoladek = st.text_input("Żołądek ściana (mm)", placeholder="np. 2.3")
        with tm3:
            dim_dwunastnica = st.text_input("Dwunastnica ściana (mm)", placeholder="np. 2.4")
            dim_okresnica = st.text_input("Okrężnica ściana (mm)", placeholder="np. 1.3")
        with tm4:
            dim_trzustka = st.text_input("Trzustka gr. (mm)", placeholder="np. 8")
            dim_pecherzyk = st.text_input("Pęch. żółciowy ściana (mm)", placeholder="np. 1.1")

    val_pecherz = dim_pecherz.strip() if dim_pecherz.strip() else "..."
    val_nerka_l = dim_nerka_l.strip() if dim_nerka_l.strip() else "..."
    val_nerka_p = dim_nerka_p.strip() if dim_nerka_p.strip() else "..."
    val_spleen = dim_spleen.strip() if dim_spleen.strip() else "..."
    val_zoladek = dim_zoladek.strip() if dim_zoladek.strip() else "..."
    val_dwunastnica = dim_dwunastnica.strip() if dim_dwunastnica.strip() else "..."
    val_okresnica = dim_okresnica.strip() if dim_okresnica.strip() else "..."
    val_trzustka = dim_trzustka.strip() if dim_trzustka.strip() else "..."
    val_pecherzyk = dim_pecherzyk.strip() if dim_pecherzyk.strip() else "..."

    st.markdown("### 🧩 Szybkie Odchylenia")
    for key in ['pecherz_pat', 'nerki_pat', 'spleen_pat', 'jelita_pat', 'watroba_pat', 'trzustka_pat', 'plyn_pat']:
        if key not in st.session_state: st.session_state[key] = ""

    with st.expander("Kliknij, aby rozwinąć bazę szybkich patologii", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Pęcherz moczowy**")
            if st.button("➕ Zapalenie / Pogrubiała ściana / Osad"): st.session_state['pecherz_pat'] = "zmiernie wypełniony, ściana pogrubiała do 3 mm z cechami zapalenia, w świetle widoczny mierny osad"
            pecherz_pat = st.text_area("Pęcherz - edycja", key='pecherz_pat', height=68, label_visibility="collapsed")

            st.markdown("**Nerki**")
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                if st.button("➕ Przebudowa zwyr."): st.session_state['nerki_pat'] = "przebudowa zwyrodnieniowo-zapalna, zatarta granica korowo-rdzeniowa"
            with col_n2:
                if st.button("➕ Ogniska pozaw."): st.session_state['nerki_pat'] = "z widocznymi drobnymi ogniskami pozawałowymi w korze"
            nerki_pat = st.text_area("Nerki - edycja", key='nerki_pat', height=68, label_visibility="collapsed")

            st.markdown("**Śledziona**")
            if st.button("➕ Niejednorodna"): st.session_state['spleen_pat'] = "miąższ niejednorodny, drobno- i gruboośrodkowo przebudowany"
            spleen_pat = st.text_area("Śledziona - edycja", key='spleen_pat', height=68, label_visibility="collapsed")

        with c2:
            st.markdown("**Dwunastnica i Jelita**")
            if st.button("➕ Cechy IBD / Pogrubienie"): st.session_state['jelita_pat'] = "pętla jelita czczego pogrubiała do 5.9 mm na dł. 4 cm z zatartą warstwowością, węzły krezkowe odczynowe (cechy IBD)"
            jelita_pat = st.text_area("Jelita - edycja", key='jelita_pat', height=68, label_visibility="collapsed")

            st.markdown("**Wątroba i Pęcherzyk**")
            if st.button("➕ Hepatomegalia + Ogniska"): st.session_state['watroba_pat'] = "powiększona, miąższ z obecnością rozsianych ognisk hipoechogennych do 5.2 mm, zarys regularny"
            watroba_pat = st.text_area("Wątroba - edycja", key='watroba_pat', height=68, label_visibility="collapsed")

            st.markdown("**Trzustka & Płyn**")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                if st.button("➕ Zapalenie trzustki"): st.session_state['trzustka_pat'] = "lewy płat powiększony do 22 mm, obszar hipoechogennym 22x18.5 mm z miejscowym odczynem"
            with col_t2:
                if st.button("➕ Wolny płyn"): st.session_state['plyn_pat'] = "Niewielki uogólniony odczyn zapalny tkanki tłuszczowej oraz niewielka ilość wolnego płynu."
            trzustka_pat = st.text_area("Trzustka - edycja", key='trzustka_pat', height=68, label_visibility="collapsed")
            plyn_pat = st.text_area("Płyn - edycja", key='plyn_pat', height=68, label_visibility="collapsed")

    # Funkcje budujące
    def b_pech(pat, d): return f"Pęcherz moczowy {pat}. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle." if pat else f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {d} mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    def b_ner(pat, dl, dp): return f"Nerki prawidłowego kształtu, lewa ok. {dl} cm, prawa ok. {dp} cm, {pat}. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie." if pat else f"Nerki prawidłowego kształtu i wielkości około {dl} cm x {dp} cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    def b_spl(pat, d): return f"Śledziona {pat}, grubości około {d} cm, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona." if pat else f"Śledziona prawidłowej wielkości, grubości około {d} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
    def b_zol(d): return f"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. {d} mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."
    def b_jel(pat, d_dw, d_ok): return f"{pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. {d_ok} mm, okrężnica wypełniona uformowanymi masami kałowymi." if pat else f"Ściana dwunastnicy niepogrubiała, ok. {d_dw} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. {d_ok} mm, okrężnica wypełniona uformowanymi masami kałowymi."
    def b_wat(pat, d): return f"Wątroba {pat}. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie." if pat else f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {d} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
    def b_trz(pat, d): return f"Trzustka {pat}. Przewód trzustkowy nieposzerzony." if pat else f"Trzustka prawidłowej wielkości i kształtu, gr. ok. {d} mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."
    def b_plyn(pat): return f"{pat}" if pat else "Brak wolnego płynu w jamie brzusznej."

    report_sections = [
        b_pech(pecherz_pat, val_pecherz), get_rodne_text(st.session_state["plec_pacjenta"]), b_ner(nerki_pat, val_nerka_l, val_nerka_p),
        "Nadnercza prawidłowej wielkości i kształtu, grubości około ... mm, bez uchwytnych zmian w budowie.",
        b_spl(spleen_pat, val_spleen), b_zol(val_zoladek), b_jel(jelita_pat, val_dwunastnica, val_okresnica),
        b_wat(watroba_pat, val_pecherzyk), b_trz(trzustka_pat, val_trzustka),
        "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.", b_plyn(plyn_pat)
    ]
    if dodaj_tarczyce: report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")
    mode2_final_report = "\n\n".join(report_sections)
    
    if mode2_final_report != st.session_state.get("last_mode2_hash", ""):
        st.session_state["editable_report_area_2"] = mode2_final_report
        st.session_state["last_mode2_hash"] = mode2_final_report

    st.markdown("---")
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Odśwież widok", use_container_width=True):
            st.session_state["editable_report_area_2"] = mode2_final_report
            st.rerun()
    with c_btn2:
        if st.button("💾 Zapisz ten opis do historii", type="primary", key="save_btn_tab2", use_container_width=True):
            add_to_history(st.session_state.get("editable_report_area_2", mode2_final_report))
            st.success("Zapisano badanie do paska bocznego!")

    st.text_area("Edytor Raportu:", key="editable_report_area_2", height=350)

# ==========================================
# TRYB 3: WYBÓR ZMIENIONYCH NARZĄDÓW
# ==========================================
elif tryb == "📝 TRYB 3: Wybór Zmian":
    st.subheader("Zaznacz i nadpisz narządy z patologią")
    st.caption("Niezaznaczone narządy zostaną uzupełnione jako zdrowa norma. Wybierz narząd, aby otworzyć pole z tekstem do modyfikacji.")

    organs_defaults = {
        "Pęcherz moczowy": "Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana prawidłowej budowy, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle.",
        "Układ rozrodczy": get_rodne_text(st.session_state["plec_pacjenta"]),
        "Nerki": "Nerki prawidłowego kształtu i wielkości, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie.",
        "Nadnercza": "Nadnercza prawidłowej wielkości i kształtu, bez uchwytnych zmian w budowie.",
        "Śledziona": "Śledziona prawidłowej wielkości, jednorodna echogenicznie, miąższ drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona.",
        "Żołądek": "Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego.",
        "Jelita i Dwunastnica": "Ściana dwunastnicy niepogrubiała, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi.",
        "Wątroba i Pęcherzyk żółciowy": "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie.",
        "Trzustka": "Trzustka prawidłowej wielkości i kształtu, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony.",
        "Węzły chłonne": "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
        "Wolny płyn": "Brak wolnego płynu w jamie brzusznej."
    }
    if dodaj_tarczyce: organs_defaults["Tarczyca"] = "TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."

    final_mode3_paragraphs = []
    
    with st.container(border=False):
        c_left, c_right = st.columns(2)
        items = list(organs_defaults.items())
        half = len(items) // 2 + 1
        
        for i, (organ_name, default_text) in enumerate(items):
            col = c_left if i < half else c_right
            with col:
                is_changed = st.checkbox(f"🔴 Zmiany: **{organ_name}**", key=f"chk_{organ_name}")
                if is_changed:
                    custom_text = st.text_area(f"Opisz patologię ({organ_name}):", value=default_text, key=f"txt_{organ_name}", height=100)
                    final_mode3_paragraphs.append(custom_text)
                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
                else:
                    final_mode3_paragraphs.append(default_text)

    mode3_final_report = "\n\n".join(final_mode3_paragraphs)

    if mode3_final_report != st.session_state.get("last_mode3_hash", ""):
        st.session_state["editable_report_area_3"] = mode3_final_report
        st.session_state["last_mode3_hash"] = mode3_final_report

    st.markdown("---")
    st.text_area("Edytor Raportu:", key="editable_report_area_3", height=350)
    
    if st.button("💾 Zapisz ten opis do historii", key="save_btn_tab3"):
        add_to_history(st.session_state.get("editable_report_area_3", mode3_final_report))
        st.success("Zapisano badanie do paska bocznego!")


# ==========================================
# SIDEBAR DOLNY: HISTORIA BADAŃ
# ==========================================
with st.sidebar:
    st.markdown("---")
    st.header("📜 Historia Sesji")
    
    if st.session_state["reports_history"]:
        for i, item in enumerate(st.session_state["reports_history"]):
            label = f"🕒 {item['time']} - {item['snippet']}"
            if st.button(label, key=f"hist_{i}", use_container_width=True):
                st.session_state["editable_report_area"] = item["text"]
                st.session_state["editable_report_area_2"] = item["text"]
                st.session_state["editable_report_area_3"] = item["text"]
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Wyczyść historię", use_container_width=True):
            st.session_state["reports_history"] = []
            st.rerun()
    else:
        st.info("Historia jest pusta. Wygeneruj opis i użyj przycisku 'Zapisz'.")
