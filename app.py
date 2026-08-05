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
if "full_report_mode1" not in st.session_state: st.session_state["full_report_mode1"] = ""
if "reports_history" not in st.session_state: st.session_state["reports_history"] = []
if "gatunek_pacjenta" not in st.session_state: st.session_state["gatunek_pacjenta"] = "Pies"
if "plec_pacjenta" not in st.session_state: st.session_state["plec_pacjenta"] = "Suka (kastrowana / kikut)"
if "last_mode1_hash" not in st.session_state: st.session_state["last_mode1_hash"] = ""
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
    
    /* Zmniejszenie marginesów nagłówków w sekcji patologii */
    .stMarkdown h5 {
        color: #135c7e;
        margin-top: 15px;
        margin-bottom: 5px;
    }
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

def get_rodne_text(plec_wybor, gatunek):
    p = str(plec_wybor).lower()
    if gatunek == "Kot":
        if "cała" in p:
            return "Macica niepowiększona, na wysokości rogów śr. do ok. 4,6 mm, na wysokości szyjki macicy do ok. 6,3 mm, na wysokości trzonu narządu do ok. 5 mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, lewy wielkości ok. 8 mm x 5 mm, prawy ok. 9 mm x 5,5 mm, normoechogenne, bez uchwytnych zmian guzowatych, bez uchwytnych zmian w budowie."
        else:
            return "" 
    else: # Pies
        if "niekastrowany" in p: 
            return "Gruczoł krokowy niepowiększony, wielkości ok. 2,6 cm x 2,5 cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia."
        elif "samiec kastrowany" in p: 
            return "Gruczoł krokowy obkurczony, zanikowy, wielkości ok. 1 cm x 0,7 cm, miąższ hipoechogenny, jednorodny, bez zmian w budowie."
        elif "cała" in p: 
            return "Macica niepowiększona, na wysokości rogów śr. do ok. 4,6 mm, na wysokości szyjki macicy do ok. 6,3 mm, na wysokości trzonu narządu do ok. 5 mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, lewy wielkości ok. 8 mm x 5 mm, prawy ok. 9 mm x 5,5 mm, normoechogenne, bez uchwytnych zmian guzowatych, bez uchwytnych zmian w budowie."
        else: 
            return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

