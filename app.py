import streamlit as st
import tempfile
import os

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
    ["🎙️ TRYB 1: Dyktowanie głosem (Whisper + Oficjalny Szablon)", "📏 TRYB 2: Tabela wymiarów + Szybkie Patologie"],
    horizontal=True,
    key="tryb_pracy"
)

st.markdown("---")

# ==========================================
# TRYB 1: DYKTOWANIE Z OFICJALNYM SZYBKIM SZABLONEM AI
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie głosem (Whisper + Oficjalny Szablon)":
    st.subheader("🎙️ Swobodne dyktowanie badania z generacją wg Oficjalnego Wzorca")
    st.caption("Podyktuj swoje obserwacje. AI automatycznie zamieni je na kompletny opis USG w dokładnie takim formacie, jaki stosujesz.")

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
                            "jelita, dwunastnica, żołądek, okrężnica, nadnercza, prostata, macica, jajniki."
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

            # KROK 2: Generowanie raportu wg dokładnego Twojego wzorca
            if raw_transcript and len(raw_transcript) > 2:
                with st.spinner("🩺 KROK 2/2: Formowanie oficjalnego opisu USG wg wzorca..."):
                    try:
                        system_prompt = f"""
Jesteś systemem generowania raportów USG weterynaryjnego. Twoim zadaniem jest przekształcenie luźnej notatki lekarza w PEŁNY, PROFESJONALNY OPIS MEDYCZNY zachowujący dokładnie strukturę, frazy i format podany w poniższym wzorcu.

DANE PACJENTA:
- Płeć / stan: {plec}
- Badanie tarczycy: {"TAK" if dodaj_tarczyce else "NIE"}

OFICJALNY WZORIEC RAPORTU (Użyj tych dokładnych zdań dla narządów prawidłowych, a jeśli lekarz poda odchylenia/wymiary – dostosuj je merytorycznie wewnątrz struktury zdań):

1. Pęcherz moczowy:
"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. ... mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

2. Układ rozrodczy / Prostata (dobierz odpowiednio do płci pacjenta [{plec}]):
- Jeśli pies niekastrowany: "Gruczoł krokowy niepowiększony, wielkości ok. ... cm x ... cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia. Jądra w mosznie, prawidłowej wielkości i echogeniczności, miąższ jednorodny, bez zmian ogniskowych."
- Jeśli pies kastrowany: "Gruczoł krokowy niepowiększony, fizjologicznie zmniejszony (stan po kastracji), miąższ jednorodny, bez cech zapalenia. Stan po orchidektomii – brak jąder w mosznie."
- Jeśli suka cała: "Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
- Jeśli suka kastrowana / kikut: "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

3. Nerki:
"Nerki prawidłowego kształtu i wielkości około ... cm x ... cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

4. Nadnercza:
"Nadnercza prawidłowej wielkości i kształtu, grubości około ... mm, bez uchwytnych zmian w budowie."

5. Śledziona:
"Śledziona prawidłowej wielkości, grubości około ... cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

6. Żołądek:
"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. ... mm, okolica odźwiernika bez zmian, ściana gr. ok. ... mm, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

7. Jelita i Dwunastnica:
"Ściana dwunastnicy niepogrubiała, ok. ... mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. ... mm, okrężnica wypełniona uformowanymi masami kałowymi."

8. Wątroba i Pęcherzyk żółciowy:
"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. ... mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

9. Trzustka:
"Trzustka prawidłowej wielkości i kształtu, gr. ok. ... mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

10. Węzły chłonne:
"Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie."

11. Wolny płyn:
"Brak wolnego płynu w jamie brzusznej."

{( '12. Tarczyca:\n"TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych."' if dodaj_tarczyce else '' )}

ZASADY:
1. Rozwiń skróty myślowe lekarza do pełnych zdań z powyższego wzorca (jeśli narząd jest prawidłowy, wypisz pełen wzorcowy akapit).
2. Jeśli lekarz podał konkretne wymiary lub patologie, uzupełnij je w odpowiednich miejscach zdań.
3. Poszczególne narządy oddzielaj podwójną spacją / nową linią.
4. Zwróć WYŁĄCZNIE gotowy tekst raportu, bez żadnych wstępów i komentarzy czatbota.
"""

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Notatka lekarza:\n{raw_transcript}"}
                            ],
                            temperature=0.1
                        )
                        
                        corrected_text = response.choices[0].message.content.strip()
                        st.session_state["editable_report_area"] = corrected_text
                        st.success("✅ Wygenerowano pełny raport wg Twojego wzorca!")

                    except Exception as e:
                        st.session_state["editable_report_area"] = raw_transcript
                        st.warning(f"⚠️ Błąd generatora: {e}")
            else:
                st.warning("⚠️ Brak rozpoznanej mowy. Podyktuj wynik badania.")
        else:
            st.error("⚠️ Brak aktywnego klienta OpenAI API.")

    podyktowany_tekst = st.text_area(
        "Wygenerowany Raport USG (możesz edytować tekst poniżej):",
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
    st.subheader("📏 Tabela Wymiarów (dla opisów prawidłowych)")
    st.caption("Wpisz same cyfry. Puste pola zostaną zastąpione wielokropkiem (...) wewnątrz normy.")
    
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

    val_pecherz = dim_pecherz if dim_pecherz.strip() else "..."
    val_nerka_l = dim_nerka_l if dim_nerka_l.strip() else "..."
    val_nerka_p = dim_nerka_p if dim_nerka_p.strip() else "..."
    val_spleen = dim_spleen if dim_spleen.strip() else "..."
    val_zoladek = dim_zoladek if dim_zoladek.strip() else "..."
    val_dwunastnica = dim_dwunastnica if dim_dwunastnica.strip() else "..."
    val_okresnica = dim_okresnica if dim_okresnica.strip() else "..."
    val_trzustka = dim_trzustka if dim_trzustka.strip() else "..."
    val_pecherzyk = dim_pecherzyk if dim_pecherzyk.strip() else "..."

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
        with col_s2:
            if st.button("➕ Susp. chłoniak"):
                st.session_state['spleen_pat'] = "powiększona, miąższ tarczyowato przebudowany z licznymi ogniskami hipoechogennymi (susp. chłoniak)"
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
            if st.button("➕ Wolny płyn + Odczyn"):
                st.session_state['plyn_pat'] = "Niewielki uogólniony odczyn zapalny tkanki tłuszczowej oraz niewielka ilość wolnego płynu w przestrzeni międzypętlowej."
        trzustka_pat = st.text_area("Trzustka odchylenia", key='trzustka_pat', height=70, label_visibility="collapsed")
        plyn_pat = st.text_area("Płyn odchylenia", key='plyn_pat', height=70, label_visibility="collapsed")

    def get_pecherz(pat, d_pech):
        if pat:
            return f"Pęcherz moczowy {pat}. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."
        return f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {d_pech} mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

    def get_rodne_prostata(plec_wybor):
        if plec_wybor == "Pies (samiec niekastrowany)":
            return "Gruczoł krokowy niepowiększony, wielkości ok. ... cm x ... cm, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia. Jądra w mosznie, prawidłowej wielkości i echogeniczności, miąższ jednorodny, bez zmian ogniskowych."
        elif plec_wybor == "Pies (samiec kastrowany)":
            return "Gruczoł krokowy niepowiększony, fizjologicznie zmniejszony (stan po kastracji), miąższ jednorodny, bez cech zapalenia. Stan po orchidektomii – brak jąder w mosznie."
        elif plec_wybor == "Suka (cała)":
            return "Macica niepowiększona, na wysokości rogów śr. ok. ... mm, na wysokości szyjki macicy ok. ... mm, na wysokości trzonu narządu ok. ... mm. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, wielkości ok. ... mm x ... mm, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
        else:
            return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

    def get_nerki(pat, dl, dp):
        if pat:
            wymiary_txt = f", lewa ok. {dl} cm, prawa ok. {dp} cm" if (dl != "..." or dp != "...") else ""
            return f"Nerki prawidłowego kształtu{wymiary_txt}, {pat}. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
        return f"Nerki prawidłowego kształtu i wielkości około ... cm x ... cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

    def get_spleen(pat, d_spleen):
        if pat:
            gr_txt = f", grubości około {d_spleen} cm" if d_spleen != "..." else ""
            return f"Śledziona {pat}{gr_txt}, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
        return f"Śledziona prawidłowej wielkości, grubości około ... cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

    def get_zoladek(d_zoladek):
        return f"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, o prawidłowej grubości około ...-... mm, w trzonie ok. ... mm, okolica odźwiernika bez zmian, ściana gr. ok. ... mm, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

    def get_jelita(pat, d_dw, d_ok):
        if pat:
            return f"{pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi."
        return f"Ściana dwunastnicy niepogrubiała, ok. ... mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, ok. ... mm, okrężnica wypełniona uformowanymi masami kałowymi."

    def get_watroba(pat, d_pech):
        if pat:
            return f"Wątroba {pat}. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
        return f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości i echogeniczności, gr. ok. ... mm, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    def get_trzustka(pat, d_trz):
        if pat:
            return f"Trzustka {pat}. Przewód trzustkowy nieposzerzony."
        return f"Trzustka prawidłowej wielkości i kształtu, gr. ok. ... mm w płacie prawym, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

    def get_plyn(pat):
        if pat:
            return f"{pat}"
        return "Brak wolnego płynu w jamie brzusznej."

    report_sections = [
        get_pecherz(pecherz_pat, val_pecherz),
        get_rodne_prostata(plec),
        get_nerki(nerki_pat, val_nerka_l, val_nerka_p),
        "Nadnercza prawidłowej wielkości i kształtu, grubości około ... mm, bez uchwytnych zmian w budowie.",
        get_spleen(spleen_pat, val_spleen),
        get_zoladek(val_zoladek),
        get_jelita(jelita_pat, val_dwunastnica, val_okresnica),
        get_watroba(watroba_pat, val_pecherzyk),
        get_trzustka(trzustka_pat, val_trzustka),
        "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie.",
        get_plyn(plyn_pat)
    ]
    
    if dodaj_tarczyce:
        report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")

    final_report_text = "\n\n".join(report_sections)

    st.markdown("---")
    st.subheader("📋 Gotowy Raport USG (do skopiowania):")
    st.code(final_report_text, language=None)
