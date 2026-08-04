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
if "gatunek_pacjenta" not in st.session_state: st.session_state["gatunek_pacjenta"] = "Pies"
if "plec_pacjenta" not in st.session_state: st.session_state["plec_pacjenta"] = "Suka (kastrowana / kikut)"
if "last_mode2_hash" not in st.session_state: st.session_state["last_mode2_hash"] = ""
if "last_mode3_hash" not in st.session_state: st.session_state["last_mode3_hash"] = ""
if "processed_audio_size" not in st.session_state: st.session_state["processed_audio_size"] = 0

# ==========================================
# 2. ZAAWANSOWANA STYLIZACJA CSS
# ==========================================
st.markdown("""
    <style>
    :root {
        --color-pink: #f49ac1;
        --color-dark-teal: #135c7e;
        --color-btn-teal: #237a9f;
        --color-bg: #f9fbfb;
    }
    .stApp { background-color: var(--color-bg); }
    .custom-header {
        background-color: white; padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03); text-align: center;
        margin-bottom: 2rem; border-bottom: 3px solid var(--color-pink);
    }
    .custom-header .usg { color: var(--color-pink); font-weight: 900; font-size: 2.8rem; font-family: 'Arial', sans-serif;}
    .custom-header .scans { color: var(--color-dark-teal); font-weight: 900; font-size: 2.8rem; font-family: 'Arial', sans-serif;}
    .custom-header p { color: #666; font-size: 1.1rem; margin-top: 5px; font-weight: 500;}

    div.stButton > button {
        background-color: var(--color-btn-teal); color: white; border-radius: 25px !important;
        border: none; padding: 0.5rem 1.5rem; font-weight: 600; transition: all 0.3s ease;
    }
    div.stButton > button:hover { background-color: var(--color-dark-teal); box-shadow: 0 4px 10px rgba(19, 92, 126, 0.3); color: white;}
    section[data-testid="stSidebar"] div.stButton > button { background-color: white; color: var(--color-pink); border: 1px solid var(--color-pink); }
    section[data-testid="stSidebar"] div.stButton > button:hover { background-color: var(--color-pink); color: white; }

    .stCheckbox > label {
        background-color: white !important; padding: 12px 18px !important; border-radius: 10px !important;
        border: 1px solid #eef1f2 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important; width: 100%;
    }
    .stCheckbox > label:hover { border-color: var(--color-btn-teal) !important; box-shadow: 0 4px 8px rgba(35, 122, 159, 0.1) !important;}

    div[role="radiogroup"] {
        display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; gap: 15px !important; width: 100% !important;
    }
    div[role="radiogroup"] > label {
        background-color: white !important; border: 2px solid #e0e6e8 !important; border-radius: 12px !important;
        padding: 15px 10px !important; cursor: pointer !important; transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important; flex: 1 1 33% !important; min-height: 90px !important;
        text-align: center !important; display: flex !important; justify-content: center !important; align-items: center !important; margin: 0 !important;
    }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label p { font-size: 1.15rem !important; font-weight: 700 !important; color: var(--color-dark-teal) !important; margin: 0 !important; line-height: 1.3 !important;}
    div[role="radiogroup"] > label[data-checked="true"] {
        border-color: var(--color-pink) !important; background-color: #fffafb !important;
        box-shadow: 0 8px 16px rgba(244, 154, 193, 0.15) !important; transform: translateY(-3px);
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox > div > div { border-radius: 10px !important; border: 1px solid #dce4e6 !important;}
    .stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox > div > div:focus { border-color: var(--color-btn-teal) !important; box-shadow: 0 0 0 1px var(--color-btn-teal) !important;}
    </style>
""", unsafe_allow_html=True)

# GŁÓWNY NAGŁÓWEK
st.markdown("""
    <div class="custom-header">
        <span class="usg">USGVet</span> <span class="scans">Scans</span>
        <p>System Generowania Raportów Ultrasonograficznych</p>
    </div>
""", unsafe_allow_html=True)


# ==========================================
# EKRAN LOGOWANIA (HASŁO)
# ==========================================
def check_password():
    def password_entered():
        prawidlowe_haslo = st.secrets.get("APP_PASSWORD", "usg2024")
        if st.session_state["password"] == prawidlowe_haslo:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background-color: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; border-top: 4px solid #135c7e; margin-bottom: 2rem;'>
            <h3 style='color: #135c7e; margin-bottom: 10px;'>🔒 Dostęp Zabezpieczony</h3>
            <p style='color: #666; font-size: 0.95rem; margin-bottom: 0;'>Wprowadź hasło, aby skorzystać z generatora USG.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input("Hasło dostępu", type="password", on_change=password_entered, key="password", placeholder="Wpisz hasło...")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Niepoprawne hasło. Spróbuj ponownie.")
    return False

