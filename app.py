import streamlit as st

# 1. Konfiguracja strony
st.set_page_config(
    page_title="USG Vet Scans - Generator Opisów", 
    layout="wide", 
    page_icon="🩺"
)

# 2. Stylizacja CSS nawiązująca do marki usgvetscans.pl
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
        border-radius: 8px;
        border: none;
        font-weight: 500;
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

# --- WYBÓR PŁCI I STANU W PANELU BOCZNYM ---
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

# WYBÓR TRYBU PRACY NA SAMEJ GÓRZE
tryb = st.radio(
    "Wybierz tryb pracy:",
    ["🎙️ TRYB 1: Dyktowanie swobodne (Puste tło)", "📏 TRYB 2: Tabela wymiarów dla opisów z szablonu"],
    horizontal=True,
    key="tryb_pracy"
)

st.markdown("---")

# ==========================================
# TRYB 1: DYKTOWANIE SWOBODNE
# ==========================================
if tryb == "🎙️ TRYB 1: Dyktowanie swobodne (Puste tło)":
    st.subheader("🎙️ Swobodne dyktowanie badania")
    st.caption("Kliknij w pole poniżej, włącz mikrofon na klawiaturze i podyktuj treść badania.")
    
    podyktowany_tekst = st.text_area(
        "Podyktuj treść badania głosem:",
        placeholder="np. Pęcherz moczowy miernie wypełniony ściana 2.5 mm, nerka lewa 4.5x2.8 cm z przebudową pozapalną...",
        height=250
    )
    
    if podyktowany_tekst:
        final_report_text = f"OPIS BADANIA USG:\n\n{podyktowany_tekst}"
    else:
        final_report_text = "Czekam na dyktowanie... (Wpisz lub podyktuj treść powyżej)"

