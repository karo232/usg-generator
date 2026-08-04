import streamlit as st
import tempfile
import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

st.set_page_config(page_title="USG Vet Scans", layout="wide", page_icon="🩺")

if "editable_report_area" not in st.session_state:
    st.session_state["editable_report_area"] = ""

api_key = None
if "OPENAI_API_KEY" in st.secrets:
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip().strip('"').strip("'")

client = OpenAI(api_key=api_key) if (HAS_OPENAI and api_key) else None

st.title("🩺 USG Vet Scans — Dyktowanie USG")

audio_recorded = st.audio_input("Nagraj notatkę głosową USG", key="audio_input_widget")

if audio_recorded is not None:
    audio_bytes = audio_recorded.getvalue()
    file_size = len(audio_bytes)
    
    st.write(f"📊 **Rozmiar odebranego pliku audio:** `{file_size}` bajtów")

    if file_size < 5000:
        st.warning("⚠️ Nagranie jest zbyt krótkie lub puste. Spróbuj nagrać dłuższą wypowiedź.")
    else:
        if client is not None:
            st.info("🚀 Wywołuję Whisper API...")
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_bytes)
                    tmp_path = tmp_file.name

                with open(tmp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="pl",
                        prompt="Opis badania USG weterynaryjnego u psa lub kota, narządy jamy brzusznej:"
                    )
                
                # Przypisanie tekstu do widgetu
                st.session_state["editable_report_area"] = transcript.text
                
                # Diagnostyka struktury
                st.success("✅ Otrzymano odpowiedź z API")
                st.write("**Wygenerowany tekst (`transcript.text`):**")
                st.code(repr(transcript.text))
                
                with st.expander("🔍 Pełny zrzut obiektu JSON z OpenAI"):
                    try:
                        st.json(transcript.model_dump())
                    except Exception:
                        st.write(transcript)

            except Exception as e:
                st.error(f"❌ Błąd OpenAI API: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            st.error("⚠️ Brak aktywnego klienta OpenAI API.")

podyktowany_tekst = st.text_area(
    "Wynik transkrypcji (możesz edytować):",
    key="editable_report_area",
    height=200
)

st.subheader("📋 Wynikowy Opis USG:")
st.code(podyktowany_tekst if podyktowany_tekst else "Czekam na nagranie...", language=None)