if not check_password():
    st.stop()

# ==========================================
# GŁÓWNA LOGIKA APLIKACJI
# ==========================================

api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip().strip('"').strip("'")

client = None
if HAS_OPENAI and api_key:
    try: client = OpenAI(api_key=api_key)
    except Exception: client = None

def add_to_history(report_text):
    if report_text and report_text.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        snippet = report_text[:35].replace("\n", " ") + "..."
        entry = {"time": timestamp, "snippet": snippet, "text": report_text}
        st.session_state["reports_history"].insert(0, entry)
        st.session_state["reports_history"] = st.session_state["reports_history"][:10]

def get_rodne_text(plec_wybor):
    p = str(plec_wybor).lower()
    if "niekastrowany" in p: 
        return "Gruczoł krokowy niepowiększony, wielkości ok. 2,6 cm x 2,5 cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia. Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, miąższ obu jąder normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."
    elif "samiec kastrowany" in p: 
        return "Gruczoł krokowy obkurczony, zanikowy, wielkości ok. 1 cm x 0,7 cm, miąższ hipoechogenny, jednorodny, bez zmian w budowie."
    elif "cała" in p: 
        return "Macica niepowiększona, na wysokości rogów śr. do ok. 4,6 mm, na wysokości szyjki macicy do ok. 6,3 mm, na wysokości trzonu narządu do ok. 5 mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, lewy wielkości ok. 8 mm x 5 mm, prawy ok. 9 mm x 5,5 mm, normoechogenne, bez uchwytnych zmian guzowatych, bez uchwytnych zmian w budowie."
    else: 
        return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

# BAZA SZABLONÓW DLA PSA I KOTA
def get_templates(gatunek):
    if gatunek == "Kot":
        return {
            "pecherz": "Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {pech} mm, prawidłowej budowy, bez cech zapalenia ostrego, mocz aechogenny, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle.",
            "nerki": "Nerki prawidłowego kształtu i wielkości {nerki}, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie.",
            "nadnercza": "Nadnercza prawidłowej wielkości i kształtu, grubości około 4,3 mm, bez uchwytnych zmian w budowie.",
            "sledziona": "Śledziona prawidłowej wielkości, grubości około {spl} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona.",
            "zoladek": "Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości, około 2,2-4,4 mm, w trzonie ok. {zol} mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego.",
            "jelita": "Ściana dwunastnicy niepogrubiała, gr. ok. {dwu} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość płynnej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa. Światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka zachowana. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, gr. do ok. {okr} mm, okrężnica wypełniona uformowanymi masami kałowymi.",
            "watroba": "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez uchwytnych zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. do {pech_zol} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie.",
            "trzustka": "Trzustka prawidłowej wielkości i kształtu, gr. ok. {trz} mm w płacie lewym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony.",
            "wezly": "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
            "plyn": "Brak wolnego płynu w jamie brzusznej."
        }
    else: # Pies
        return {
            "pecherz": "Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {pech} mm, prawidłowej budowy, bez cech zapalenia ostrego, mocz aechogenny, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle.",
            "nerki": "Nerki prawidłowego kształtu i wielkości {nerki}, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie.",
            "nadnercza": "Nadnercza prawidłowej wielkości i kształtu, grubości około 4,3 mm, bez uchwytnych zmian w budowie.",
            "sledziona": "Śledziona prawidłowej wielkości, grubości około {spl} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona.",
            "zoladek": "Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości, pomiędzy fałdami do około {zol} mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego.",
            "jelita": "Ściana dwunastnicy niepogrubiała, gr. ok. {dwu} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość płynnej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa. Światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka zachowana. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, gr. do ok. {okr} mm, okrężnica wypełniona uformowanymi masami kałowymi.",
            "watroba": "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez uchwytnych zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {pech_zol} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie.",
            "trzustka": "Trzustka prawidłowej wielkości i kształtu, gr. ok. {trz} mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony.",
            "wezly": "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
            "plyn": "Brak wolnego płynu w jamie brzusznej."
        }