# ==========================================
# TRYB 2: TABELA WYMIARÓW DLA NORM Z WIELOKROPKIEM + CHECKBOXY
# ==========================================
else:
    st.subheader("📏 Tabela Wymiarów")
    st.caption("Wpisz wymiary narządów. Puste pola zostaną zastąpione wielokropkiem (...) wewnątrz szablonu.")
    
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

    # Ustalanie dynamicznych wartości (wpisana wartość LUB '...')
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
    st.subheader("🧩 Szybkie odchylenia / Częste patologie:")
    st.caption("Zaznacz odpowiednie pole, aby automatycznie zmodyfikować opis danego narządu.")

    cb_col1, cb_col2, cb_col3 = st.columns(3)

    with cb_col1:
        osad_pecherz = st.checkbox("Pęcherz: Mierny osad w świetle")
        zapalenie_pecherza = st.checkbox("Pęcherz: Cechy zapalenia (pogrubiała ściana)")
        przebudowa_nerek = st.checkbox("Nerki: Mierna przebudowa pozapalna/zwyrodnieniowa")

    with cb_col2:
        niejednorodna_spleen = st.checkbox("Śledziona: Niejednorodny miąższ / drobne ogniska")
        stf_watroba = st.checkbox("Wątroba: Podwyższona echogeniczność (stłuszczenie)")
        zestalona_zolc = st.checkbox("Pęcherzyk żółciowy: Zagęszczona/zestalona żółć")

    with cb_col3:
        ibd_jelita = st.checkbox("Jelita: Cechy zapalenia przewlekłego (pogrubienie/odczyn)")
        odczyn_plyn = st.checkbox("Jam brzuszna: Niewielka ilość wolnego płynu")
        powiekszone_wezly = st.checkbox("Węzły chłonne: Odczynowo powiększone")

    # --- GENEROWANIE SZABLONÓW DLA NARZĄDÓW ---

    # Pęcherz
    if zapalenie_pecherza:
        pecherz_norma = f"Pęcherz moczowy miernie wypełniony, ściana pogrubiała, nierówna, gr. ok. {val_pecherz} mm, ze wskazaniem na odczyn zapalny. Mocz niejednorodny."
    elif osad_pecherz:
        pecherz_norma = f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {val_pecherz} mm. W świetle pęcherza widoczny mierny, echogenny osad opadający grawitacyjnie. Cewka moczowa w dostępnym odcinku nieposzerzona."
    else:
        pecherz_norma = f"Pęcherz moczowy dobrze wypełniony, prawidłowego kształtu, cienkościenny, ściana gr. ok. {val_pecherz} mm, prawidłowej budowy, bez cech zapalenia, mocz aechogenny, bez mineralizacji w świetle, lokalizacja narządu prawidłowa. Cewka moczowa w dostępnym do badania odcinku nieposzerzona, ściana prawidłowej budowy, bez uchwytnych złogów w świetle."

    # Układ rozrodczy
    if plec == "Pies (samiec niekastrowany)":
        rodne_norma = "Gruczoł krokowy niepowiększony, miąższ normoechogenny, jednorodny, bez zmian guzowatych, bez cech zapalenia. Jądra w mosznie, prawidłowej wielkości i echogeniczności, miąższ jednorodny, bez zmian ogniskowych."
    elif plec == "Pies (samiec kastrowany)":
        rodne_norma = "Gruczoł krokowy niepowiększony, fizjologicznie zmniejszony (stan po kastracji), miąższ jednorodny, bez cech zapalenia. Stan po orchidektomii – brak jąder w mosznie."
    elif plec == "Suka (cała)":
        rodne_norma = "Macica niepowiększona. Ściana prawidłowej grubości, prawidłowej budowy, bez uchwytnych zmian patologicznych, brak cech ropnego zapalenia w momencie badania. Jajniki niepowiększone, normoechogenne, bez zmian guzowatych, bez uchwytnych zmian w budowie."
    else:
        rodne_norma = "Kikut macicy, loże po jajnikach bez uchwytnych zmian."

    # Nerki
    if przebudowa_nerek:
        nerki_norma = f"Nerki lewa około {val_nerka_l} cm, prawa ok. {val_nerka_p} cm. Zatarte zróżnicowanie korowo-rdzeniowe, miąższ o podwyższonej echogeniczności z cechami przebudowy pozapalnej/zwyrodnieniowej. Torebka narządu gładka, miedniczki nieposzerzone."
    else:
        nerki_norma = f"Nerki prawidłowego kształtu, lewa około {val_nerka_l} cm, prawa ok. {val_nerka_p} cm, kora i rdzeń prawidłowej echogeniczności, nerki o wyraźnej granicy korowo-rdzeniowej, stosunek obu warstw zachowany. Torebka narządu gładka, hiperechogenna, miedniczki nerkowe nieposzerzone, bez uchwytnych złogów w świetle. Moczowody bez uchwytnych zmian w budowie."

    nadnercza_norma = "Nadnercza prawidłowej wielkości i kształtu, bez uchwytnych zmian w budowie."

    # Śledziona
    if niejednorodna_spleen:
        spleen_norma = f"Śledziona powiększona/prawidłowa, grubości około {val_spleen} cm na wysokości trzonu narządu, miąższ niejednorodny, o podwyższonej echogeniczności / z obecnością drobnych ognisk odczynowych. Torebka narządu gładka."
    else:
        spleen_norma = f"Śledziona prawidłowej wielkości, grubości około {val_spleen} cm na wysokości trzonu narządu, miąższ jednorodny, drobnoziarnisty, bez zmian ogniskowych, torebka narządu gładka, hiperechogenna. Żyła śledzionowa nieposzerzona."

    zoladek_norma = f"Żołądek nieposzerzony, w świetle niewielka ilość gazu, ściana o zachowanej warstwowości, pomiędzy fałdami gr. ok. {val_zoladek} mm, okolica odźwiernika bez zmian, drożność zachowana, perystaltyka zachowana, brak cech zapalenia ostrego."

    # Jelita
    if ibd_jelita:
        jelita_norma = f"Ściana dwunastnicy gr. ok. {val_dwunastnica} mm, ściana okrężnicy ok. {val_okresnica} mm. Jelita cienkie z cechami przewlekłego odczynu zapalnego, warstwowość miejscami zatarta / pogrubiała warstwa śluzowa, perystaltyka wzmożona."
    else:
        jelita_norma = f"Ściana dwunastnicy niepogrubiała, ok. {val_dwunastnica} mm, warstwowość zachowana, światło nieposzerzone, w świetle niewielka ilość strawionej treści, perystaltyka prawidłowa. Jelita cienkie o zachowanej warstwowości ściany, grubość ściany prawidłowa, perystaltyka zachowana. Światło nieposzerzone, w świetle niewielka ilość strawionej treści. Ujście BŚO bez zmian. Ściana okrężnicy o prawidłowej grubości, ok. {val_okresnica} mm i warstwowości, okrężnica wypełniona uformowanymi masami kałowymi."

    # Wątroba i pęcherzyk
    wat_text = "Wątroba podwyższonej echogeniczności (cechy stłuszczenia/przebudowy miąższu)." if stf_watroba else "Wątroba niepowiększona, miąższ gruboziarnisty, jednorodny, o prawidłowej echogeniczności, bez zmian ogniskowych, krawędzie narządu regularne. Naczynia wątrobowe nieposzerzone."
    pec_text = f"Pęcherzyk żółciowy niepowiększony, ściana gr. ok. {val_pecherzyk} mm, w świetle obecna zagęszczona/zestalona żółć (błotko żółciowe)." if zestalona_zolc else f"Pęcherzyk żółciowy niepowiększony, ściana prawidłowej grubości, gr. ok. {val_pecherzyk} mm i echogeniczności, bez uchwytnych złogów w świetle."
    watroba_norma = f"{wat_text} {pec_text} Drogi żółciowe nieposzerzone. Układ wrotny bez uchwytnych zmian w budowie."

    trzustka_norma = f"Trzustka prawidłowej wielkości, gr. ok. {val_trzustka} mm i kształtu, brzegi regularne, struktura niezmieniona, miąższ o prawidłowej echogeniczności, bez cech zapalenia ostrego. Przewód trzustkowy nieposzerzony."

    # Węzły chłonne
    wezly_norma = "Węzły chłonne krezkowe/biodrowe odczynowo powiększone, o obniżonej echogeniczności." if powiekszone_wezly else "Węzły chłonne na terenie jamy brzusznej niepowiększone, bez uchwytnych zmian w budowie."

    # Płyn
    plyn_norma = "Obecna niewielka ilość wolnego, aechogennego płynu w przestrzeni międzypętlowej." if odczyn_plyn else "Brak wolnego płynu w jamie brzusznej."

    report_sections = [
        pecherz_norma,
        rodne_norma,
        nerki_norma,
        nadnercza_norma,
        spleen_norma,
        zoladek_norma,
        jelita_norma,
        watroba_norma,
        trzustka_norma,
        wezly_norma,
        plyn_norma
    ]
    
    if dodaj_tarczyce:
        report_sections.append("TARCZYCA: Płaty tarczycy prawidłowej wielkości i kształtu, miąższ o prawidłowej echogeniczności, bez zmian ogniskowych.")

    final_report_text = "\n\n".join(report_sections)

st.markdown("---")

# --- WYŚWIETLANIE WYNIKU Z PRZYCISKIEM KOPIOWANIA ---
st.subheader("📋 Wygenerowany Opis USG:")
st.caption("Użyj ikony 📋 w prawym górnym rogu poniższego pola, aby natychmiast skopiować cały raport.")
st.code(final_report_text, language=None)
