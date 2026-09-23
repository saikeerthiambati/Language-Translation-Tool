import streamlit as st
from deep_translator import MyMemoryTranslator
from gtts import gTTS
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import io
import os
import base64

# ---------------- Page setup ----------------
st.set_page_config(page_title="Language Translator", page_icon="🌐", layout="wide")

# ---------------- Background image (local file, base64-encoded) ----------------
# Resolve relative to this script's own folder, not the process's working
# directory — this is what breaks the background on some hosts/deployments.
IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Background.png")


@st.cache_data
def get_base64_of_image(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Don't let a missing/unreadable image take down the whole app.
try:
    img_base64 = get_base64_of_image(IMAGE_PATH)
    bg_css = f"""
    background-image: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    """
except FileNotFoundError:
    st.warning("Background.png not found — continuing without the background image.")
    bg_css = ""

page_bg = f"""
<style>
[data-testid="stAppViewContainer"] {{
    {bg_css}
}}

[data-testid="stHeader"] {{
    background-color: rgba(0, 0, 0, 0);
}}

.block-container {{
    padding: 2rem 4rem;
    margin-top: 1rem;
    max-width: 1100px;
}}

h1, h2, h3, p, label, .stMarkdown, .stCaption, div[data-testid="stCaptionContainer"] {{
    text-shadow: 0px 1px 6px rgba(0,0,0,0.9), 0px 0px 12px rgba(0,0,0,0.7);
}}

[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background-color: rgba(10, 12, 16, 0.75) !important;
}}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.title("🌐 Language Translation Tool")
st.write("Type or speak text, choose a language, and get an instant translation — with audio output!")

# ---------------- Language options (code used by Google Translate & speech recognition) ----------------
languages = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Odia": "or",
    "Assamese": "as",
    "Konkani": "gom",
    "Sindhi": "sd",
    "Sanskrit": "sa",
    "Nepali": "ne",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Chinese (Simplified)": "zh-CN",
}

# MyMemory needs locale-style codes (e.g. hi-IN) instead of plain codes (hi)
# NOTE: previously missing "gom" (Konkani) and "sd" (Sindhi) — when Google
# Translate failed and the app fell back to MyMemory for those two
# languages, .get(code, code) silently passed the bare code through, which
# MyMemory's API generally rejects, so the fallback failed too.
mymemory_lang_map = {
    "en": "en-US", "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN",
    "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN",
    "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-PK", "or": "or-IN",
    "as": "as-IN", "sa": "sa-IN", "ne": "ne-NP", "es": "es-ES",
    "fr": "fr-FR", "de": "de-DE", "ja": "ja-JP", "zh-CN": "zh-CN",
    "gom": "gom-IN", "sd": "sd-PK",
}

# Google Speech Recognition needs BCP-47 style codes too
# NOTE: previously missing "sa" (Sanskrit), "gom" (Konkani), "sd" (Sindhi) —
# picking one of those as the *spoken* source language silently fell back
# to en-US recognition, which just produces garbage for non-English speech.
recognition_lang_map = {
    "en": "en-US", "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN",
    "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN",
    "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-IN", "or": "or-IN",
    "as": "as-IN", "ne": "ne-NP", "es": "es-ES", "fr": "fr-FR",
    "de": "de-DE", "ja": "ja-JP", "zh-CN": "zh-CN",
    "sa": "sa-IN", "gom": "gom-IN", "sd": "sd-IN",
}
# Google's speech-recognition service doesn't actually have models for
# Sanskrit, Konkani, or Sindhi, so recognition will still fail for those —
# that's a real service limitation, not a bug in this file.


# ---------------- Helper: translate with automatic fallback ----------------
def translate_and_speak(text, source_code, target_code):
    # MyMemory only — Google Translate (via deep_translator's unofficial
    # scraping) kept hitting 429 rate limits on every call when deployed,
    # since Streamlit Community Cloud shares outbound IPs across many apps.
    # MyMemory is a real, supported API and doesn't have that problem.
    mm_source = mymemory_lang_map.get(source_code, source_code)
    mm_target = mymemory_lang_map.get(target_code, target_code)

    try:
        translated_text = MyMemoryTranslator(source=mm_source, target=mm_target).translate(text)
    except Exception as e:
        st.error(
            "Translation failed — the translation service may be temporarily "
            "unavailable, or this language pair may not be supported. Please try again."
        )
        st.caption(f"Debug info: {str(e)}")
        return

    st.success("Translation:")
    st.write(translated_text)

    # ---- Text-to-Speech for the translated result ----
    try:
        tts = gTTS(text=translated_text, lang=target_code)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        st.info("Audio not available for this language.")


# ---------------- Helper: convert recorded speech to text ----------------
def speech_to_text(audio_bytes, lang_code):
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    recog_lang = recognition_lang_map.get(lang_code, "en-US")
    return recognizer.recognize_google(audio_data, language=recog_lang)


# ---------------- Language selection (shared by both modes) ----------------
col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("From:", list(languages.keys()), index=0)
with col2:
    target_lang = st.selectbox("To:", list(languages.keys()), index=1)

source_code = languages[source_lang]
target_code = languages[target_lang]

st.divider()

# ---------------- Mode 1: Type to Translate (Text-to-Text / Text-to-Speech) ----------------
st.subheader("⌨️ Type to Translate")
input_text = st.text_area("Enter text to translate:", height=120)

if st.button("Translate Text"):
    if input_text.strip() == "":
        st.warning("Please enter some text to translate.")
    else:
        translate_and_speak(input_text, source_code, target_code)

st.divider()

# ---------------- Mode 2: Speak to Translate (Speech-to-Text / Speech-to-Speech) ----------------
st.subheader("🎙️ Speak to Translate")
st.caption(f"Click the mic, speak in **{source_lang}**, then click again to stop.")

audio_bytes = audio_recorder(pause_threshold=2.0, sample_rate=16000)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

    if st.button("Translate Speech"):
        try:
            with st.spinner("Converting speech to text..."):
                recognized_text = speech_to_text(audio_bytes, source_code)
            st.info(f"You said: {recognized_text}")
            translate_and_speak(recognized_text, source_code, target_code)
        except sr.UnknownValueError:
            st.error("Sorry, couldn't understand the audio. Please try again clearly.")
        except sr.RequestError:
            st.error("Speech recognition service is unavailable right now.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")