# ==========================================
# SIDEBAR: USTAWIENIA GÓRNE
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color: #135c7e; font-weight: 700; margin-bottom: 10px;'>⚙️ Konfiguracja Pacjenta</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("<div style='font-weight: 600; color: #135c7e; margin-bottom: 5px; font-size: 15px;'>Gatunek:</div>", unsafe_allow_html=True)
        gatunek = st.selectbox(
            "Gatunek", 
            ["Pies", "Kot"],
            key="gatunek_pacjenta",
            label_visibility="collapsed"
        )
        
    plec_opcje = ["Suka (kastrowana / kikut)", "Suka (cała)", "Pies (samiec niekastrowany)", "Pies (samiec kastrowany)"] if gatunek == "Pies" else ["Kotka (kastrowana / kikut)", "Kotka (cała)", "Kocur (samiec niekastrowany)", "Kocur (samiec kastrowany)"]
    
    with st.container(border=True):
        st.markdown("<div style='font-weight: 600; color: #135c7e; margin-bottom: 5px; font-size: 15px;'>Płeć i stan fizjologiczny:</div>", unsafe_allow_html=True)
        plec = st.selectbox(
            "Płeć", 
            plec_opcje,
            key="plec_pacjenta",
            label_visibility="collapsed"
        )
        
    with st.container(border=True):
        dodaj_tarczyce = st.checkbox("Dodaj badanie tarczycy", value=False)

