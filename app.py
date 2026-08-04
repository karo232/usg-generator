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

# Pamięć na historię ostatnich badań (maksymalnie 10)
if "reports_history" not in st.session_state:
    st.session_state["reports_history"] = []

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

# Funkcja pomocnicza do dodawania opisu do historii
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

# ==========================================
# SIDEBAR: USTAWIENIA + HISTORIA 10 BADAŃ
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

tryb = st.radio(
    "Wybierz tryb pracy:",
    ["🎙️ TRYB 1: Dyktowanie głosem (Whisper + Ścisły Szablon Medyczny)", "📏 TRYB 2: Tabela wymiarów + Szybkie Patologie"],
    horizontal=True,
    key="tryb_pracy"
)

st.markdown("---")

# ==========================================
# TRYB 1: DYKTOWANIE Z PEŁNYM ŚCISŁYM SZABLONEM
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie głosem (Whisper + Ścisły Szablon Medyczny)":
    st.subheader("🎙️ Swobodne dyktowanie badania z generacją wg Ścisłego Wzorca Medycznego")
    st.caption("Podyktuj obserwacje. AI wstawi je w dokładnie zdefiniowane, pełne akapity szablonowe.")

    audio_recorded = st.audio_input("Nagraj notatkę głosową USG", key="audio_input_widget")

    if audio_recorded is not None:
        if client is not None:
            tmp_path = None
            raw_transcript = ""
            
            with st.spinner("🧠 KROK 1/2: Rozpoznawanie mowy (Whisper)..."):
                try:
                    file_ext = ".wav"
                    if hasattr(audio_recorded, "name") and audio_recorded.name:
                        ext = os.path.splitext(audio_recorded.name)[1]
                        if ext:
                            file_ext = ext
                    elif hasattr(audio_recorded, "type") and "webm" in audio_recorded.type:
                        file_ext = ".webm"

                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                        tmp_file.write(audio_recorded.getvalue())
                        tmp_path = tmp_file.name

                    with open(tmp_path, "rb") as audio_file:
                        prompt_vet = (
                            "Transkrypcja opisu badania USG weterynaryjnego u psa lub kota. "
                            "Słownictwo: wątroba, śledziona, nerki, trzustka, pęcherz moczowy, "
                            "jelita, dwunastnica, żołądek, okrężnica, nadnercza, prostata, macica, jajniki, "
                            "polipy, miedniczki, mineralizacje, zachyłki, jelito czcze, BŚO."
                        )
                        res = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="pl",
                            prompt=prompt_vet
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
                        system_prompt = f"""
Jesteś profesjonalnym edytorem raportów USG weterynaryjnego.
Twoim zadaniem jest przekształcenie podyktowanej notatki lekarza w PEŁNE, BOGATE AKAPITY MEDYCZNE wg podanych niżej wzorców.

BEZWZGLĘDNA ZASADA PŁCI:
Pacjent to: {plec}. 
Musisz użyć opisu układu rozrodczego ściśle dopasowanego do opcji: {plec}.

MATRYCE AKAPITÓW DLA NARZĄDÓW:

PĘCHERZ MOCZOWY:
"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. [WYMIAR] mm, prawidłowej budowy, bez cech zapalenia ostrego [LUB OPIS ZAPALENIA], mocz [STAN MOCZU, np. aechogenny / lekko zagęszczony], bez uchwytnych mineralizacji formujących kamienie/osad [LUB OPIS MINERALIZACJI], lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

UKŁAD ROZRODCZY / PROSTATA (płeć wyboru: {plec}):
- Jeśli "Pies (samiec niekastrowany)":
"Gruczoł krokowy niepowiększony, normoechogenny, jednorodny echogenicznie, bez zmian guzowatych, bez cech zapalenia [LUB OPIS PATOLOGII].
Jądra prawidłowej wielkości i kształtu, miąższ obu jąder bez uchwytnych zmian w budowie [LUB OPIS PATOLOGII]."
- Jeśli "Pies (samiec kastrowany)":
"Gruczoł krokowy obkurczony, hipoechogenny, bez zmian w budowie, typowy obraz pokastracyjny."
- Jeśli "Suka (cała)":
"Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
- Jeśli "Suka (kastrowana / kikut)":
"Kikut macicy, loże po jajnikach bez uchwytnych zmian."

NERKI:
"Nerki prawidłowego kształtu i wielkości [EWENTUALNIE DODAJ WYMIARY: lewa ok. ... cm x ... cm, prawa ok. ... cm x ... cm], kora i rdzeń prawidłowej echogeniczności [LUB OPIS ECHOGENICZNOŚCI KORY], nerki o wyraźnej granicy korowo-rdzeniowej [LUB LEKKO ZATARTEJ], stosunek obu warstw zachowany [LUB POGRUBIAŁA KORA]. [DODAJ OPIS PRZEBUDOWY, NP. cechy umiarkowanej przebudowy przewlekłej, w typie zwyrodnieniowo-pozapalnym]. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone [LUB ZACHYŁKI MIEDNICZEK NIEPOSZERZONE], bez uchwytnych złogów w świetle [LUB OPIS MINERALIZACJI W ZACHYŁKACH]. Moczowody bez uchwytnych zmian w budowie."

NADNERCZA:
"Nadnercza prawidłowej wielkości i kształtu [DODAJ WYMIAR, NP. grubości około 3,7-3,9 mm], bez uchwytnych zmian w budowie [LUB DODAJ ZWŁÓKNIENIA, NP. z drobnymi ogniskami zwłóknień, poza tym bez uchwytnych zmian w budowie]."

ŚLEDZIONA:
"Śledziona prawidłowej wielkości [LUB LEKKO POWIĘKSZONA], grubości około [WYMIAR] cm na wysokości trzonu narządu, jednorodna echogenicznie, miąższ drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

ŻOŁĄDEK:
"Żołądek nieco poszerzony [LUB OBKURCZONY], w świetle nieco zwiększona ilość płynnej treści i gazu, ściana o zachowanej warstwowości, na wysokości dna żołądka o prawidłowej grubości około [WYMIAR] mm, w trzonie [OPIS GRUBOŚCI TRZONU, NP. pogrubiała do ok. 3,1 mm, warstwa podśluzowa lekko pogrubiała, jak zapalnie przewlekle, z niewielkim zaostrzeniem], okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana [LUB LEKKO SPOWOLNIONA]."

JELITA I DWUNASTNICA:
"Ściana dwunastnicy niepogrubiała, ok. [WYMIAR] mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa [LUB LEKKO SPOWOLNIONA]. [JEŚLI OPISANO PATOLOGIĘ JELITA CZCZEGO, DODAJ FULL AKAPIT: W śródbrzuszu obecność pętli jelita cienkiego o wyraźnie pogrubiałej ścianie do ok. ... mm na dł. ok. ... cm, odcinkowo o zatartej warstwowości, z pogrubiałą warstwą mięśniową do ... mm, w świetle płynna zawartość, wokół ostry odczyn zapalny – w diagnostyce różnicowej należy brać pod uwagę ostre odcinkowe zapalenie jelita czczego, ew. przebudowę o podłożu rozrostowym – sugerowana kontrola USG za ok. 7 dni]. Pozostałe jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa [LUB Z DYSKRETNYMI ZMIANAMI ZAPALNYMI], perystaltyka zachowana. Światło nieposzerzone. Węzły chłonne jelita czczego nieco przewlekle/pozapalnie przebudowane, śr. do ok. [WYMIAR] mm. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi."

WĄTROBA I PĘCHERZYK ŻÓŁCIOWY:
"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności [LUB POGRUBIAŁA DO ... mm Z CECHAMI ZAPALENIA I ZAGĘSZCZONĄ ŻÓŁCIĄ], bez cech niedrożności. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

TRZUSTKA:
"Trzustka prawidłowej wielkości i kształtu, gr. ok. [WYMIAR] mm w płacie lewym/prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności [LUB O NIECO OBNIŻONEJ ECHOGENICZNOŚCI Z CECHAMI PRZEBUDOWY PRZEWLEKŁEJ/POZAPALNEJ], bez cech zapalenia ostrego. Przewód trzustkowy [POSZERZONY DO ... mm / NIEPOSZERZONY], bez uchwytnych złogów w świetle."

WĘZŁY CHŁONNE:
"Pozostałe węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie."

WOLNY PŁYN:
"Brak wolnego płynu w jamie brzusznej."

{( 'TARCZYCA:\n"TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."' if dodaj_tarczyce else '' )}

ZASADY WYLOTOWE:
- Oddzielaj narządy nową linią.
- Zwracaj WYŁĄCZNIE czysty tekst opisu medycznego.
"""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Słowa podyktowane przez lekarza:\n{raw_transcript}"}
                            ],
                            temperature=0.0
                        )
                        
                        corrected_text = response.choices[0].message.content.strip()
                        st.session_state["editable_report_area"] = corrected_text
                        add_to_history(corrected_text)
                        st.success("✅ Generowanie wzorcowego raportu zakończone!")

                    except Exception as e:
                        st.session_state["editable_report_area"] = raw_transcript
                        st.warning(f"⚠️ Błąd generatora: {e}")
            else:
                st.warning("⚠️ Brak rozpoznanej mowy. Podyktuj wynik badania.")
        else:
            st.error("⚠️ Brak aktywnego klienta OpenAI API.")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (edytowalny tekst ciągły):",
        key="editable_report_area",
        placeholder="Tutaj pojawi się gotowy opis medyczny...",
        height=350
    )

    final_report_text = podyktowany_tekst if podyktowany_tekst else "Czekam na nagranie głosu..."

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(final_report_text, language=None)

