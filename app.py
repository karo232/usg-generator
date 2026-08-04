import streamlit as st
import tempfile
import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

st.set_page_config(
    page_title="USG Vet Scans - Generator Opisów", 
    layout="wide", 
    page_icon="🩺"
)

# === WPISZ KLUCZ BEZPOŚREDNIO TUTAJ ===
# Wklej swój wygenerowany klucz wewnątrz cudzysłowu poniżej:
api_key = "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"

client = None
if HAS_OPENAI and api_key:
    client = OpenAI(api_key=api_key)