def get_templates(gatunek):
    if gatunek == "Kot":
        return {
            "pecherz": "Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {pech} mm, prawidłowej budowy, bez cech zapalenia ostrego, mocz aechogenny, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle.",
            "nerki": "Nerki prawidłowego kształtu i wielkości {nerki}, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie.",
            "nadnercza": "Nadnercza prawidłowej wielkości i kształtu, grubości około {nadn} mm, bez uchwytnych zmian w budowie.",
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
            "nadnercza": "Nadnercza prawidłowej wielkości i kształtu, grubości około {nadn} mm, bez uchwytnych zmian w budowie.",
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
    
    if st.session_state.get("plec_pacjenta") not in plec_opcje:
        st.session_state["plec_pacjenta"] = plec_opcje[0]
        
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


szablony = get_templates(st.session_state["gatunek_pacjenta"])
g_akt = st.session_state["gatunek_pacjenta"]
plec_akt = st.session_state["plec_pacjenta"]
is_samiec = "samiec" in plec_akt.lower() or "kocur" in plec_akt.lower()
is_niekastrowany = "niekastrowany" in plec_akt.lower()

# GENEROWANIE DOMYŚLNEGO "ZDROWEGO" OPISU
def get_default_full_report(nadn_val="4,3"):
    def_pech = "1,1"
    def_nerki = "około 3,2 cm x 1,7 cm"
    def_nadn = nadn_val
    def_spl = "1,4"
    def_zol = "2,1" if g_akt == "Kot" else "2,9"
    def_dwu = "2,8"
    def_okr = "1,3"
    def_trz = "6,5" if g_akt == "Kot" else "8"
    def_pech_zol = "1" if g_akt == "Kot" else "1,1"

    sections = []
    
    if is_samiec and is_niekastrowany and g_akt == "Pies":
        sections.append("Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, miąższ obu jąder normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie.")
        
    sections.append(szablony['pecherz'].format(pech=def_pech))
    
    rodz_text = get_rodne_text(plec_akt, g_akt)
    if rodz_text:
        sections.append(rodz_text)
        
    sections.append(szablony['nerki'].format(nerki=def_nerki))
    sections.append(szablony['nadnercza'].format(nadn=def_nadn))
    sections.append(szablony['sledziona'].format(spl=def_spl))
    sections.append(szablony['zoladek'].format(zol=def_zol))
    sections.append(szablony['jelita'].format(dwu=def_dwu, okr=def_okr))
    sections.append(szablony['watroba'].format(pech_zol=def_pech_zol))
    sections.append(szablony['trzustka'].format(trz=def_trz))
    sections.append(szablony['wezly'])
    sections.append(szablony['plyn'])
    
    if dodaj_tarczyce:
        sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")
    
    return "\n\n".join(sections)

base_default_report = get_default_full_report()

# PILNUJEMY, ABY DOLNE OKNO NIGDY NIE BYŁO PUSTE NA STARCIE LUB PO ZMIANIE GATUNKU
if base_default_report != st.session_state.get("last_mode1_hash", "") or not st.session_state.get("full_report_mode1"):
    st.session_state["full_report_mode1"] = base_default_report
    st.session_state["last_mode1_hash"] = base_default_report
    st.session_state["editable_report_area"] = "" 

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
    st.subheader("Wypowiedz obserwacje dla ZMIENIONYCH narządów")
    st.caption("Podyktuj patologie. AI przetworzy TYLKO to, co powiesz. Gotowy tekst skopiuj i wklej w odpowiednie miejsce w swoim schemacie poniżej.")

    if "ai_success_msg" in st.session_state:
        st.success(st.session_state["ai_success_msg"])
        del st.session_state["ai_success_msg"]

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
                    with st.spinner("🩺 KROK 2/2: Generowanie zredagowanego fragmentu..."):
                        try:
                            system_prompt = f"""
                            Jesteś profesjonalnym edytorem raportów USG weterynaryjnego.
                            GATUNEK PACJENTA: {g_akt}
                            
                            ZADANIE:
                            Lekarz podyktował opis patologii lub wymiarów dla konkretnych narządów. Twoim zadaniem jest poprawienie interpunkcji, ortografii i błędów z rozpoznawania mowy, ALE przy zachowaniu DOKŁADNEGO brzmienia i słownictwa lekarza.
                            
                            KRYTYCZNE ZASADY:
                            1. STYL MEDYCZNY (RÓWNOWAŻNIKI ZDAŃ): Opisy weterynaryjne używają równoważników zdań. KATEGORYCZNIE ZABRANIA SIĘ dodawania słów łączących takich jak: "jest", "wykazuje", "posiada", "charakteryzuje się", "znajduje się". 
                               ZŁE: "Pęcherz moczowy jest dobrze wypełniony i wykazuje prawidłową budowę."
                               DOBRE: "Pęcherz moczowy dobrze wypełniony, prawidłowej budowy."
                            2. WIERNOŚĆ: Jeśli lekarz podyktował gotowe, poprawnie brzmiący fragment (np. "Pęcherz moczowy dobrze wypełniony, o prawidłowym kształcie, cienkościenny prawidłowej budowy"), oddaj go w formacie 1:1, dodając jedynie brakujące przecinki lub kropki.
                            3. Zredaguj i opisz TYLKO I WYŁĄCZNIE te narządy, o których lekarz bezpośrednio wspomina. Nie wymyślaj opisów innych narządów.
                            
                            Zwróć bezpośrednio gotowy fragment tekstu.
                            """
                            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Podyktowane:\n{raw_transcript}"}], temperature=0.0)
                            
                            st.session_state["editable_report_area"] = response.choices[0].message.content.strip()
                            st.success("✅ Fragment wygenerowany pomyślnie! Skopiuj go i zastąp odpowiedni tekst w schemacie na dole.")
                        except Exception as e:
                            st.session_state["editable_report_area"] = raw_transcript
                            st.warning(f"⚠️ Błąd generatora: {e}")
                else: 
                    st.warning("⚠️ Nie usłyszałem wyraźnie tekstu. Spróbuj nagrać jeszcze raz.")
            else: 
                st.error("⚠️ Brak aktywnego klienta OpenAI API. Sprawdź ustawienia klucza API w Secrets.")
    else: 
        st.session_state["processed_audio_size"] = 0 

    st.markdown("---")
    
    st.markdown("<h4 style='color: #135c7e;'>📝 Zredagowany fragment (z notatki głosowej):</h4>", unsafe_allow_html=True)
    st.text_area("Wynik AI", key="editable_report_area", height=150, placeholder="Tutaj pojawi się zredagowany tekst TYLKO dla tych narządów, o których podyktujesz...", label_visibility="collapsed")
    
    st.markdown("---")

    st.markdown("<h4 style='color: #135c7e;'>📄 Twój bazowy schemat (pełny raport do złożenia):</h4>", unsafe_allow_html=True)
    st.caption("Wklej zredagowany fragment z góry w odpowiednie miejsce poniżej (zastępując zdrowy opis chorego narządu).")
    
    st.text_area("Twój pełny raport", key="full_report_mode1", height=450, label_visibility="collapsed")

    if st.button("💾 Zapisz ten pełny opis do historii", key="save_btn_tab1"):
        add_to_history(st.session_state["full_report_mode1"])
        st.success("Zapisano badanie do paska bocznego!")


# ==========================================
# TRYB 2: TABELA WYMIARÓW + PATOLOGIE (Z NOWĄ BAZĄ)
# ==========================================
elif tryb == "📏 TRYB 2: Tabela Wymiarów":
    st.subheader("Wpisz wymiary i zaznacz patologie z bazy")
    st.caption("Wybierz gotową patologię dla narządu. Jeśli pole wymiarów będzie puste, aplikacja wstawi normę lub wymiar z wybranej patologii.")
    
    with st.container(border=True):
        tm1, tm2, tm3, tm4 = st.columns(4)
        with tm1:
            dim_pecherz = st.text_input("Pęcherz ściana (mm)", placeholder="np. 1.1")
            dim_nerka_l = st.text_input("Nerka lewa (cm)", placeholder="np. 3.2 x 1.7")
            dim_nerka_p = st.text_input("Nerka prawa (cm)", placeholder="np. 3.2 x 1.7")
        with tm2:
            dim_spleen = st.text_input("Śledziona gr. (cm)", placeholder="np. 1.4")
            dim_zoladek = st.text_input("Żołądek ściana (mm)", placeholder="np. 2.1")
            dim_nadnercza = st.text_input("Nadnercza gr. (mm)", placeholder="np. 4.3")
        with tm3:
            dim_dwunastnica = st.text_input("Dwunastnica ściana (mm)", placeholder="np. 2.8")
            dim_okresnica = st.text_input("Okrężnica ściana (mm)", placeholder="np. 1.3")
        with tm4:
            dim_trzustka = st.text_input("Trzustka gr. (mm)", placeholder="np. 8")
            dim_pecherzyk = st.text_input("Pęch. żółciowy ściana (mm)", placeholder="np. 1.1")

    gat = st.session_state["gatunek_pacjenta"]
    user_pech = dim_pecherz.strip()
    
    v_nl = dim_nerka_l.strip()
    v_np = dim_nerka_p.strip()
    # Jeśli użytkownik wpisał wymiar, używamy go. W przeciwnym razie ustawiamy flagę na false, 
    # żeby patologia mogła narzucić swoje specyficzne wymiary, jeśli jakieś ma (np. dla PKD).
    user_nerki_wpisane = bool(v_nl or v_np)
    if user_nerki_wpisane:
        v_nerki = f"lewa około {v_nl if v_nl else '3,2 x 1,7'} cm, prawa ok. {v_np if v_np else '3,5 x 2,4'} cm"
    else:
        v_nerki = "około 3,2 cm x 1,7 cm"
        
    v_nadn = dim_nadnercza.strip() if dim_nadnercza.strip() else "4,3"
    v_spl = dim_spleen.strip() if dim_spleen.strip() else "1,4"
    v_zol = dim_zoladek.strip() if dim_zoladek.strip() else ("2,1" if gat == "Kot" else "2,9")
    v_dwu = dim_dwunastnica.strip() if dim_dwunastnica.strip() else "2,8"
    v_okr = dim_okresnica.strip() if dim_okresnica.strip() else "1,3"
    v_trz = dim_trzustka.strip() if dim_trzustka.strip() else ("6,5" if gat == "Kot" else "8")
    v_pech_zol = dim_pecherzyk.strip() if dim_pecherzyk.strip() else ("1" if gat == "Kot" else "1,1")

    st.markdown("### 🧩 Baza Patologii i Odchyleń")

    # ================= LISTY OPCJI =================
    pat_pecherz_options = ["Prawidłowy (Norma)", "Słabo wypełniony pęcherz", "Zagęszczony mocz", "Ostre zapalenie pęcherza moczowego", "Przewlekłe zapalenie pęcherza", "Osad w pęcherzu", "Kamienie w pęcherzu", "Neo pęcherza"]
    pat_macica_options = ["Prawidłowy / Fizjologiczny (Norma)", "Macica - ruja", "Ropne zapalenie macicy", "Śluzo/wodomacicze"]
    pat_prostata_options = ["Prawidłowy / Fizjologiczny (Norma)", "Przerost prostaty", "Wnętrostwo", "Guz jądra"]
    pat_nerki_options = ["Prawidłowe (Norma)", "Zwyrodnienie nerek", "Zwyrodnienie nerek z poszerzeniem miedniczek", "PKD", "Pojedyncze torbiele w nerkach", "Ogniska pozawałowe", "Objaw rąbka", "Mineralizacje w zachyłkach miedniczek", "Ektopia moczowodu / Mineralizacje"]
    pat_nadnercza_options = ["Prawidłowe (Norma)", "Powiększone nadnercza", "Guzy nadnerczy"]
    pat_sledziona_options = ["Prawidłowa (Norma)", "Przebudowa przerostowa śledziony", "Guz śledziony", "Łagodne zmiany w śledzionie", "Mielolipoma"]
    pat_watroba_options = ["Prawidłowa (Norma)", "Zwyrodnienie i przerost drobnoguzkowy wątroby", "Zmiany guzowate w miąższu wątroby", "Ostre zapalenie wątroby"]
    pat_pecherzyk_options = ["Prawidłowy (Norma)", "Ostre zapalenie pęcherzyka", "Przewlekłe zapalenie pęcherzyka", "Błotko w pęcherzyku żółciowym", "Mineralizacje w pęcherzyku żółciowym", "Mineralizacje w pęcherzyku i drogach żółciowych", "Poszerzone drogi żółciowe", "Polipy w pęcherzyku żółciowym"]
    pat_trzustka_options = ["Prawidłowa (Norma)", "Ostre zapalenie trzustki", "Przebudowa przewlekła", "Przebudowa przewlekła z poszerzonym przewodem"]
    pat_pokarmowy_options = ["Prawidłowy (Norma)", "Ostre zapalenie żołądka", "Refluks / Nadkwasota", "Przewlekłe zapalenie żołądka", "Ostre zapalenie jelit", "Zmiany w typie zaburzeń trawienia", "IBD", "Przewlekłe zapalenie jelit"]

    # ================= WYŚWIETLANIE LIST W KOLUMNACH =================
    with st.container(border=True):
        st.markdown("<h5>UKŁAD MOCZOWO-PŁCIOWY:</h5>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: sel_pecherz = st.selectbox("Pęcherz moczowy:", pat_pecherz_options, label_visibility="collapsed")
        with col_p2: sel_macica = st.selectbox("Rozród (Samica):", pat_macica_options[:4], label_visibility="collapsed")
        with col_p3: sel_prostata = st.selectbox("Prostata/Jądra (Samiec):", pat_prostata_options, label_visibility="collapsed")
        
        st.markdown("<h5>NARZĄDY MIĄŻSZOWE (I):</h5>", unsafe_allow_html=True)
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1: sel_nerki = st.selectbox("Nerki:", pat_nerki_options, label_visibility="collapsed")
        with col_n2: sel_nadnercza = st.selectbox("Nadnercza:", pat_nadnercza_options, label_visibility="collapsed")
        with col_n3: sel_sledziona = st.selectbox("Śledziona:", pat_sledziona_options, label_visibility="collapsed")

        st.markdown("<h5>NARZĄDY MIĄŻSZOWE (II):</h5>", unsafe_allow_html=True)
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1: sel_watroba = st.selectbox("Wątroba:", pat_watroba_options, label_visibility="collapsed")
        with col_w2: sel_pech_zol = st.selectbox("Pęcherzyk żółciowy i drogi:", pat_pecherzyk_options, label_visibility="collapsed")
        with col_w3: sel_trzustka = st.selectbox("Trzustka:", pat_trzustka_options, label_visibility="collapsed")

        st.markdown("<h5>PRZEWÓD POKARMOWY:</h5>", unsafe_allow_html=True)
        col_pk1, col_pk2 = st.columns(2)
        with col_pk1: sel_pokarmowy = st.selectbox("Żołądek i Jelita:", pat_pokarmowy_options, label_visibility="collapsed")
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_d1, col_d2 = st.columns(2)
        with col_d1: chk_klos = st.checkbox("Dodaj: Kłos (kończyna międzypalcowa)")
        with col_d2: chk_zmiana = st.checkbox("Dodaj: Zmiana podskórna (okolica pośladka)")

    # ================= GENEROWANIE TEKSTÓW Z BAZY =================
    
    # 1. PĘCHERZ
    if sel_pecherz == "Słabo wypełniony pęcherz":
        val_p = user_pech if user_pech else "4,4"
        txt_pech = f"Pęcherz moczowy słabo wypełniony, prawidłowego kształtu, ściana gr. ok. {val_p} mm, jednak trudna do pełnej oceny ze względu na obkurczenie, wtórne do słabego wypełnienia pęcherza, mocz aechogenny, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Zagęszczony mocz":
        val_p = user_pech if user_pech else "1,2"
        txt_pech = f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {val_p} mm, prawidłowej budowy, bez cech zapalenia ostrego, mocz lekko zagęszczony, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Ostre zapalenie pęcherza moczowego":
        val_p = user_pech if user_pech else "4"
        txt_pech = f"Pęcherz moczowy umiarkowanie wypełniony, prawidłowego kształtu, ściana pogrubiała, gr. ok. {val_p} mm, o cechach obrzęku, mocz lekko zagęszczony, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Wokół pęcherza umiarkowany odczyn zapalny. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Przewlekłe zapalenie pęcherza":
        val_p = user_pech if user_pech else "2,3"
        txt_pech = f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, ściana lekko pogrubiała, do ok. {val_p} mm, warstwa śluzowa o nieco podwyższonej echogeniczności, o lekko nieregularnej powierzchni, bez cech zapalenia ostrego, mocz aechogenny, bez uchwytnych mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Osad w pęcherzu":
        val_p = user_pech if user_pech else "1,3"
        txt_pech = f"Pęcherz moczowy umiarkowanie wypełniony, prawidłowego kształtu, ściana niepogrubiała, gr. do ok. {val_p} mm, mocz zagęszczony, z obecnością mineralizacji w postaci osadu na dnie pęcherza, bez cech niedrożności, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Kamienie w pęcherzu":
        val_p = user_pech if user_pech else "3"
        txt_pech = f"Pęcherz moczowy umiarkowanie wypełniony, prawidłowego kształtu, ściana lekko pogrubiała, gr. do ok. {val_p} mm, mocz zagęszczony, z obecnością mineralizacji w postaci kilku (3-4), kamieni, o regularnej powierzchni, śr. do ok. 9 mm, bez cech niedrożności, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
    elif sel_pecherz == "Neo pęcherza":
        val_p = user_pech if user_pech else "1,4"
        txt_pech = f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {val_p} mm, warstwa śluzowa o nieco podniesionej echogeniczności, o lekko pofałdowanej powierzchni, bez cech zapalenia ostrego. W okolicy szyjki pęcherza moczowego, widoczne wywodzące się ze ściany, nieregularne, polipowatego kształtu twory, obustronnie, wys. ok. 5 mm, na dł. ok. 20 mm, na ich powierzchni uchwytne drobne mineralizacje. Okolica trójkąta pęcherza moczowego bez zmian. Mocz aechogenny, lokalizacja narządu prawidłowa. Ściana cewki moczowej nieco pogrubiała, do ok. 2,4 mm, przyściennie widoczne liczne mineralizacje, na długości do ok. połowy gruczołu krokowego, światło nieposzerzone, bez cech niedrożności."
    else:
        val_p = user_pech if user_pech else "1,1"
        txt_pech = szablony['pecherz'].format(pech=val_p)

    # 2. JĄDRA / PROSTATA / UKŁAD ROZRODCZY
    jadra_sekcja = ""
    if is_samiec and is_niekastrowany and g_akt == "Pies":
        if sel_prostata == "Wnętrostwo": jadra_sekcja = "Lewe jądro w worku mosznowym, prawidłowej wielkości i kształtu, ok. 2,2 cm x 1,4 cm, miąższ normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrze bez uchwytnych zmian w budowie. Prawe jądro wnętrowskie, zlokalizowane w kanale pachwinowym, w około 1/3 doogonowej części jego długości/ na terenie jamy brzusznej, doogonowo od nerki lewej i śledziony, w sąsiedztwie rozwidlenia aorty. Jądro nieco pomniejszone, wielkości ok. 1,3 cm x 2,2 cm, prawidłowego kształtu, miąższ o nieco obniżonej echogeniczności, jednorodny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrze bez zmian."
        elif sel_prostata == "Guz jądra": jadra_sekcja = "Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, wielkości ok. 3 cm x 1,5 cm, miąższ obu jąder normoechogenny, w miąższu jądra prawego obecność zmiany ogniskowej, wielkości ok. 10 mm x 5 mm, dobrze odgraniczonej, o niejednorodnej strukturze, w przewadze hiperechogennej względem miąższu jądra, dość bogato unaczynionej centralnie i obwodowo, śródjądrze jądra prawego zatarte, lewego dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."
        else: jadra_sekcja = "Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, miąższ obu jąder normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."

    txt_rodne = ""
    if g_akt == "Kot":
        if not is_samiec and "cała" in plec_akt.lower():
            if sel_macica == "Macica - ruja": txt_rodne = "Macica lekko rozpulchniona, na wysokości rogów śr. do ok. 5,5 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm, ściana lekko rozpulchniona do ok. 2,4 mm, prawidłowej budowy, warstwa śluzowa o nieco obniżonej echogeniczności, brak cech ropnego zapalenia w momencie badania. Jajniki lekko powiększone, wielkości ok. 14 mm x 7 mm, normoechogenne, w miąższu widoczne pojedyncze, hipoechogenne obszary, śr. do ok. 2 mm, odpowiadające prawidłowym komórkom jajnikowym, brak zmian guzowatych, brak uchwytnych zmian patologicznych."
            elif sel_macica == "Ropne zapalenie macicy": txt_rodne = "Macica powiększona, na wysokości rogów śr. do ok. 10 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm. Ściana prawidłowej grubości, o lekko nieregularnej powierzchni warstwy śluzowej, w świetle macicy zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            elif sel_macica == "Śluzo/wodomacicze": txt_rodne = "Macica powiększona, na wysokości rogów śr. ok. 10 mm, na wysokości szyjki macicy ok. 10 mm, na wysokości trzonu narządu ok. 7 mm. Ściana lekko pogrubiała do ok. 2,5 mm, o lekko podwyższonej echogeniczności, w świetle macicy nieco zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            else: txt_rodne = get_rodne_text(plec_akt, g_akt)
    else: # Pies
        if is_samiec:
            if sel_prostata == "Przerost prostaty": txt_rodne = "Gruczoł krokowy powiększony, wielkości ok. 4,3 cm x 3,4 cm, miąższ hiperechogenny, nieco niejednorodny, z licznymi, drobnymi torbielami prostymi, śr. do ok. 3 mm, bez uchwytnych zmian guzowatych, bez cech zapalenia ostrego."
            else: txt_rodne = get_rodne_text(plec_akt, g_akt)
        else:
            if sel_macica == "Macica - ruja": txt_rodne = "Macica lekko rozpulchniona, na wysokości rogów śr. do ok. 5,5 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm, ściana lekko rozpulchniona do ok. 2,4 mm, prawidłowej budowy, warstwa śluzowa o nieco obniżonej echogeniczności, brak cech ropnego zapalenia w momencie badania. Jajniki lekko powiększone, wielkości ok. 14 mm x 7 mm, normoechogenne, w miąższu widoczne pojedyncze, hipoechogenne obszary, śr. do ok. 2 mm, odpowiadające prawidłowym komórkom jajnikowym, brak zmian guzowatych, brak uchwytnych zmian patologicznych."
            elif sel_macica == "Ropne zapalenie macicy": txt_rodne = "Macica powiększona, na wysokości rogów śr. do ok. 10 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm. Ściana prawidłowej grubości, o lekko nieregularnej powierzchni warstwy śluzowej, w świetle macicy zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            elif sel_macica == "Śluzo/wodomacicze": txt_rodne = "Macica powiększona, na wysokości rogów śr. ok. 10 mm, na wysokości szyjki macicy ok. 10 mm, na wysokości trzonu narządu ok. 7 mm. Ściana lekko pogrubiała do ok. 2,5 mm, o lekko podwyższonej echogeniczności, w świetle macicy nieco zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            else: txt_rodne = get_rodne_text(plec_akt, g_akt)

    # 3. NERKI
    if sel_nerki == "Zwyrodnienie nerek": txt_ner = f"Nerki prawidłowego kształtu i wielkości, lewa około {v_nl if v_nl else '3,2 x 1,7'} cm, prawa ok. {v_np if v_np else '3,5 x 2,4'} cm, warstwa korowa o lekko podwyższonej echogeniczności, nieco niejednorodna struktura, nerki o lekko zatartej granicy korowo-rdzeniowej, stosunek obu warstw zachowany/warstwa korowa lekko pogrubiała/warstwa korowa odcinkowo lekko ścieńczała. Torebka narządu nieco nieregularna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Zwyrodnienie nerek z poszerzeniem miedniczek": txt_ner = f"Nerki prawidłowego kształtu i wielkości, lewa około {v_nl if v_nl else '3,2 x 1,7'} cm, prawa ok. {v_np if v_np else '3,5 x 2,4'} cm, warstwa korowa o lekko podwyższonej echogeniczności, nieco niejednorodna struktura, nerki o lekko zatartej granicy korowo-rdzeniowej, stosunek obu warstw zachowany/warstwa korowa lekko pogrubiała/warstwa korowa odcinkowo lekko ścieńczała. Torebka narządu nieco nieregularna, miedniczki nerkowe lekko poszerzone, lewa do ok. 2,5 mm, prawa do ok. 2,8 mm, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "PKD": txt_ner = f"Nerki zniekształcone, powiększone, lewa około {v_nl if v_nl else '6,3 x 4,15'} cm, prawa {v_np if v_np else '8,4 x 4,7'} cm, w miąższu obu nerek obecne liczne, torbiele proste i złożone, w nerce lewej największa wielkości ok. 5,6 cm x 4,35 cm, w nerce prawej wielkości ok. 3,1 cm x 2,75 cm, wszystkie wypełnione lekko zagęszczonym płynem, wyraźnie modulujące torebkę narządu. Pozostałe fragmenty miąższu o podwyższonej echogeniczności, z pojedynczymi ogniskami zwłóknień, nerki o zatartej granicy korowo-rdzeniowej. Torebka narządu nieregularna, hiperechogenna, miedniczki nerkowe lekko poszerzone, lewa do ok. 4,6 mm, prawa do ok. 3 mm, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Pojedyncze torbiele w nerkach": txt_ner = f"Nerki prawidłowego kształtu i wielkości, lewa około {v_nl if v_nl else '5,0 x 3,0'} cm, prawa ok. {v_np if v_np else '5,0 x 3,0'} cm, miąższ o lekko podwyższonej echogeniczności, w warstwie korowej obu nerek obecne pojedyncze torbiele proste, w nerce lewej śr. do ok. 2 mm, w nerce prawej śr. do ok. 1,8 mm, wypełnione aechogennym płynem, nerki o miernie zatartej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Ogniska pozawałowe": txt_ner = f"Nerki prawidłowego kształtu i wielkości, lewa około {v_nl if v_nl else '3,2 x 1,7'} cm, prawa ok. {v_np if v_np else '3,5 x 2,4'} cm, warstwa korowa o lekko podwyższonej echogeniczności, nieco niejednorodna struktura, w miąższu nerek obecne pojedyncze, hiperechogenne, klinowate ogniska, susp. ogniska pozawałowe, nerki o lekko zatartej granicy korowo-rdzeniowej, stosunek obu warstw zachowany/warstwa korowa lekko pogrubiała/warstwa korowa odcinkowo lekko ścieńczała. Torebka narządu lekko nieregularna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Objaw rąbka": txt_ner = f"Nerki prawidłowego kształtu i wielkości, lewa około {v_nl if v_nl else '5,0 x 3,0'} cm, prawa ok. {v_np if v_np else '5,0 x 3,0'} cm, miąższ o prawidłowej echogeniczności, nerki o miernie zatartej granicy korowo-rdzeniowej, obecny objaw rąbka gr. ok. 1,2 mm, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Mineralizacje w zachyłkach miedniczek": txt_ner = f"Nerki prawidłowego kształtu i wielkości około {v_nerki}, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, miedniczki nerkowe nieposzerzone, w zachyłkach miedniczek nerkowych obecne pasmowate ogniska mineralizacji, bez formowania kamieni, bez cech niedrożności. Moczowody bez uchwytnych zmian w budowie."
    elif sel_nerki == "Ektopia moczowodu / Mineralizacje": txt_ner = "Ektopia moczowodu / Mineralizacje w moczowodach (Zalecany dodatkowy opis ręczny)."
    else: txt_ner = szablony['nerki'].format(nerki=v_nerki)

    # 4. NADNERCZA
    if sel_nadnercza == "Powiększone nadnercza": txt_nadn = "Nadnercza powiększone i zaokrąglone w biegunach, lewe grubości około 6,3 mm w biegunie doogonowym, ok. 6,2 mm w biegunie doczaszkowym, prawe grubości około 6,3 mm w biegunie doogonowym, ok. 6,2 mm w biegunie doczaszkowym, bez uchwytnych zmian guzowatych."
    elif sel_nadnercza == "Guzy nadnerczy": txt_nadn = "Nadnercze lewe powiększone, w biegunie doogonowym gr. ok. 11 mm, tutaj zmiana ogniskowa wielkości ok. 1,4 cm x 1,1 cm, o lekko podwyższonej, nieco niejednorodnej echogeniczności, unaczynienie obwodowe, zmiana powodująca efekt masy na okoliczne struktury, bez cech penetracji do okolicznych naczyń, biegun doczaszkowy w normie wielkości, gr. ok. 5,4 mm. Nadnercze prawe prawidłowej wielkości i kształtu, gr. ok. 5-5,6 mm, bez uchwytnych zmian w budowie."
    else: txt_nadn = szablony['nadnercza'].format(nadn=v_nadn)

    # 5. ŚLEDZIONA
    if sel_sledziona == "Przebudowa przerostowa śledziony": txt_spl = f"Śledziona prawidłowej wielkości, grubości około {v_spl} cm na wysokości trzonu narządu, miąższ lekko niejednorodny, drobnoziarnisty, bez uchwytnych zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
    elif sel_sledziona == "Guz śledziony": txt_spl = f"Śledziona powiększona, gr. ok. {v_spl if v_spl != '1,4' else '2,9'} cm na wysokości trzonu narządu, miąższ dość jednorodny, drobnoziarnisty, w miąższu na wysokości trzonu śledziony, bardziej dogłowowo, obecność zmiany ogniskowej, wielkości ok. 6,7 mm x 5,5 mm, o niejednorodnej strukturze, o mieszanej echogeniczności, w przewadze hipoechogennej względem miąższu śledziony, z obszarami hiperechogennymi, unaczynionej obwodowo, wyraźnie modulującej torebkę narządu. Reszta torebki narządu lekko nieregularna, hiperechogenna. Żyła śledzionowa nieposzerzona."
    elif sel_sledziona == "Łagodne zmiany w śledzionie": txt_spl = f"Śledziona prawidłowej wielkości, grubości około {v_spl} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, w miąższu na wysokości trzonu śledziony, obecność hipoechogennego obszaru wielkości ok. 6,7 mm x 5,2 mm, o dosyć regularnym kształcie, unaczynienie zbliżone do unaczynienia śledziony, bez cech modulowania torebki narządu. Torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
    elif sel_sledziona == "Mielolipoma": txt_spl = f"Śledziona prawidłowej wielkości, grubości około {v_spl} cm na wysokości trzonu narządu, miąższ delikatnie niejednorodny, drobnoziarnisty, z obecnością pojedynczych, hiperechogennych, nieunaczynionych, regularnego kształtu obszarów, podtorebkowo i wzdłuż naczyń, średnicy do ok. 2,7 mm, torebka narządu nieco nieregularna, hiperechogenna. Żyła śledzionowa nieposzerzona."
    else: txt_spl = szablony['sledziona'].format(spl=v_spl)

    # 6. WĄTROBA
    if sel_watroba == "Zwyrodnienie i przerost drobnoguzkowy wątroby": txt_wat = "Wątroba powiększona, miąższ gruboziarnisty, lekko niejednorodny, o podwyższonej echogeniczności, z licznymi hipoechogennymi obszarami, słabo odgraniczonymi, unaczynienie zbliżone do unaczynienia wątroby, śr. do ok. 8 mm, bez cech modulacji brzegu narządu, krawędzie narządu nieco zaokrąglone. Naczynia wątrobowe nieposzerzone."
    elif sel_watroba == "Zmiany guzowate w miąższu wątroby": txt_wat = "Wątroba powiększona, miąższ gruboziarnisty, lekko niejednorodny, o lekko podwyższonej echogeniczności, w miąższu działu lewym obecność zmiany ogniskowej, wielkości ok. 8 mm x 4 mm, o niejednorodnej strukturze, o mieszanej echogeniczności, w przewadze hipoechogennej względem miąższu, z obszarami hiperechogennymi, unaczynionej obwodowo, bez cech modulacji brzegu narządu, krawędzie narządu nieco zaokrąglone. Naczynia wątrobowe nieposzerzone."
    elif sel_watroba == "Ostre zapalenie wątroby": txt_wat = "Wątroba lekko powiększona, miąższ gruboziarnisty, jednorodny, o obniżonej echogeniczności, rysunek naczyń silniej zaznaczony, brak uchwytnych zmian ogniskowych, krawędzie narządu regularne. Ostry odczyn zapalny okołowątrobowy."
    else: txt_wat = "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez uchwytnych zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone."

    # 7. PĘCHERZYK ŻÓŁCIOWY (doklejany do Wątroby)
    if sel_pech_zol == "Ostre zapalenie pęcherzyka": txt_wat += " Pęcherzyk żółciowy niepowiększony, ściana pogrubiała, o cechach obrzęku, gr. ok. 1,9 mm, z niewielką ilością zagęszczeń żółci w świetle. Drogi żółciowe poszerzone, przewód żółciowy wspólny szer. do ok. 4 mm, bez uchwytnych złogów w świetle. Ostry odczyn zapalny wzdłuż dróg żółciowych. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Przewlekłe zapalenie pęcherzyka": txt_wat += " Pęcherzyk żółciowy niepowiększony, ściana pogrubiała, o podwyższonej echogeniczności, gr. ok. 1,9 mm, z nieco zwiększoną ilością błotka w świetle, zajmującego ok. 1/3 objętości pęcherzyka, bez cech niedrożności. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Błotko w pęcherzyku żółciowym": txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {v_pech_zol} mm, z nieco zwiększoną ilością błotka w świetle, zajmującego ok. 1/3 objętości pęcherzyka, bez cech niedrożności. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Mineralizacje w pęcherzyku żółciowym": txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {v_pech_zol} mm, z dość obfitym osadem mineralnym na dnie pęcherzyka/ z obecnością konglomeratów mineralnych śr. do ok. 4 mm, bez cech niedrożności. Drogi żółciowe nieposzerzone, bez uchwytnych złogów w świetle. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Mineralizacje w pęcherzyku i drogach żółciowych": txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {v_pech_zol} mm, z dość obfitym osadem mineralnym na dnie pęcherzyka/ z obecnością konglomeratów mineralnych śr. do ok. 4 mm. Drogi żółciowe lekko poszerzone, przewód żółciowy wspólny szer. do ok. 4 mm, w świetle drobne ogniska mineralizacji śr. do ok. 2 mm, nie powodujące niedrożności całkowitej. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Poszerzone drogi żółciowe": txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. do {v_pech_zol} mm. Przewód pęcherzykowy lekko poszerzony, do ok. 5 mm, w świetle aechogenna żółć, dalej pżw również nieco poszerzony, do ok. 4,5 mm, w świetle aechogenna żółć. Układ wrotny bez uchwytnych zmian w budowie."
    elif sel_pech_zol == "Polipy w pęcherzyku żółciowym": txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {v_pech_zol} mm, z nieco zwiększoną ilością zagęszczeń żółci w świetle, zajmujących ok. 1/3 objętości pęcherzyka, bez cech niedrożności, widoczne również pojedyncze, polipowate struktury przyściennie, wys. do ok. 3 mm, bez cech hiperwaskularyzacji. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
    else: txt_wat += f" Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {v_pech_zol} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    # 8. TRZUSTKA
    if sel_trzustka == "Ostre zapalenie trzustki": txt_trz = "Trzustka powiększona, gr. do ok. 15 mm na wysokości płata prawego, brzegi lekko nieregularne, miąższ o obniżonej echogeniczności w porównaniu z otaczającym tłuszczem, wokół narządu ostry odczyn zapalny. Przewód trzustkowy nieposzerzony."
    elif sel_trzustka == "Przebudowa przewlekła": txt_trz = f"Trzustka prawidłowej wielkości i kształtu, gr. ok. {v_trz} mm w płacie prawym, brzegi nieco nieregularne, struktura lekko niejednorodna, miąższ o niejednorodnej/ o podniesionej/ o obniżonej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."
    elif sel_trzustka == "Przebudowa przewlekła z poszerzonym przewodem": txt_trz = f"Trzustka prawidłowej wielkości i kształtu, gr. ok. {v_trz} mm w płacie lewym, brzegi nieco nieregularne, struktura dość jednorodna, miąższ o obniżonej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieregularnie poszerzony do ok. 2,5 mm, bez uchwytnych złogów w świetle."
    else: txt_trz = szablony['trzustka'].format(trz=v_trz)

    # 9. PRZEWÓD POKARMOWY (Żołądek + Jelita jako jeden blok lub dwa w zależności od wyboru)
    txt_zol = ""
    txt_jel = ""
    
    if sel_pokarmowy == "Ostre zapalenie żołądka":
        txt_zol = "Żołądek poszerzony, w świetle zwiększona ilość gazu, aechogennego płynu i resztek treści, ściana o zachowanej warstwowości, pomiędzy fałdami pogrubiała do około 3,3 mm, w trzonie ok. 14 mm, nieco rozpulchniona warstwa śluzowa, obrzęk warstwy podśluzowej, ściana odźwiernika pogrubiała do ok. 6 mm, drożność zachowana, perystaltyka spowolniona. Wokół żołądka ostry odczyn zapalny, węzeł chłonny żołądkowy powiększony, śr. ok. 5 mm, wzbudzony zapalnie."
        txt_jel = szablony['jelita'].format(dwu=v_dwu, okr=v_okr)
    elif sel_pokarmowy == "Refluks / Nadkwasota":
        txt_zol = "Żołądek lekko poszerzony, w świetle zwiększona ilość aechogennego płynu i gazu (susp. nadkwasota/refluks), ściana o mniejszym pofałdowaniu, o zachowanej warstwowości, o prawidłowej grubości, pomiędzy fałdami do około 3,7 mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka lekko spowolniona, brak cech zapalenia ostrego."
        txt_jel = szablony['jelita'].format(dwu=v_dwu, okr=v_okr)
    elif sel_pokarmowy == "Przewlekłe zapalenie żołądka":
        txt_zol = "Żołądek nieposzerzony, w świetle nieco zwiększona ilość płynnej treści i gazu, ściana o zachowanej warstwowości, niepogrubiała, pomiędzy fałdami do około 3,6 mm, w trzonie ok. 4,3 mm, warstwa śluzowa o lekko podwyższonej echogeniczności, warstwa podśluzowa silniej zaznaczona, silniej echogenna, warstwa mięśniowa nieco pogrubiała na wysokości trzonu, do ok. 2 mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka nieco spowolniona."
        txt_jel = szablony['jelita'].format(dwu=v_dwu, okr=v_okr)
    elif sel_pokarmowy == "Ostre zapalenie jelit":
        txt_zol = szablony['zoladek'].format(zol=v_zol)
        txt_jel = "Ściana dwunastnicy lekko pogrubiała, gr. ok. 7 mm, warstwowość zachowana, warstwa śluzowa rozpulchniona, światło nieco poszerzone do ok. 7 mm, wypełnione zwiększoną ilością hiperechogennego, przelewającego się płynu oraz gazu, perystaltyka lekko spowolniona. Jelita cienkie co zachowanej warstwowości ściany, ściana pogrubiała do ok. 4,5 mm, warstwa śluzowa rozpulchniona, perystaltyka lekko spowolniona. Światło nieco odcinkowo poszerzone do ok. 10 mm, w świetle zwiększona ilość przelewającego się, hiperechogennego płynu oraz gazu. Lekki odczyn zapalny międzypętlowy, węzły chłonne jelita czczego powiększone, wzbudzone zapalnie, śr. ok. 8 mm. Ujście BŚO bez zmian. Ściana okrężnicy pogrubiała, o zachowanej warstwowości, gr. ok. 2,4 mm, rozpulchnienie warstwy śluzowej, w świetle okrężnicy płynne masy kałowe i gaz."
    elif sel_pokarmowy == "Zmiany w typie zaburzeń trawienia":
        txt_zol = szablony['zoladek'].format(zol=v_zol)
        txt_jel = "Ściana dwunastnicy niepogrubiała, gr. ok. 3,6 mm, warstwowość zachowana, światło nieposzerzone, wypełnione niewielką ilością płynnej, lekko przelewającej się treści oraz zwiększoną ilością gazu, perystaltyka lekko spowolniona. Reszta jelit cienkich o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka lekko przyspieszona. Światło nieco odcinkowo poszerzone, do ok. 5 mm, w świetle zwiększona ilość odcinkowo przelewającego się, hiperechogennego płynu oraz gazu. Ujście BŚO bez zmian. Ściana okrężnicy o zachowanej warstwowości, niepogrubiała, do ok. 1,4 mm, w świetle okrężnicy na wpół uformowane masy kałowe i gaz."
    elif sel_pokarmowy == "IBD":
        txt_zol = szablony['zoladek'].format(zol=v_zol)
        txt_jel = "Ściana dwunastnicy nieco pogrubiała, ok. 3,4 mm, warstwowość zachowana, warstwa podśluzowa silniej zaznaczona, światło nieposzerzone, próżne, perystaltyka prawidłowa. Reszta jelit cienkich o zachowanej warstwowości ściany, ściana lekko pogrubiała do ok. 3,4 mm, w jelicie biodrowym do ok. 3,6 mm, warstwa mięśniowa lekko pogrubiała do ok. 1,3 mm, w jelicie biodrowym do ok. 2 mm, warstwa podśluzowa silniej zaznaczona, perystaltyka zachowana. Światło nieposzerzone, wypełnione niewielką ilością płynnej treści. Węzły chłonne jelita czczego lekko powiększone, śr. ok. 4,8 mm, nieco reaktywne przewlekle, obecny umiarkowany, przewlekły odczyn zapalny międzypętlowy. Ujście BŚO bez uchwytnych zmian, wokół lekki, przewlekły odczyn zapalny, okoliczne węzły chłonne śr. ok. 4,2 mm, nieco wzbudzone zapalnie przewlekle. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. 1,8 mm, okrężnica wypełniona uformowanymi masami kałowymi."
    elif sel_pokarmowy == "Przewlekłe zapalenie jelit":
        txt_zol = szablony['zoladek'].format(zol=v_zol)
        txt_jel = "Ściana dwunastnicy niepogrubiała, ok. 3 mm, warstwowość zachowana, warstwa śluzowa o lekko podwyższonej echogeniczności, światło nieposzerzone, w świetle niewielka ilość hiperechogennego, lekko przelewającego się płynu i gazu, perystaltyka lekko spowolniona. Reszta jelit cienkich o zachowanej warstwowości ściany, ściana lekko pogrubiała do ok. 3,4 mm, warstwa śluzowa o lekko podwyższonej echogeniczności, warstwa podśluzowa silniej zaznaczona, perystaltyka lekko przyspieszona. Światło nieposzerzone, wypełnione niewielką ilością płynnej, lekko przelewającej się treści i gazu. Węzły chłonne jelita czczego lekko powiększone, śr. ok. 4,8 mm, nieco reaktywne przewlekle, obecny umiarkowany, przewlekły odczyn zapalny międzypętlowy. Ujście BŚO bez uchwytnych zmian, wokół lekki, przewlekły odczyn zapalny, okoliczne węzły chłonne śr. ok. 4,2 mm, nieco wzbudzone zapalnie przewlekle. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. 1,8 mm, okrężnica wypełniona uformowanymi masami kałowymi."
    else:
        txt_zol = szablony['zoladek'].format(zol=v_zol)
        txt_jel = szablony['jelita'].format(dwu=v_dwu, okr=v_okr)

    # =============== SKŁADANIE RAPORTU TRYBU 2 ===============
    report_sections = []
    
    if jadra_sekcja: report_sections.append(jadra_sekcja)
    report_sections.append(txt_pech)
    if txt_rodne: report_sections.append(txt_rodne)
    
    report_sections.extend([
        txt_ner,
        txt_nadn,
        txt_spl, 
        txt_zol, 
        txt_jel,
        txt_wat, 
        txt_trz,
        szablony['wezly'], 
        szablony['plyn']
    ])
    
    if dodaj_tarczyce: 
        report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")

    if chk_klos:
        report_sections.append("Kłos: W badaniu USG okolicy międzypalcowej, pomiędzy palcem III i IV, prawej kończyny miednicznej obecny znaczny obrzęk tkanki podskórnej, pomiędzy tkankami obecna niewielka ilość wolnego płynu. W tkance podskórnej, od strony grzbietowej, w miejscu największego obrzęku, obecna podłużna, hiperechogenna struktura, dł. ok. 2 cm, na głębokości ok. 4 mm od skóry. Podejrzenie ciała obcego.")
    if chk_zmiana:
        report_sections.append("Zmiana podskórna: Obecność zmiany podskórnej po stronie prawej w okolicy pośladka. Zmiana dobrze odgraniczona, owalna, dosyć regularnego kształtu, wielkości ok. 3,3 cm x 1,3 cm, jednorodna, w przewadze hiperechogenna względem otaczających tkanek, bez komponenty płynowej, bez cech hiperwaskularyzacji, nie powodująca efektu masy na okoliczne tkanki.")

    mode2_final_report = "\n\n".join(report_sections)
    
    if mode2_final_report != st.session_state.get("last_mode2_hash", ""):
        st.session_state["editable_report_area_2"] = mode2_final_report
        st.session_state["last_mode2_hash"] = mode2_final_report

    st.markdown("---")
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Odśwież widok", use_container_width=True):
            st.session_state["editable_report_area_2"] = mode2_final_report
    with c_btn2:
        if st.button("💾 Zapisz ten opis do historii", type="primary", key="save_btn_tab2", use_container_width=True):
            add_to_history(st.session_state.get("editable_report_area_2", mode2_final_report))
            st.success("Zapisano badanie do paska bocznego!")

    st.text_area("Edytor Raportu:", key="editable_report_area_2", height=450)

    st.markdown("<h4 style='color: #135c7e;'>📋 Gotowy Raport (do skopiowania):</h4>", unsafe_allow_html=True)
    st.code(st.session_state.get("editable_report_area_2", mode2_final_report), language=None)

# ==========================================
# TRYB 3: WYBÓR ZMIENIONYCH NARZĄDÓW
# ==========================================
elif tryb == "📝 TRYB 3: Wybór Zmian":
    st.subheader("Zaznacz i nadpisz narządy z patologią")
    st.caption("Niezaznaczone narządy zostaną uzupełnione jako zdrowa norma (odpowiednia dla gatunku). Wybierz narząd, aby otworzyć pole z tekstem do modyfikacji.")
    gat = st.session_state["gatunek_pacjenta"]

    organs_defaults = {}
    if is_samiec and is_niekastrowany and gat == "Pies":
        organs_defaults["Jądra"] = "Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, miąższ obu jąder normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."
    
    organs_defaults["Pęcherz moczowy"] = szablony['pecherz'].format(pech="1,1")
    
    rodz_text = get_rodne_text(plec_akt, gat)
    if rodz_text:
        organs_defaults["Układ rozrodczy"] = rodz_text
        
    organs_defaults["Nerki"] = szablony['nerki'].format(nerki="około 3,2 cm x 1,7 cm")
    organs_defaults["Nadnercza"] = szablony['nadnercza'].format(nadn="4,3")
    organs_defaults["Śledziona"] = szablony['sledziona'].format(spl="1,4")
    organs_defaults["Żołądek"] = szablony['zoladek'].format(zol=("2,1" if gat == "Kot" else "2,9"))
    organs_defaults["Jelita i Dwunastnica"] = szablony['jelita'].format(dwu="2,8", okr="1,3")
    organs_defaults["Wątroba i Pęcherzyk żółciowy"] = szablony['watroba'].format(pech_zol=("1" if gat == "Kot" else "1,1"))
    organs_defaults["Trzustka"] = szablony['trzustka'].format(trz=("6,5" if gat == "Kot" else "8"))
    organs_defaults["Węzły chłonne"] = szablony['wezly']
    organs_defaults["Wolny płyn"] = szablony['plyn']

    if dodaj_tarczyce: 
        organs_defaults["Tarczyca"] = "TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."

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
                # Historia nadpisuje pole właściwe dla danego trybu
                st.session_state["full_report_mode1"] = item["text"]
                st.session_state["editable_report_area_2"] = item["text"]
                st.session_state["editable_report_area_3"] = item["text"]
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Wyczyść historię", use_container_width=True):
            st.session_state["reports_history"] = []
            st.rerun()
    else:
        st.info("Historia jest pusta. Wygeneruj opis i użyj przycisku 'Zapisz'.")
