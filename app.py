import streamlit as st
import tempfile
import os
import traceback

st.set_page_config(page_title="USG Vet Scans - Pełna Diagnostyka", layout="wide", page_icon="🩺")

st.title("🩺 USG Vet Scans — Diagnostyka Głęboka")

# 1. WERSJE BIBLIOTEK
st.subheader("1. Wersje zainstalowanych pakietów:")
try:
    import openai
    st.write(f"📦 Wersja `openai`: **{openai.__version__}**")
except Exception as e:
    st.error(f"❌ Błąd importu `openai`: {e}")

# 2. STATUS SECRETS & REPR()
st.subheader("2. Odczyt ze `st.secrets`:")
if "OPENAI_API_KEY" in st.secrets:
    raw_key = st.secrets["OPENAI_API_KEY"]
    st.write(f"✔️ Typ obiektu: `{type(raw_key)}`")
    st.write(f"📏 Długość ciągu: `{len(raw_key)}` znaków")
    st.write(f"🔍 Początek klucza `sk-proj-`: `{str(raw_key).startswith('sk-proj-')}`")
    st.write(f"🔬 Surowy odczyt `repr()` (pokazuje ukryte spacji/znaki \\n): `{repr(raw_key)}`")
    
    # Oczyszczenie klucza dla próby połączenia
    clean_key = str(raw_key).strip().strip('"').strip("'")
else:
    clean_key = None
    st.error("❌ `OPENAI_API_KEY` NIE występuje w `st.secrets`!")

st.markdown("---")

# 3. PRÓBA INICJALIZACJI KLIENTA OPENAI
st.subheader("3. Test tworzenia obiektu `OpenAI(api_key=...)`:")
client = None
if clean_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=clean_key)
        st.success("🎉 Klient OpenAI został zainicjalizowany poprawnie!")
    except Exception:
        st.error("❌ Błąd podczas wykonywania `OpenAI(api_key=...)`:")
        st.code(traceback.format_exc(), language="python")
else:
    st.warning("⚠️ Pomijanie inicjalizacji — brak klucza w Secrets.")

st.markdown("---")

# 4. TEST NAGRYWANIA AUDIO
st.subheader("4. Test nagrywania i transkrypcji:")
audio_recorded = st.audio_input("Nagraj krótki test głosu (np. 'test USG')")

if audio_recorded is not None:
    if client is not None:
        with st.spinner("🧠 Transkrypcja w toku..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_recorded.read())
                    tmp_path = tmp_file.name

                with open(tmp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="pl"
                    )
                
                os.remove(tmp_path)
                st.balloons()
                st.success(f"✅ TRANSKRYPCJA ZAKOŃCZONA SUKCESEM: **{transcript.text}**")
            except Exception:
                st.error("❌ Błąd zgłoszony przez serwer OpenAI przy transkrypcji:")
                st.code(traceback.format_exc(), language="python")
    else:
        st.error("❌ Brak aktywnego klienta OpenAI.")
