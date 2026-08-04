import streamlit as st
import tempfile
import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

st.set_page_config(
    page_title="USG Vet Scans - Diagnostyka", 
    layout="wide", 
    page_icon="🩺"
)

st.title("🩺 USG Vet Scans — Diagnostyka połączenia")

# --- DIAGNOSTYKA SECRETS ---
st.subheader("🔍 Status Secrets i Klucza API:")

found_key = None

# Sprawdzanie st.secrets
if hasattr(st, "secrets"):
    st.write("✅ Obiekt `st.secrets` jest dostępny.")
    keys_list = list(st.secrets.keys())
    st.write(f"🔑 Znalezione klucze w Secrets: `{keys_list}`")
    
    if "OPENAI_API_KEY" in st.secrets:
        found_key = st.secrets["OPENAI_API_KEY"]
    elif "openai" in st.secrets:
        st.write("ℹ️ Znaleziono sekcję [openai] w Secrets.")
        if "api_key" in st.secrets["openai"]:
            found_key = st.secrets["openai"]["api_key"]
else:
    st.error("❌ Brak obiektu `st.secrets`!")

# Sprawdzanie zmiennych środowiskowych
env_key = os.environ.get("OPENAI_API_KEY")
if env_key:
    st.write("✅ Znaleziono `OPENAI_API_KEY` w zmiennych środowiskowych systemowych (env).")
    if not found_key:
        found_key = env_key

# Podsumowanie klucza
if found_key:
    # Pokazujemy tylko kilka pierwszych i ostatnich znaków dla bezpieczeństwa
    masked_key = found_key[:7] + "..." + found_key[-4:] if len(found_key) > 11 else "ZA KRÓTKI"
    st.success(f"✅ Wykryto klucz API: `{masked_key}` (Długość: {len(found_key)} znaków)")
else:
    st.error("❌ Aplikacja NIE WIDZI żadnego klucza API w Secrets!")

st.markdown("---")

# Inicjalizacja klienta OpenAI
client = None
if HAS_OPENAI and found_key:
    try:
        client = OpenAI(api_key=found_key)
        st.success("✅ Połączono z biblioteką OpenAI!")
    except Exception as e:
        st.error(f"❌ Błąd inicjalizacji OpenAI: {e}")

# TRYB DYKTOWANIA
st.subheader("🎙️ Testowe dyktowanie")
audio_recorded = st.audio_input("Nagraj krótki test głosu (np. 'test raz dwa')")

if audio_recorded is not None:
    if client is not None:
        with st.spinner("🧠 Przetwarzanie przez Whisper AI..."):
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
                st.success(f"🎉 SUKCES! Przepisany tekst: **{transcript.text}**")
            except Exception as e:
                st.error(f"❌ Błąd z serwera OpenAI: {e}")
    else:
        st.error("❌ Nie można wykonać transkrypcji — brak poprawnego klucza API.")