# Pobranie aktywnych szablonów narządów
szablony = get_templates(st.session_state["gatunek_pacjenta"])

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
                            sz_rozrodczy = get_rodne_text(st.session_state["plec_pacjenta"])
                            # Podmiana zmiennych w szablonach na komendę dla AI
                            ai_pech = szablony['pecherz'].replace('{pech}', '[WYMIAR]')
                            ai_ner = szablony['nerki'].replace('{nerki}', 'około [DODAJ WYMIARY]')
                            ai_spl = szablony['sledziona'].replace('{spl}', '[WYMIAR]')
                            ai_zol = szablony['zoladek'].replace('{zol}', '[WYMIAR]')
                            ai_jel = szablony['jelita'].replace('{dwu}', '[WYMIAR]').replace('{okr}', '[WYMIAR]')
                            ai_wat = szablony['watroba'].replace('{pech_zol}', '[WYMIAR]')
                            ai_trz = szablony['trzustka'].replace('{trz}', '[WYMIAR]')
                            
                            system_prompt = f"""
Jesteś profesjonalnym edytorem raportów USG weterynaryjnego. Przekształć notatkę w PEŁNE AKAPITY MEDYCZNE wg wzorców.
GATUNEK: {st.session_state["gatunek_pacjenta"]}
KRYTYCZNA ZASADA PŁCI (Pacjent: {st.session_state["plec_pacjenta"]}): "{sz_rozrodczy}"

MATRYCE AKAPITÓW DLA POZOSTAŁYCH NARZĄDÓW:
PĘCHERZ MOCZOWY: "{ai_pech}"
NERKI: "{ai_ner}"
NADNERCZA: "{szablony['nadnercza']}"
ŚLEDZIONA: "{ai_spl}"
ŻOŁĄDEK: "{ai_zol}"
JELITA I DWUNASTNICA: "{ai_jel}"
WĄTROBA I PĘCHERZYK ŻÓŁCIOWY: "{ai_wat}"
TRZUSTKA: "{ai_trz}"
WĘZŁY CHŁONNE: "{szablony['wezly']}"
WOLNY PŁYN: "{szablony['plyn']}"
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
    
    st.markdown("<h4 style='color: #135c7e;'>📋 Gotowy Raport (do skopiowania):</h4>", unsafe_allow_html=True)
    st.code(st.session_state["editable_report_area"], language=None)

    if st.button("💾 Zapisz ten opis do historii", key="save_btn_tab1"):
        add_to_history(st.session_state["editable_report_area"])
        st.success("Zapisano badanie do paska bocznego!")

# ==========================================
# TRYB 2: TABELA WYMIARÓW + SZYBKIE PATOLOGIE
# ==========================================
elif tryb == "📏 TRYB 2: Tabela Wymiarów":
    st.subheader("Wpisz wymiary i zaznacz odchylenia z bazy")
    st.caption("Puste pola zostaną zastąpione prawidłowymi, książkowymi wymiarami dla zaznaczonego gatunku.")
    
    with st.container(border=True):
        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            dim_pecherz = st.text_input("Pęcherz ściana (mm)", placeholder="np. 1.1")
            dim_nerka_l = st.text_input("Nerka lewa (cm)", placeholder="np. 3.2 x 1.7")
            dim_nerka_p = st.text_input("Nerka prawa (cm)", placeholder="np. 3.2 x 1.7")
        with tm2:
            dim_spleen = st.text_input("Śledziona gr. (cm)", placeholder="np. 1.4")
            dim_zoladek = st.text_input("Żołądek ściana (mm)", placeholder="np. 2.1")
        with tm3:
            dim_dwunastnica = st.text_input("Dwunastnica ściana (mm)", placeholder="np. 2.8")
            dim_okresnica = st.text_input("Okrężnica ściana (mm)", placeholder="np. 1.3")
        with tm4:
            dim_trzustka = st.text_input("Trzustka gr. (mm)", placeholder="np. 8")
            dim_pecherzyk = st.text_input("Pęch. żółciowy ściana (mm)", placeholder="np. 1.1")

    gat = st.session_state["gatunek_pacjenta"]
    v_pech = dim_pecherz.strip() if dim_pecherz.strip() else "1,1"
    v_nl = dim_nerka_l.strip()
    v_np = dim_nerka_p.strip()
    if v_nl or v_np:
        v_nerki = f"lewa ok. {v_nl or '...'} cm, prawa ok. {v_np or '...'} cm"
    else:
        v_nerki = "około 3,2 cm x 1,7 cm"
        
    v_spl = dim_spleen.strip() if dim_spleen.strip() else "1,4"
    v_zol = dim_zoladek.strip() if dim_zoladek.strip() else ("2,1" if gat == "Kot" else "2,9")
    v_dwu = dim_dwunastnica.strip() if dim_dwunastnica.strip() else "2,8"
    v_okr = dim_okresnica.strip() if dim_okresnica.strip() else "1,3"
    v_trz = dim_trzustka.strip() if dim_trzustka.strip() else ("6,5" if gat == "Kot" else "8")
    v_pech_zol = dim_pecherzyk.strip() if dim_pecherzyk.strip() else ("1" if gat == "Kot" else "1,1")

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

    txt_pech = f"Pęcherz moczowy {pecherz_pat}. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle." if pecherz_pat else szablony['pecherz'].format(pech=v_pech)
    txt_ner = f"Nerki prawidłowego kształtu, {v_nerki}, {nerki_pat}. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie." if nerki_pat else szablony['nerki'].format(nerki=v_nerki)
    txt_spl = f"Śledziona {spleen_pat}, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona." if spleen_pat else szablony['sledziona'].format(spl=v_spl)
    txt_jel = f"{jelita_pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, gr. do ok. {v_okr} mm, okrężnica wypełniona uformowanymi masami kałowymi." if jelita_pat else szablony['jelita'].format(dwu=v_dwu, okr=v_okr)
    txt_wat = f"Wątroba {watroba_pat}. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. do {v_pech_zol} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie." if watroba_pat else szablony['watroba'].format(pech_zol=v_pech_zol)
    txt_trz = f"Trzustka {trzustka_pat}. Przewód trzustkowy nieposzerzony." if trzustka_pat else szablony['trzustka'].format(trz=v_trz)
    txt_plyn = f"{plyn_pat}" if plyn_pat else szablony['plyn']

    report_sections = [
        txt_pech, 
        get_rodne_text(st.session_state["plec_pacjenta"]), 
        txt_ner,
        szablony['nadnercza'],
        txt_spl, 
        szablony['zoladek'].format(zol=v_zol), 
        txt_jel,
        txt_wat, 
        txt_trz,
        szablony['wezly'], 
        txt_plyn
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

    st.markdown("<h4 style='color: #135c7e;'>📋 Gotowy Raport (do skopiowania):</h4>", unsafe_allow_html=True)
    st.code(st.session_state.get("editable_report_area_2", mode2_final_report), language=None)

# ==========================================
# TRYB 3: WYBÓR ZMIENIONYCH NARZĄDÓW
# ==========================================
elif tryb == "📝 TRYB 3: Wybór Zmian":
    st.subheader("Zaznacz i nadpisz narządy z patologią")
    st.caption("Niezaznaczone narządy zostaną uzupełnione jako zdrowa norma (odpowiednia dla gatunku). Wybierz narząd, aby otworzyć pole z tekstem do modyfikacji.")
    gat = st.session_state["gatunek_pacjenta"]

    organs_defaults = {
        "Pęcherz moczowy": szablony['pecherz'].format(pech="1,1"),
        "Układ rozrodczy": get_rodne_text(st.session_state["plec_pacjenta"]),
        "Nerki": szablony['nerki'].format(nerki="około 3,2 cm x 1,7 cm"),
        "Nadnercza": szablony['nadnercza'],
        "Śledziona": szablony['sledziona'].format(spl="1,4"),
        "Żołądek": szablony['zoladek'].format(zol=("2,1" if gat == "Kot" else "2,9")),
        "Jelita i Dwunastnica": szablony['jelita'].format(dwu="2,8", okr="1,3"),
        "Wątroba i Pęcherzyk żółciowy": szablony['watroba'].format(pech_zol=("1" if gat == "Kot" else "1,1")),
        "Trzustka": szablony['trzustka'].format(trz=("6,5" if gat == "Kot" else "8")),
        "Węzły chłonne": szablony['wezly'],
        "Wolny płyn": szablony['plyn']
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
    
    st.markdown("<h4 style='color: #135c7e;'>📋 Gotowy Raport (do skopiowania):</h4>", unsafe_allow_html=True)
    st.code(st.session_state.get("editable_report_area_3", mode3_final_report), language=None)

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
