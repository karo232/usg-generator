import streamlit as st
import streamlit.components.v1 as components

# 1. Konfiguracja strony
st.set_page_config(
    page_title="USG Vet Scans - Generator Opisów", 
    layout="wide", 
    page_icon="🩺"
)

# 2. Stylizacja CSS
st.markdown("""
    <style>
    :root {
        --primary-color: #0d5c58;
        --bg-color: #f8fafc;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0d5c58 0%, #147a74 100%);
        padding: 1.8rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 600;
    }
    .main-header p {
        color: #e2f1f0 !important;
        margin-top: 5px;
        margin-bottom: 0;
    }

    div.stButton > button {
        background-color: #0d5c58;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.3rem 0.8rem;
        font-size: 0.85rem;
    }
    div.stButton > button:hover {
        background-color: #147a74;
        color: white;
    }

    .stRadio [role=radiogroup] {
        padding: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- BANER GŁÓWNY ---
st.markdown("""
    <div class="main-header">
        <h1>🩺 USG Vet Scans</h1>
        <p>Professional Veterinary Ultrasound Reporting System</p>
    </div>
""", unsafe_allow_html=True)

# --- PANEL BOCZNY ---
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

# WYBÓR TRYBU PRACY
tryb = st.radio(
    "Wybierz tryb pracy:",
    ["🎙️ TRYB 1: Dyktowanie swobodne", "📏 TRYB 2: Tabela wymiarów + Szybkie Patologie"],
    horizontal=True,
    key="tryb_pracy"
)

st.markdown("---")

# ==========================================
# TRYB 1: DYKTOWANIE SWOBODNE
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie swobodne":
    st.subheader("🎙️ Dyktowanie opisu badania")
    st.caption("Kliknij przycisk, aby rozpocząć dyktowanie. Upewnij się, że mówisz wyraźnie po polsku.")

    speech_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0; background: transparent; }
        .card { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; }
        .bar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
        .btn-start { background-color: #0d5c58; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; }
        .btn-stop { background-color: #dc2626; color: white; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; display: none; }
        .btn-copy { background-color: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; padding: 10px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; }
        .btn-clear { background-color: #fff; color: #64748b; border: 1px solid #cbd5e1; padding: 10px 14px; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; }
        .status { font-size: 13px; font-weight: 600; color: #64748b; }
        textarea { width: 100%; height: 220px; box-sizing: border-box; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 15px; line-height: 1.5; font-family: inherit; resize: vertical; outline: none; }
        textarea:focus { border-color: #0d5c58; }
    </style>
    </head>
    <body>
    <div class="card">
        <div class="bar">
            <button id="startBtn" class="btn-start" onclick="startRec()">🎙️ Zacznij mówić</button>
            <button id="stopBtn" class="btn-stop" onclick="stopRec()">⏹️ Zakończ dyktowanie</button>
            <button class="btn-copy" onclick="copyTxt()">📋 Skopiuj opis</button>
            <button class="btn-clear" onclick="clearTxt()">🗑️ Wyczyść</button>
            <span id="statusLabel" class="status">Gotowy</span>
        </div>
        <textarea id="outputBox" placeholder="Naciśnij 'Zacznij mówić' i dyktuj treść opisu USG..."></textarea>
    </div>

    <script>
        var recognition = null;
        var outputBox = document.getElementById('outputBox');
        var startBtn = document.getElementById('startBtn');
        var stopBtn = document.getElementById('stopBtn');
        var statusLabel = document.getElementById('statusLabel');

        function setupSpeech() {
            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                statusLabel.innerText = "⚠️ Użyj Google Chrome lub Microsoft Edge.";
                statusLabel.style.color = "#dc2626";
                return null;
            }
            var rec = new SpeechRecognition();
            rec.continuous = true;
            rec.interimResults = false;
            rec.lang = 'pl-PL';

            rec.onstart = function() {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
                statusLabel.innerText = "🔴 Słucham... Mów teraz";
                statusLabel.style.color = "#dc2626";
            };

            rec.onresult = function(event) {
                for (var i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        outputBox.value += event.results[i][0].transcript + ' ';
                    }
                }
            };

            rec.onerror = function(e) {
                statusLabel.innerText = "⚠️ Błąd: " + e.error;
                statusLabel.style.color = "#dc2626";
                resetBtns();
            };

            rec.onend = function() {
                resetBtns();
            };

            return rec;
        }

        function resetBtns() {
            startBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
            statusLabel.innerText = "⚪ Zakończono dyktowanie";
            statusLabel.style.color = "#64748b";
        }

        function startRec() {
            if (!recognition) recognition = setupSpeech();
            if (recognition) {
                try {
                    recognition.start();
                } catch(e) {
                    recognition.stop();
                    setTimeout(function(){ recognition.start(); }, 200);
                }
            }
        }

        function stopRec() {
            if (recognition) {
                recognition.stop();
            }
            resetBtns();
        }

        function copyTxt() {
            outputBox.select();
            document.execCommand('copy');
            statusLabel.innerText = "✅ Skopiowano do schowka!";
            statusLabel.style.color = "#16a34a";
        }

        function clearTxt() {
            outputBox.value = '';
            statusLabel.innerText = "Wyczyszczono";
            statusLabel.style.color = "#64748b";
        }
    </script>
    </body>
    </html>
    """
    
    components.html(speech_html, height=330)

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
    st.caption("Kliknij przycisk, aby automatycznie wstawić opis patologii lub wpisz własny tekst w pole obok.")

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
            return "Gruczoł krokowy niepowiększony, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia. Jądra w mosznie, prawidłowej wielkości i echogeniczności, miąższ jednorodny, bez zmian ogniskowych."
        elif plec_wybor == "Pies (samiec kastrowany)":
            return "Gruczoł krokowy niepowiększony, fizjologicznie zmniejszony (stan po kastracji), miąższ jednorodny, bez cech zapalenia. Stan po orchidektomii – brak jąder w mosznie."
        elif plec_wybor == "Suka (cała)":
            return "Macica niepowiększona. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
        else:
            return "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

    def get_nerki(pat, dl, dp):
        if pat:
            wymiary_txt = f", lewa ok. {dl} cm, prawa ok. {dp} cm" if (dl != "..." or dp != "...") else ""
            return f"Nerki prawidłowego kształtu{wymiary_txt}, {pat}. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."
        return f"Nerki prawidłowego kształtu, lewa około {dl} cm, prawa ok. {dp} cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

    def get_spleen(pat, d_spleen):
        if pat:
            gr_txt = f", grubości około {d_spleen} cm" if d_spleen != "..." else ""
            return f"Śledziona {pat}{gr_txt}, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."
        return f"Śledziona prawidłowej wielkości, grubości około {d_spleen} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

    def get_zoladek(d_zoladek):
        return f"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, pomiędzy fałdami gr. ok. {d_zoladek} mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

    def get_jelita(pat, d_dw, d_ok):
        if pat:
            return f"{pat}. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi."
        return f"Ściana dwunastnicy niepogrubiała, ok. {d_dw} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości, ok. {d_ok} mm i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi."

    def get_watroba(pat, d_pech):
        if pat:
            return f"Wątroba {pat}. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."
        return f"Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone. Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości, gr. ok. {d_pech} mm i echogeniczności, bez uchwytnych złogów w świetle. Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    def get_trzustka(pat, d_trz):
        if pat:
            return f"Trzustka {pat}. Przewód trzustkowy nieposzerzony."
        return f"Trzustka prawidłowej wielkości, gr. ok. {d_trz} mm i kształtu, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

    def get_plyn(pat):
        if pat:
            return f"{pat}"
        return "Brak wolnego płynu w jamie brzusznej."

    report_sections = [
        get_pecherz(pecherz_pat, val_pecherz),
        get_rodne_prostata(plec),
        get_nerki(nerki_pat, val_nerka_l, val_nerka_p),
        "Nadnercza prawidłowej wielkości i kształtu, bez uchwytnych zmian w budowie.",
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
    st.subheader("📋 Wygenerowany Opis USG:")
    st.caption("Użyj ikony 📋 w prawym górnym rogu poniższego pola, aby natychmiast skopiować cały raport.")
    st.code(final_report_text, language=None)