# ==========================================
# TRYB 2: TABELA WYMIARÓW + SZYBKIE PATOLOGIE
# ==========================================
else:
    st.subheader("📏 Tabela Wymiarów (dla opisów prawidłowych i odchyleń)")
    st.caption("Wpisz cyfry wymiarów lub wybierz patologię z przycisków. Wybór płci z panelu bocznego automatycznie ustala tekst rozrodu.")
    
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

    val_pecherz = dim_pecherz.strip() if dim_pecherz.strip() else None
    val_nerka_l = dim_nerka_l.strip() if dim_nerka_l.strip() else None
    val_nerka_p = dim_nerka_p.strip() if dim_nerka_p.strip() else None
    val_spleen = dim_spleen.strip() if dim_spleen.strip() else None
    val_zoladek = dim_zoladek.strip() if dim_zoladek.strip() else None
    val_dwunastnica = dim_dwunastnica.strip() if dim_dwunastnica.strip() else None
    val_okresnica = dim_okresnica.strip() if dim_okresnica.strip() else None
    val_trzustka = dim_trzustka.strip() if dim_trzustka.strip() else None
    val_pecherzyk = dim_pecherzyk.strip() if dim_pecherzyk.strip() else None

    st.markdown("---")
    st.subheader("📝 Odchylenia i Patologie (Szybkie Przyciski)")

    for key in ['pecherz_pat', 'nerki_pat', 'spleen_pat', 'jelita_pat', 'watroba_pat', 'trzustka_pat', 'plyn_pat']:
        if key not in st.session_state:
            st.session_state[key] = ""

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Pęcherz moczowy**")
        if st.button("➕ Zapalenie / Pogrubiała ściana / Osad"):
            st.session_state['pecherz_pat'] = "ściana pogrubiała, z cechami zapalenia ostrego, mocz z widocznym miernym osadem"
        pecherz_pat = st.text_area("Pęcherz odchylenia", key='pecherz_pat', height=70, label_visibility="collapsed")

        st.markdown("**Nerki**")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            if st.button("➕ Przebudowa zwyrodnieniowa"):
                st.session_state['nerki_pat'] = "cechy umiarkowanej przebudowy przewlekłej, w typie zwyrodnieniowo-pozapalnym, zatarta granica korowo-rdzeniowa"
        with col_n2:
            if st.button("➕ Drobne mineralizacje"):
                st.session_state['nerki_pat'] = "w zachyłkach obecne drobne mineralizacje, ale bez cech niedrożności"
        nerki_pat = st.text_area("Nerki odchylenia", key='nerki_pat', height=70, label_visibility="collapsed")

        st.markdown("**Śledziona**")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("➕ Powiększona / Niejednorodna"):
                st.session_state['spleen_pat'] = "lekko powiększona, miąższ niejednorodny, drobno- i gruboośrodkowo przebudowany"
        with col_s2:
            if st.button("➕ Susp. chłoniak"):
                st.session_state['spleen_pat'] = "powiększona, miąższ tarczyowato przebudowany z licznymi ogniskami hipoechogennymi (susp. chłoniak)"
        spleen_pat = st.text_area("Śledziona odchylenia", key='spleen_pat', height=70, label_visibility="collapsed")

    with c2:
        st.markdown("**Dwunastnica i Jelita**")
        if st.button("➕ Cechy IBD / Zapalenie jelita czczego"):
            st.session_state['jelita_pat'] = "W śródbrzuszu obecność pętli jelita cienkiego o wyraźnie pogrubiałej ścianie do 5.9 mm na dł. ok. 4 cm, z ostrym odczynem zapalnym (ostre odcinkowe zapalenie jelita czczego)"
        jelita_pat = st.text_area("Jelita odchylenia", key='jelita_pat', height=70, label_visibility="collapsed")

        st.markdown("**Wątroba i Pęcherzyk**")
        if st.button("➕ Pęcherzyk: Polipy / Śluz / Zagęszczony"):
            st.session_state['watroba_pat'] = "Pęcherzyk żółciowy z obecnością zmian w typie polipów, ściana lekko pogrubiała, niewielka ilość zagęszczonej żółci w świetle"
        watroba_pat = st.text_area("Wątroba odchylenia", key='watroba_pat', height=70, label_visibility="collapsed")

        st.markdown("**Trzustka & Wolny Płyn**")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("➕ Przebudowa pozapalna"):
                st.session_state['trzustka_pat'] = "miąższ o nieco obniżonej echogeniczności, z cechami umiarkowanej przebudowy przewlekłej/pozapalnej, przewód poszerzony do 2.8 mm"
        with col_t2:
            if st.button("➕ Wolny płyn + Odczyn"):
                st.session_state['plyn_pat'] = "Niewielki uogólniony odczyn zapalny tkanki tłuszczowej oraz niewielka ilość wolnego płynu w przestrzeni międzypętlowej."
        trzustka_pat = st.text_area("Trzustka odchylenia", key='trzustka_pat', height=70, label_visibility="collapsed")
        plyn_pat = st.text_area("Płyn odchylenia", key='plyn_pat', height=70, label_visibility="collapsed")

    # PRECYZYJNA LOGIKA GENEROWANIA AKAPITÓW W TRYBIE 2 (ŚCIŚLE UZWGLĘDNIAJĄCA PŁEĆ Pacjenta)
    def build_pecherz(pat, d_pech):
        dim_txt = f" gr. ok. {d_pech} mm" if d_pech else ""
        if pat:
            return f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana{dim_txt}, {pat}, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
        return f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana{dim_txt}, prawidłowej budowy, bez cech zapalenia ostrego, mocz aechogenny, bez uchwytnych mineralizacji formujących kamienie/osad, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

    def build_rodne_prostata(plec_wybor):
        if plec_wybor == "Pies (samiec niekastrowany)":
            return "Gruczoł krokowy niepowiększony, normoechogenny, jednorodny echogenicznie, bez zmian guzowatych, bez cech zapalenia.\nJądra prawidłowej wielkości i kształtu, miąższ obu jąder bez uchwytnych zmian w budowie."
        elif plec_wybor == "Pies (samiec kastrowany)":
            return "Gruczoł krokowy obkurczony, hipoechogenny, bez zmian w budowie, typowy obraz pokastracyjny."
        elif plec_wybor == "Suka (cała)":
            return "Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
        else: # Suka kastrowana
            return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

    def build_nerki(pat, dl, dp):
        wymiary_txt = ""
        if dl and dp:
            wymiary_txt = f", lewa ok. {dl} cm, prawa ok. {dp} cm"
        elif dl:
            wymiary_txt = f", lewa ok. {dl} cm"
        elif dp:
            wymiary_txt = f", prawa ok. {dp} cm"

        if pat:
            return f"Nerki prawidłowego kształtu i wielkości{wymiary_txt}, {pat}. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone. Moczowody bez uchwytnych zmian w budowie."
        return f"Nerki prawidłowego kształtu i wielkości{wymiary_txt}, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, zachyłki miedniczek nerkowych nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

    def build_spleen(pat, d_spleen):
        dim_txt = f", grubości około {d_spleen} cm na wysokości trzonu narządu" if d_spleen else ""
        if pat:
            return f"Śledziona {pat}{dim_txt}, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
        return f"Śledziona prawidłowej wielkości{dim_txt}, jednorodna echogenicznie, miąższ drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

    def build_zoladek(d_zoladek):
        dim_txt = f", na wysokości dna gr. ok. {d_zoladek} mm" if d_zoladek else ""
        return f"Żołądek obkurczony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości{dim_txt}, okolica odźwiernika bez zmian, brak cech zapalenia. Układ warstwowy zachowany, perystaltyka zachowana."

    def build_jelita(pat, d_dw, d_ok):
        dw_txt = f", ok. {d_dw} mm" if d_dw else ""
        ok_txt = f", ok. {d_ok} mm" if d_ok else ""
        if pat:
            return f"Ściana dwunastnicy niepogrubiała{dw_txt}, warstwowość zachowana, perystaltyka prawidłowa. {pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości{ok_txt}, okrężnica wypełniona uformowanymi masami kałowymi."
        return f"Ściana dwunastnicy niepogrubiała{dw_txt}, warstwowość zachowana, światło nieposzerzone, wypełnione niewielką ilością płynnej treści, perystaltyka prawidłowa. Reszta jelit cienkich o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości{ok_txt}, okrężnica wypełniona uformowanymi masami kałowymi."

    def build_watroba(pat, d_pech):
        pech_txt = f", ściana gr. ok. {d_pech} mm" if d_pech else ""
        if pat:
            return f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. {pat}{pech_txt}, bez cech niedrożności. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
        return f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości{pech_txt} i echogeniczności, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    def build_trzustka(pat, d_trz):
        dim_txt = f", gr. ok. {d_trz} mm w płacie lewym" if d_trz else ""
        if pat:
            return f"Płaty trzustki prawidłowej wielkości{dim_txt}, {pat}. Przewód trzustkowy bez złogów."
        return f"Płaty trzustki prawidłowej wielkości i kształtu{dim_txt}, struktura niezmieniona, lokalizacja prawidłowa, miąższ izoechogeniczny z otaczającym tłuszczem. Przewód trzustkowy nieposzerzony."

    def build_plyn(pat):
        if pat:
            return f"{pat}"
        return "Brak wolnego płynu w jamie brzusznej."

    # SKŁADANIE GENERATORA DLA TRYBU 2 DOKŁADNIE DLA WYBRANEJ PŁCI z SIDEBARA:
    report_sections = [
        build_pecherz(pecherz_pat, val_pecherz),
        build_rodne_prostata(plec),
        build_nerki(nerki_pat, val_nerka_l, val_nerka_p),
        "Pozostałe węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
        build_spleen(spleen_pat, val_spleen),
        build_zoladek(val_zoladek),
        build_jelita(jelita_pat, val_dwunastnica, val_okresnica),
        build_watroba(watroba_pat, val_pecherzyk),
        build_trzustka(trzustka_pat, val_trzustka),
        build_plyn(plyn_pat)
    ]
    
    if dodaj_tarczyce:
        report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")

    mode2_final_report = "\n\n".join(report_sections)
    
    st.markdown("---")
    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("🔄 Wygeneruj / Odśwież Raport"):
            st.session_state["editable_report_area"] = mode2_final_report
            st.rerun()
    with c_btn2:
        if st.button("📋 Zapisz ten opis w historii"):
            add_to_history(mode2_final_report)
            st.success("Zapisano badanie do historii!")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (edytowalny tekst ciągły):",
        value=mode2_final_report,
        key="editable_report_area_mode2",
        height=350
    )

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(podyktowany_tekst, language=None)
