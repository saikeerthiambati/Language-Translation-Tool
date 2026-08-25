import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import io
import base64

# ---------------- Page setup ----------------
st.set_page_config(page_title="Language Translator", page_icon="🌐", layout="wide")

# ---------------- Background image (custom CSS) ----------------
IMAGE_PATH = "Background.png"


def get_base64_of_image(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


img_base64 = get_base64_of_image(IMAGE_PATH)

page_bg = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
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

# ---------------- Language options ----------------
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

# ---------------- Helper: run translation + TTS ----------------
def translate_and_speak(text, source_code, target_code):
    translated_text = GoogleTranslator(source=source_code, target=target_code).translate(text)

    st.success("Translation:")
    st.write(translated_text)

    try:
        tts = gTTS(text=translated_text, lang=target_code)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception:
        st.info("Audio not available for this language.")


# ---------------- Helper: convert recorded audio to text ----------------
def speech_to_text(audio_bytes, lang_code):
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    # Google Speech Recognition needs BCP-47 style codes (e.g. en-US, te-IN)
    recognition_lang_map = {
        "en": "en-US", "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN",
        "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN",
        "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-IN", "or": "or-IN",
        "as": "as-IN", "ne": "ne-NP", "es": "es-ES", "fr": "fr-FR",
        "de": "de-DE", "ja": "ja-JP", "zh-CN": "zh-CN",
    }
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

# ---------------- Mode 1: Text input (Text-to-Text / Text-to-Speech) ----------------
st.subheader("⌨️ Type to Translate")
input_text = st.text_area("Enter text to translate:", height=120)

if st.button("Translate Text"):
    if input_text.strip() == "":
        st.warning("Please enter some text to translate.")
    else:
        try:
            translate_and_speak(input_text, source_code, target_code)
        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.divider()

# ---------------- Mode 2: Speech input (Speech-to-Text / Speech-to-Speech) ----------------
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