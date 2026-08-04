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
    page_title="USG Vet Scans - Generator Opisów", 
    layout="wide", 
    page_icon="🩺"
)

# === INICJALIZACJA SESSION STATE ===
if "editable_report_area" not in st.session_state:
    st.session_state["editable_report_area"] = ""

if "reports_history" not in st.session_state:
    st.session_state["reports_history"] = []

if "plec_pacjenta" not in st.session_state:
    st.session_state["plec_pacjenta"] = "Suka (kastrowana / kikut)"

if "last_mode2_hash" not in st.session_state:
    st.session_state["last_mode2_hash"] = ""

if "last_mode3_hash" not in st.session_state:
    st.session_state["last_mode3_hash"] = ""

if "processed_audio_size" not in st.session_state:
    st.session_state["processed_audio_size"] = 0

# === ODCZYT KLUCZA Z SECRETS ===
api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip().strip('"').strip("'")

client = None
if HAS_OPENAI and api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# 2. Stylizacja CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0d5c58 0%, #147a74 100%);
        padding: 1.8rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.1rem; }
    .main-header p { color: #e2f1f0 !important; margin-top: 5px; }
    div.stButton > button {
        background-color: #0d5c58; color: white; border-radius: 6px; border: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🩺 USG Vet Scans</h1>
        <p>Professional Veterinary Ultrasound Reporting System</p>
    </div>
""", unsafe_allow_html=True)

# Funkcja pomocnicza do zapisywania w historii
def add_to_history(report_text):
    if report_text and report_text.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        snippet = report_text[:35].replace("\n", " ") + "..."
        entry = {
            "time": timestamp,
            "snippet": snippet,
            "text": report_text
        }
        st.session_state["reports_history"].insert(0, entry)
        st.session_state["reports_history"] = st.session_state["reports_history"][:10]

# GŁÓWNA FUNKCJA DOPASOWUJĄCA UKŁAD ROZRODCZY
def get_rodne_text(plec_wybor):
    p = str(plec_wybor).lower()
    if "niekastrowany" in p:
        return "Gruczoł krokowy niepowiększony, wielkości ok. ... cm x ... cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia."
    elif "samiec kastrowany" in p:
        return "Gruczoł krokowy obkurczony, hipoechogenny, bez zmian w budowie, typowy obraz pokastracyjny."
    elif "cała" in p:
        return "Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
    else: # Kikut
        return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

# ==========================================
# SIDEBAR: USTAWIENIA (Rysowane na górze)
# ==========================================
with st.sidebar:
    st.header("⚙️ Ustawienia Pacjenta")
    plec = st.radio(
        "Płeć i stan fizjologiczny:",
        [
            "Suka (kastrowana / kikut)", 
            "Suka (cała)", 
            "Pies (samiec niekastrowany)", 
            "Pies (samiec kastrowany)"
        ],
        key="plec_pacjenta"
    )
    dodaj_tarczyce = st.checkbox("Dodaj badanie tarczycy", value=False)

tryb = st.radio(
    "Wybierz tryb pracy:",
    [
        "🎙️ TRYB 1: Dyktowanie (AI)", 
        "📏 TRYB 2: Tabela wymiarów",
        "📝 TRYB 3: Wybór zmienionych narządów"
    ],
    horizontal=True,
    key="tryb_pracy"
)

st.markdown("---")

# ==========================================
# TRYB 1: DYKTOWANIE Z PEŁNYM ŚCISŁYM SZABLONEM
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie (AI)":
    st.subheader("🎙️ Swobodne dyktowanie badania z generacją wg Ścisłego Wzorca Medycznego")
    st.caption("Podyktuj obserwacje. AI wstawi je w dokładnie zdefiniowane, pełne akapity szablonowe.")

    audio_recorded = st.audio_input("Nagraj notatkę głosową USG", key="audio_input_widget")

    if audio_recorded is not None:
        current_audio_size = len(audio_recorded.getvalue())
        
        # Przetwarzaj tylko, jeśli nagrano nowe audio (wielkość pliku jest inna)
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
                            prompt_vet = (
                                "Transkrypcja opisu badania USG weterynaryjnego. Słownictwo: wątroba, śledziona, nerki, "
                                "trzustka, pęcherz moczowy, jelita, dwunastnica, żołądek, okrężnica, nadnercza, prostata, "
                                "macica, jajniki, polipy, miedniczki, mineralizacje, zachyłki, jelito czcze, BŚO."
                            )
                            res = client.audio.transcriptions.create(
                                model="whisper-1", file=audio_file, language="pl", prompt=prompt_vet
                            )
                            raw_transcript = res.text.strip() if res.text else ""

                    except Exception as e:
                        st.error(f"❌ Błąd transkrypcji: {e}")
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.remove(tmp_path)

                if raw_transcript and len(raw_transcript) > 2:
                    with st.spinner("🩺 KROK 2/2: Generowanie pełnych akapitów opisu USG..."):
                        try:
                            szablon_rozrodczy = get_rodne_text(st.session_state["plec_pacjenta"])
                            
                            system_prompt = f"""
Jesteś profesjonalnym edytorem raportów USG weterynaryjnego.
Przekształć notatkę w PEŁNE AKAPITY MEDYCZNE wg wzorców.

KRYTYCZNA ZASADA PŁCI (Pacjent: {st.session_state["plec_pacjenta"]}):
Dla układu rozrodczego / prostaty MUSISZ UŻYĆ DOKŁADNIE PONIŻSZEGO WZORCA:
"{szablon_rozrodczy}"

MATRYCE AKAPITÓW DLA POZOSTAŁYCH NARZĄDÓW:

PĘCHERZ MOCZOWY:
"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. [WYMIAR] mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

NERKI:
"Nerki prawidłowego kształtu i wielkości około [DODAJ WYMIARY, np. 4,9 cm x 2,9 cm, prawa ok. 4,8 cm x 2,8 cm], kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

NADNERCZA:
"Nadnercza prawidłowej wielkości i kształtu, grubości około [WYMIAR] mm, bez uchwytnych zmian w budowie."

ŚLEDZIONA:
"Śledziona prawidłowej wielkości, grubości około [WYMIAR] cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

ŻOŁĄDEK:
"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. [WYMIAR] mm, okolica odźwiernika bez zmian, ściana gr. ok. [WYMIAR] mm, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

JELITA I DWUNASTNICA:
"Ściana dwunastnicy niepogrubiała, ok. [WYMIAR] mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. [WYMIAR] mm, okrężnica wypełniona uformowanymi masami kałowymi."

WĄTROBA I PĘCHERZYK ŻÓŁCIOWY:
"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. [WYMIAR] mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

TRZUSTKA:
"Trzustka prawidłowej wielkości i kształtu, gr. ok. [WYMIAR] mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

WĘZŁY CHŁONNE:
"Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie."

WOLNY PŁYN:
"Brak wolnego płynu w jamie brzusznej."

{( 'TARCZYCA:\n"TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."' if dodaj_tarczyce else '' )}

ZASADY WYLOTOWE: Oddzielaj narządy nową linią. Zwracaj WYŁĄCZNIE czysty tekst opisu medycznego.
"""
                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": f"Podyktowane:\n{raw_transcript}"}
                                ],
                                temperature=0.0
                            )
                            
                            corrected_text = response.choices[0].message.content.strip()
                            st.session_state["editable_report_area"] = corrected_text
                            st.success("✅ Generowanie wzorcowego raportu zakończone!")

                        except Exception as e:
                            st.session_state["editable_report_area"] = raw_transcript
                            st.warning(f"⚠️ Błąd generatora: {e}")
            else:
                st.error("⚠️ Brak aktywnego klienta OpenAI API.")
    else:
        st.session_state["processed_audio_size"] = 0 # reset po usunięciu nagrania

    st.markdown("---")
    if st.button("📋 Zapisz ten opis w historii (Tryb 1)"):
        add_to_history(st.session_state["editable_report_area"])
        st.success("Zapisano badanie do historii!")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (edytowalny tekst ciągły):",
        key="editable_report_area",
        placeholder="Tutaj pojawi się gotowy opis medyczny...",
        height=350
    )

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(st.session_state["editable_report_area"], language=None)

# ==========================================
# TRYB 2: TABELA WYMIARÓW + SZYBKIE PATOLOGIE
# ==========================================
elif tryb == "📏 TRYB 2: Tabela wymiarów":
    st.subheader("📏 Tabela Wymiarów (dla opisów prawidłowych i odchyleń)")
    
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
        dim_pecherzyk = st.text_input("Pęcherzyk żółciowy ściana (mm)", placeholder="np. 1.1")

    val_pecherz = dim_pecherz.strip() if dim_pecherz.strip() else "..."
    val_nerka_l = dim_nerka_l.strip() if dim_nerka_l.strip() else "..."
    val_nerka_p = dim_nerka_p.strip() if dim_nerka_p.strip() else "..."
    val_spleen = dim_spleen.strip() if dim_spleen.strip() else "..."
    val_zoladek = dim_zoladek.strip() if dim_zoladek.strip() else "..."
    val_dwunastnica = dim_dwunastnica.strip() if dim_dwunastnica.strip() else "..."
    val_okresnica = dim_okresnica.strip() if dim_okresnica.strip() else "..."
    val_trzustka = dim_trzustka.strip() if dim_trzustka.strip() else "..."
    val_pecherzyk = dim_pecherzyk.strip() if dim_pecherzyk.strip() else "..."

    st.markdown("---")
    st.subheader("📝 Odchylenia i Patologie (Szybkie Przyciski)")

    for key in ['pecherz_pat', 'nerki_pat', 'spleen_pat', 'jelita_pat', 'watroba_pat', 'trzustka_pat', 'plyn_pat']:
        if key not in st.session_state:
            st.session_state[key] = ""

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Pęcherz moczowy**")
        if st.button("➕ Zapalenie / Pogrubiała ściana / Osad"):
            st.session_state['pecherz_pat'] = "zmiernie wypełniony, ściana pogrubiała do 3 mm z cechami zapalenia, w świetle widoczny mierny osad"
        pecherz_pat = st.text_area("Pęcherz odchylenia", key='pecherz_pat', height=70, label_visibility="collapsed")

        st.markdown("**Nerki**")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            if st.button("➕ Przebudowa zwyrodnieniowa"):
                st.session_state['nerki_pat'] = "przebudowa zwyrodnieniowo-zapalna, zatarta granica korowo-rdzeniowa"
        with col_n2:
            if st.button("➕ Ogniska pozawałowe"):
                st.session_state['nerki_pat'] = "z widocznymi drobnymi ogniskami pozawałowymi w korze"
        nerki_pat = st.text_area("Nerki odchylenia", key='nerki_pat', height=70, label_visibility="collapsed")

        st.markdown("**Śledziona**")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("➕ Niejednorodna"):
                st.session_state['spleen_pat'] = "miąższ niejednorodny, drobno- i gruboośrodkowo przebudowany"
        spleen_pat = st.text_area("Śledziona odchylenia", key='spleen_pat', height=70, label_visibility="collapsed")

    with c2:
        st.markdown("**Dwunastnica i Jelita**")
        if st.button("➕ Cechy IBD / Pogrubienie ściany"):
            st.session_state['jelita_pat'] = "pętla jelita czczego pogrubiała do 5.9 mm na dł. 4 cm z zatartą warstwowością, węzły krezkowe odczynowe (cechy IBD)"
        jelita_pat = st.text_area("Jelita odchylenia", key='jelita_pat', height=70, label_visibility="collapsed")

        st.markdown("**Wątroba i Pęcherzyk**")
        if st.button("➕ Hepatomegalia + Ogniska hipo"):
            st.session_state['watroba_pat'] = "powiększona, miąższ z obecnością rozsianych ognisk hipoechogennych do 5.2 mm, zarys regularny"
        watroba_pat = st.text_area("Wątroba odchylenia", key='watroba_pat', height=70, label_visibility="collapsed")

        st.markdown("**Trzustka & Wolny Płyn**")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("➕ Zapalenie trzustki"):
                st.session_state['trzustka_pat'] = "lewy płat powiększony do 22 mm, obszar hipoechogennym 22x18.5 mm z miejscowym odczynem tłuszczowym"
        with col_t2:
            if st.button("➕ Wolny płyn"):
                st.session_state['plyn_pat'] = "Niewielki uogólniony odczyn zapalny tkanki tłuszczowej oraz niewielka ilość wolnego płynu."
        trzustka_pat = st.text_area("Trzustka odchylenia", key='trzustka_pat', height=70, label_visibility="collapsed")
        plyn_pat = st.text_area("Płyn odchylenia", key='plyn_pat', height=70, label_visibility="collapsed")

    def build_pecherz(pat, d_pech):
        if pat:
            return f"Pęcherz moczowy {pat}. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
        return f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {d_pech} mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

    def build_nerki(pat, dl, dp):
        if pat:
            wymiary_txt = f", lewa ok. {dl} cm, prawa ok. {dp} cm" if (dl != "..." or dp != "...") else ""
            return f"Nerki prawidłowego kształtu{wymiary_txt}, {pat}. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
        return f"Nerki prawidłowego kształtu i wielkości około {dl} cm x {dp} cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

    def build_spleen(pat, d_spleen):
        if pat:
            gr_txt = f", grubości około {d_spleen} cm" if d_spleen != "..." else ""
            return f"Śledziona {pat}{gr_txt}, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
        return f"Śledziona prawidłowej wielkości, grubości około {d_spleen} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

    def build_zoladek(d_zoladek):
        return f"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. {d_zoladek} mm, okolica odźwiernika bez zmian, ściana gr. ok. ... mm, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

    def build_jelita(pat, d_dw, d_ok):
        if pat:
            return f"{pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. {d_ok} mm, okrężnica wypełniona uformowanymi masami kałowymi."
        return f"Ściana dwunastnicy niepogrubiała, ok. {d_dw} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. {d_ok} mm, okrężnica wypełniona uformowanymi masami kałowymi."

    def build_watroba(pat, d_pech):
        if pat:
            return f"Wątroba {pat}. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
        return f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. {d_pech} mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    def build_trzustka(pat, d_trz):
        if pat:
            return f"Trzustka {pat}. Przewód trzustkowy nieposzerzony."
        return f"Trzustka prawidłowej wielkości i kształtu, gr. ok. {d_trz} mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

    def build_plyn(pat):
        if pat:
            return f"{pat}"
        return "Brak wolnego płynu w jamie brzusznej."

    report_sections = [
        build_pecherz(pecherz_pat, val_pecherz),
        get_rodne_text(st.session_state["plec_pacjenta"]),
        build_nerki(nerki_pat, val_nerka_l, val_nerka_p),
        "Nadnercza prawidłowej wielkości i kształtu, grubości około ... mm, bez uchwytnych zmian w budowie.",
        build_spleen(spleen_pat, val_spleen),
        build_zoladek(val_zoladek),
        build_jelita(jelita_pat, val_dwunastnica, val_okresnica),
        build_watroba(watroba_pat, val_pecherzyk),
        build_trzustka(trzustka_pat, val_trzustka),
        "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
        build_plyn(plyn_pat)
    ]
    
    if dodaj_tarczyce:
        report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")

    mode2_final_report = "\n\n".join(report_sections)
    
    if mode2_final_report != st.session_state.get("last_mode2_hash", ""):
        st.session_state["editable_report_area"] = mode2_final_report
        st.session_state["last_mode2_hash"] = mode2_final_report

    st.markdown("---")
    
    if st.button("📋 Zapisz ten opis w historii (Tryb 2)"):
        add_to_history(st.session_state["editable_report_area"])
        st.success("Zapisano badanie do historii!")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (edytowalny tekst ciągły):",
        key="editable_report_area",
        height=350
    )

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(st.session_state["editable_report_area"], language=None)

# ==========================================
# TRYB 3: INTELIGENTNY SZABLON (ZMIENIONE NARZĄDY)
# ==========================================
elif tryb == "📝 TRYB 3: Wybór zmienionych narządów":
    st.subheader("📝 Inteligentny Szablon (Nadpisywanie Zmian)")
    st.caption("Zaznacz narząd, w którym występują zmiany. Pojawi się pole wstępnie wypełnione tekstem z NORMĄ – wykasuj lub dopisz w nim to, co dotyczy patologii. Niezaznaczone narządy pozostają całkowicie zdrowe.")

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

    if dodaj_tarczyce:
        organs_defaults["Tarczyca"] = "TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."

    final_mode3_paragraphs = []
    st.markdown("---")
    
    for organ_name, default_text in organs_defaults.items():
        is_changed = st.checkbox(f"⚠️ Zmiany w narządzie: **{organ_name}**", key=f"chk_{organ_name}")
        if is_changed:
            custom_text = st.text_area(f"Edytuj poniższą normę dla narządu {organ_name}:", value=default_text, key=f"txt_{organ_name}", height=120)
            final_mode3_paragraphs.append(custom_text)
        else:
            final_mode3_paragraphs.append(default_text)

    mode3_final_report = "\n\n".join(final_mode3_paragraphs)

    if mode3_final_report != st.session_state.get("last_mode3_hash", ""):
        st.session_state["editable_report_area"] = mode3_final_report
        st.session_state["last_mode3_hash"] = mode3_final_report

    st.markdown("---")
    if st.button("📋 Zapisz ten opis w historii (Tryb 3)"):
        add_to_history(st.session_state["editable_report_area"])
        st.success("Zapisano badanie do historii!")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (edytowalny tekst ciągły):",
        key="editable_report_area",
        height=350
    )

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(st.session_state["editable_report_area"], language=None)

# ==========================================
# GŁÓWNA ZMIANA: HISTORIA RYSOWANA NA SAMYM KOŃCU KODU
# Dzięki temu historia wie o wszystkich zmianach (jest 100% zsynchronizowana)
# ==========================================
with st.sidebar:
    st.markdown("---")
    st.header("📜 Historia ostatnich badań")
    
    if st.session_state["reports_history"]:
        for i, item in enumerate(st.session_state["reports_history"]):
            label = f"🕒 {item['time']} - {item['snippet']}"
            if st.button(label, key=f"hist_{i}"):
                st.session_state["editable_report_area"] = item["text"]
                st.rerun()

        if st.button("🗑️ Wyczyść historię"):
            st.session_state["reports_history"] = []
            st.rerun()
    else:
        st.caption("Brak zapisanych badań w obecnej sesji.")
