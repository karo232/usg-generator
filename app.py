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
                            Lekarz podyktował opis patologii lub wymiarów dla jednego lub kilku konkretnych narządów. 
                            Twoim zadaniem jest przekształcić tę notatkę w spójny, medyczny tekst w stylu opisu USG.
                            
                            KRYTYCZNA ZASADA:
                            Zredaguj i opisz TYLKO I WYŁĄCZNIE te narządy, o których lekarz bezpośrednio wspomina w notatce.
                            Kategorycznie ZABRANIA SIĘ generowania opisu dla pozostałych, zdrowych narządów, o których nie ma mowy w nagraniu.
                            Zwróć bezpośrednio gotowy fragment tekstu.
                            """
                            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Podyktowane:\n{raw_transcript}"}], temperature=0.0)
                            
                            # Aktualizujemy tekst, NIE WZBUDZAJĄC st.rerun() aby nie zabić stanu dolnego okienka
                            st.session_state["editable_report_area"] = response.choices[0].message.content.strip()
                            st.success("✅ Fragment wygenerowany pomyślnie! Wykonaj ewentualne poprawki, skopiuj go i zastąp odpowiedni tekst w schemacie na dole.")
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
    
    # 1. OKIENKO - TYLKO REZULTAT DYKTOWANIA
    st.markdown("<h4 style='color: #135c7e;'>📝 Zredagowany fragment (z notatki głosowej):</h4>", unsafe_allow_html=True)
    st.text_area("Wynik AI", key="editable_report_area", height=150, placeholder="Tutaj pojawi się zredagowany tekst TYLKO dla tych narządów, o których podyktujesz...", label_visibility="collapsed")
    
    st.markdown("---")

    # 2. OKIENKO - TWÓJ PEŁNY SCHEMAT ZDROWY (DO EDYCJI I ZAPISU)
    st.markdown("<h4 style='color: #135c7e;'>📄 Twój bazowy schemat (pełny raport do złożenia):</h4>", unsafe_allow_html=True)
    st.caption("Wklej zredagowany fragment z góry w odpowiednie miejsce poniżej (zastępując zdrowy opis chorego narządu).")
    
    st.text_area("Twój pełny raport", key="full_report_mode1", height=450, label_visibility="collapsed")

    if st.button("💾 Zapisz ten pełny opis do historii", key="save_btn_tab1"):
        add_to_history(st.session_state["full_report_mode1"])
        st.success("Zapisano badanie do paska bocznego!")


# ==========================================
# TRYB 2: TABELA WYMIARÓW + PATOLOGIE
# ==========================================
elif tryb == "📏 TRYB 2: Tabela Wymiarów":
    st.subheader("Wpisz wymiary i zaznacz patologie z bazy")
    st.caption("Wybierz gotową patologię dla narządu. Jeśli pole wymiarów będzie puste, aplikacja wstawi normę.")
    
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
    if v_nl or v_np:
        v_nerki = f"lewa ok. {v_nl or '...'} cm, prawa ok. {v_np or '...'} cm"
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

    pat_pecherz_options = [
        "Prawidłowy (Norma)",
        "Słabo wypełniony pęcherz",
        "Zagęszczony mocz",
        "Ostre zapalenie pęcherza moczowego",
        "Przewlekłe zapalenie pęcherza",
        "Osad w pęcherzu",
        "Kamienie w pęcherzu",
        "Neo pęcherza"
    ]
    pat_macica_options = [
        "Prawidłowy / Fizjologiczny (Norma)",
        "Macica - ruja",
        "Ropne zapalenie macicy",
        "Śluzo/wodomacicze"
    ]
    pat_prostata_options = [
        "Prawidłowy / Fizjologiczny (Norma)",
        "Przerost prostaty",
        "Wnętrostwo",
        "Guz jądra"
    ]

    with st.container(border=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            sel_pecherz = st.selectbox("Pęcherz moczowy - Stan:", pat_pecherz_options)
        with col_p2:
            sel_macica = st.selectbox("Układ rozrodczy (Samica) - Stan:", pat_macica_options[:4])
        with col_p3:
            sel_prostata = st.selectbox("Prostata / Jądra (Samiec) - Stan:", pat_prostata_options)
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            chk_klos = st.checkbox("Dodaj opis: Kłos (kończyna międzypalcowa)")
        with col_d2:
            chk_zmiana = st.checkbox("Dodaj opis: Zmiana podskórna (okolica pośladka)")

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

    jadra_sekcja = ""
    if is_samiec and is_niekastrowany and g_akt == "Pies":
        if sel_prostata == "Wnętrostwo":
            jadra_sekcja = "Lewe jądro w worku mosznowym, prawidłowej wielkości i kształtu, ok. 2,2 cm x 1,4 cm, miąższ normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrze bez uchwytnych zmian w budowie. Prawe jądro wnętrowskie, zlokalizowane w kanale pachwinowym, w około 1/3 doogonowej części jego długości/ na terenie jamy brzusznej, doogonowo od nerki lewej i śledziony, w sąsiedztwie rozwidlenia aorty. Jądro nieco pomniejszone, wielkości ok. 1,3 cm x 2,2 cm, prawidłowego kształtu, miąższ o nieco obniżonej echogeniczności, jednorodny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrze bez zmian."
        elif sel_prostata == "Guz jądra":
            jadra_sekcja = "Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, wielkości ok. 3 cm x 1,5 cm, miąższ obu jąder normoechogenny, w miąższu jądra prawego obecność zmiany ogniskowej, wielkości ok. 10 mm x 5 mm, dobrze odgraniczonej, o niejednorodnej strukturze, w przewadze hiperechogennej względem miąższu jądra, dość bogato unaczynionej centralnie i obwodowo, śródjądrze jądra prawego zatarte, lewego dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."
        else:
            jadra_sekcja = "Oba jądra w worku mosznowym, prawidłowej wielkości i kształtu, miąższ obu jąder normoechogenny, bez uchwytnych zmian ogniskowych, śródjądrze dobrze zaznaczone, najądrza bez uchwytnych zmian w budowie."

    txt_rodne = ""
    if g_akt == "Kot":
        if not is_samiec and "cała" in plec_akt.lower():
            if sel_macica == "Macica - ruja":
                txt_rodne = "Macica lekko rozpulchniona, na wysokości rogów śr. do ok. 5,5 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm, ściana lekko rozpulchniona do ok. 2,4 mm, prawidłowej budowy, warstwa śluzowa o nieco obniżonej echogeniczności, brak cech ropnego zapalenia w momencie badania. Jajniki lekko powiększone, wielkości ok. 14 mm x 7 mm, normoechogenne, w miąższu widoczne pojedyncze, hipoechogenne obszary, śr. do ok. 2 mm, odpowiadające prawidłowym komórkom jajnikowym, brak zmian guzowatych, brak uchwytnych zmian patologicznych."
            elif sel_macica == "Ropne zapalenie macicy":
                txt_rodne = "Macica powiększona, na wysokości rogów śr. do ok. 10 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm. Ściana prawidłowej grubości, o lekko nieregularnej powierzchni warstwy śluzowej, w świetle macicy zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            elif sel_macica == "Śluzo/wodomacicze":
                txt_rodne = "Macica powiększona, na wysokości rogów śr. ok. 10 mm, na wysokości szyjki macicy ok. 10 mm, na wysokości trzonu narządu ok. 7 mm. Ściana lekko pogrubiała do ok. 2,5 mm, o lekko podwyższonej echogeniczności, w świetle macicy nieco zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            else:
                txt_rodne = get_rodne_text(plec_akt, g_akt)
    else: # Pies
        if is_samiec:
            if sel_prostata == "Przerost prostaty":
                txt_rodne = "Gruczoł krokowy powiększony, wielkości ok. 4,3 cm x 3,4 cm, miąższ hiperechogenny, nieco niejednorodny, z licznymi, drobnymi torbielami prostymi, śr. do ok. 3 mm, bez uchwytnych zmian guzowatych, bez cech zapalenia ostrego."
            else:
                txt_rodne = get_rodne_text(plec_akt, g_akt)
        else:
            if sel_macica == "Macica - ruja":
                txt_rodne = "Macica lekko rozpulchniona, na wysokości rogów śr. do ok. 5,5 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm, ściana lekko rozpulchniona do ok. 2,4 mm, prawidłowej budowy, warstwa śluzowa o nieco obniżonej echogeniczności, brak cech ropnego zapalenia w momencie badania. Jajniki lekko powiększone, wielkości ok. 14 mm x 7 mm, normoechogenne, w miąższu widoczne pojedyncze, hipoechogenne obszary, śr. do ok. 2 mm, odpowiadające prawidłowym komórkom jajnikowym, brak zmian guzowatych, brak uchwytnych zmian patologicznych."
            elif sel_macica == "Ropne zapalenie macicy":
                txt_rodne = "Macica powiększona, na wysokości rogów śr. do ok. 10 mm, na wysokości szyjki macicy do ok. 10 mm, na wysokości trzonu narządu do ok. 7 mm. Ściana prawidłowej grubości, o lekko nieregularnej powierzchni warstwy śluzowej, w świetle macicy zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            elif sel_macica == "Śluzo/wodomacicze":
                txt_rodne = "Macica powiększona, na wysokości rogów śr. ok. 10 mm, na wysokości szyjki macicy ok. 10 mm, na wysokości trzonu narządu ok. 7 mm. Ściana lekko pogrubiała do ok. 2,5 mm, o lekko podwyższonej echogeniczności, w świetle macicy nieco zwiększona ilość aechogennego płynu. Jajniki niepowiększone, wielkości ok. 8 mm x 5 mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
            else:
                txt_rodne = get_rodne_text(plec_akt, g_akt)

    txt_ner = szablony['nerki'].format(nerki=v_nerki)
    txt_nadn = szablony['nadnercza'].format(nadn=v_nadn)
    txt_spl = szablony['sledziona'].format(spl=v_spl)
    txt_jel = szablony['jelita'].format(dwu=v_dwu, okr=v_okr)
    txt_wat = szablony['watroba'].format(pech_zol=v_pech_zol)
    txt_trz = szablony['trzustka'].format(trz=v_trz)

    report_sections = []
    
    if jadra_sekcja: report_sections.append(jadra_sekcja)
    report_sections.append(txt_pech)
    if txt_rodne: report_sections.append(txt_rodne)
    
    report_sections.extend([
        txt_ner,
        txt_nadn,
        txt_spl, 
        szablony['zoladek'].format(zol=v_zol), 
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
