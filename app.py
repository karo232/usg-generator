# ================= WYŚWIETLANIE LIST W KOLUMNACH =================
    with st.container(border=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: sel_pecherz = st.selectbox("Pęcherz moczowy", pat_pecherz_options)
        with col_p2: sel_macica = st.selectbox("Układ płciowy (Samica)", pat_macica_options[:4])
        with col_p3: sel_prostata = st.selectbox("Układ płciowy (Samiec)", pat_prostata_options)
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1: sel_nerki = st.selectbox("Nerki", pat_nerki_options)
        with col_n2: sel_nadnercza = st.selectbox("Nadnercza", pat_nadnercza_options)
        with col_n3: sel_sledziona = st.selectbox("Śledziona", pat_sledziona_options)

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1: sel_watroba = st.selectbox("Wątroba", pat_watroba_options)
        with col_w2: sel_pech_zol = st.selectbox("Pęcherzyk żółciowy", pat_pecherzyk_options)
        with col_w3: sel_trzustka = st.selectbox("Trzustka", pat_trzustka_options)

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_pk1, col_pk2 = st.columns(2)
        with col_pk1: sel_pokarmowy = st.selectbox("Przewód pokarmowy", pat_pokarmowy_options)
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color: #135c7e; margin-bottom: 10px;'>Zmiany skórne</h5>", unsafe_allow_html=True)
        col_d1, col_d2 = st.columns(2)
        with col_d1: chk_klos = st.checkbox("Kłos (kończyna międzypalcowa)")
        with col_d2: chk_zmiana = st.checkbox("Zmiana podskórna (okolica pośladka)")
