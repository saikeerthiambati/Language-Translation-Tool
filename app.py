import streamlit as st
from deep_translator import MyMemoryTranslator, GoogleTranslator
from gtts import gTTS
from langdetect import detect
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import io
import os
import base64
import time

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

# ---------------- Language options (code used by translation & speech recognition) ----------------
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
mymemory_lang_map = {
    "en": "en-US", "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN",
    "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN",
    "gu": "gu-IN", "pa": "pa-IN", "ur": "ur-PK", "or": "or-IN",
    "as": "as-IN", "sa": "sa-IN", "ne": "ne-NP", "es": "es-ES",
    "fr": "fr-FR", "de": "de-DE", "ja": "ja-JP", "zh-CN": "zh-CN",
    "gom": "gom-IN", "sd": "sd-PK",
}

# Google Speech Recognition needs BCP-47 style codes too
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

# ---------------- Auto-detect support ----------------
# langdetect runs fully offline (no API calls, no extra rate limits) and
# covers most — not all — of the languages above. Unsupported ones (Odia,
# Assamese, Konkani, Sindhi, Sanskrit) fall back to English.
DETECT_LABEL = "🔍 Detect Language"
FROM_OPTIONS = [DETECT_LABEL] + list(languages.keys())
_detect_reverse_lookup = {code.lower(): code for code in languages.values()}


def resolve_source_code(text, code):
    """Turn the special 'auto' source code into a real language code by
    guessing from the text. Returns the code unchanged if it isn't 'auto'."""
    if code != "auto":
        return code
    if not text or not text.strip():
        return "en"
    try:
        guess = detect(text).lower()
    except Exception:
        return "en"
    detected_code = _detect_reverse_lookup.get(guess)
    if detected_code:
        return detected_code
    st.info(f"Couldn't confidently detect a supported language (guessed '{guess}') — defaulting to English.")
    return "en"


# ---------------- Session state defaults ----------------
if "recorder_key_suffix" not in st.session_state:
    st.session_state.recorder_key_suffix = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None


# ---------------- Helper: run the translation, store it (doesn't render) ----------------
def translate_and_speak(text, source_code, target_code, from_label, to_label):
    real_source = resolve_source_code(text, source_code)
    mm_source = mymemory_lang_map.get(real_source, real_source)
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

    # Stored (rather than rendered right here) so the "Try Google Instead"
    # button below can trigger a rerun without losing this result.
    st.session_state.last_result = {
        "original": text,
        "translated": translated_text,
        "source_code": real_source,
        "target_code": target_code,
        "mm_source": mm_source,
        "mm_target": mm_target,
        "from_label": from_label if from_label != DETECT_LABEL else f"{DETECT_LABEL} ({real_source})",
        "to_label": to_label,
        "google_alt": None,
        "back_translation": None,
    }

    # ---- Save to recent-translations history (most recent first, max 5) ----
    st.session_state.history.insert(0, {
        "from": st.session_state.last_result["from_label"],
        "to": to_label,
        "original": text,
        "translated": translated_text,
    })
    st.session_state.history = st.session_state.history[:5]


def try_google_translate():
    """Callback for the 'Try Google Translate Instead' button. Only ever
    fires when the user explicitly clicks it — so Google gets at most one
    extra call per result the user is unsure about, not one per translation."""
    r = st.session_state.last_result
    if not r:
        return
    try:
        r["google_alt"] = GoogleTranslator(source=r["source_code"], target=r["target_code"]).translate(r["original"])
    except Exception as e:
        error_message = str(e)
        if "too many requests" in error_message.lower() or "429" in error_message:
            r["google_alt"] = "⚠️ Google Translate is rate-limited right now — try again in a bit."
        else:
            r["google_alt"] = f"⚠️ Google Translate unavailable: {error_message}"


def render_last_result():
    """Draws the current translation result: text, audio + download,
    a back-translation sanity check, and the on-demand Google alternative."""
    r = st.session_state.last_result
    if not r:
        return

    st.success("Translation:")
    st.code(r["translated"], language=None)

    # ---- Text-to-Speech for the translated result, with a download option ----
    try:
        tts = gTTS(text=r["translated"], lang=r["target_code"])
        audio_buf = io.BytesIO()
        tts.write_to_fp(audio_buf)
        audio_bytes_value = audio_buf.getvalue()
        st.audio(audio_bytes_value, format="audio/mp3")
        st.download_button(
            "⬇️ Download Translation Audio",
            data=audio_bytes_value,
            file_name="translation.mp3",
            mime="audio/mp3",
            key=f"dl_{hash(r['translated'])}",
        )
    except Exception:
        st.info("Audio not available for this language.")

    # ---- Round-trip back-translation, so mismatches are visible at a glance ----
    if r["back_translation"] is None:
        try:
            r["back_translation"] = MyMemoryTranslator(
                source=r["mm_target"], target=r["mm_source"]
            ).translate(r["translated"])
        except Exception:
            r["back_translation"] = ""  # stay quiet if this check itself fails
    if r["back_translation"]:
        st.caption(f"🔄 Back-translation check (should roughly match what you entered): \"{r['back_translation']}\"")
        st.caption("If that doesn't look close to your original text, the translation above may be off — try Google below.")

    # ---- On-demand Google Translate alternative ----
    st.button("🇬 Try Google Translate Instead", on_click=try_google_translate, key="try_google_btn")
    if r["google_alt"]:
        st.info(f"Google Translate says: {r['google_alt']}")


# ---------------- Helper: convert recorded speech to text ----------------
def speech_to_text(audio_bytes, lang_code):
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    recog_lang = recognition_lang_map.get(lang_code, "en-US")
    return recognizer.recognize_google(audio_data, language=recog_lang)


def clear_form():
    """Reset every input widget back to its default, and swap the audio
    recorder's key so it drops any previously recorded clip."""
    st.session_state.source_lang_select = FROM_OPTIONS[1]  # "English"
    st.session_state.target_lang_select = list(languages.keys())[1]  # "Hindi"
    st.session_state.input_text_area = ""
    st.session_state.batch_text_area = ""
    st.session_state.recorder_key_suffix += 1
    st.session_state.last_result = None


def swap_languages():
    """Swap From/To. Blocked when From is set to auto-detect, since the
    To dropdown has no 'detect' option to swap into."""
    src = st.session_state.source_lang_select
    tgt = st.session_state.target_lang_select
    if src == DETECT_LABEL:
        st.session_state._swap_blocked = True
        return
    st.session_state.source_lang_select = tgt
    st.session_state.target_lang_select = src


# ---------------- Language selection (shared by all modes) ----------------
col1, col2, col3 = st.columns([5, 1, 5])
with col1:
    source_lang = st.selectbox("From:", FROM_OPTIONS, index=1, key="source_lang_select")
with col2:
    st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
    st.button("⇄", on_click=swap_languages, help="Swap From/To languages", use_container_width=True)
with col3:
    target_lang = st.selectbox("To:", list(languages.keys()), index=1, key="target_lang_select")

if st.session_state.pop("_swap_blocked", False):
    st.warning("Pick a specific 'From' language (not Detect Language) before swapping.")

source_code = "auto" if source_lang == DETECT_LABEL else languages[source_lang]
target_code = languages[target_lang]

st.divider()

# ---------------- Mode 1: Type to Translate (Text-to-Text / Text-to-Speech) ----------------
st.subheader("⌨️ Type to Translate")
input_text = st.text_area("Enter text to translate:", height=120, key="input_text_area")

char_count = len(input_text)
word_count = len(input_text.split())
st.caption(f"{char_count} characters · {word_count} words (free translation quota is limited — keep an eye on usage)")

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    translate_clicked = st.button("Translate Text", use_container_width=True)
with btn_col2:
    play_original_clicked = st.button("🔊 Play Original Text", use_container_width=True, disabled=not input_text.strip())

if translate_clicked:
    if input_text.strip() == "":
        st.warning("Please enter some text to translate.")
    else:
        with st.spinner("Translating..."):
            translate_and_speak(input_text, source_code, target_code, source_lang, target_lang)

if play_original_clicked and input_text.strip():
    real_code = resolve_source_code(input_text, source_code)
    try:
        tts = gTTS(text=input_text, lang=real_code)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.audio(buf, format="audio/mp3")
    except Exception:
        st.info("Audio not available for this language.")

st.divider()

# ---------------- Mode 2: Speak to Translate (Speech-to-Text / Speech-to-Speech) ----------------
st.subheader("🎙️ Speak to Translate")
if source_lang == DETECT_LABEL:
    st.caption("Click the mic and speak. (Auto-detect isn't supported for speech recognition itself, "
               "so it'll be recognized as English, then the translation source language will be "
               "detected from the recognized text.)")
else:
    st.caption(f"Click the mic, speak in **{source_lang}**, then click again to stop.")

audio_bytes = audio_recorder(
    pause_threshold=2.0,
    sample_rate=16000,
    key=f"recorder_{st.session_state.recorder_key_suffix}",
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

    if st.button("Translate Speech"):
        try:
            with st.spinner("Converting speech to text..."):
                recognized_text = speech_to_text(audio_bytes, source_code)
            st.info(f"You said: {recognized_text}")
            with st.spinner("Translating..."):
                translate_and_speak(recognized_text, source_code, target_code, source_lang, target_lang)
        except sr.UnknownValueError:
            st.error("Sorry, couldn't understand the audio. Please try again clearly.")
        except sr.RequestError:
            st.error("Speech recognition service is unavailable right now.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

st.divider()

# ---------------- Result of the most recent translation (text or speech) ----------------
render_last_result()
if st.session_state.last_result:
    st.divider()

# ---------------- Mode 3: Batch Translate (multiple lines at once) ----------------
st.subheader("📋 Batch Translate")
st.caption("One phrase per line — each line is translated separately using the From/To languages above.")
batch_text = st.text_area("Enter multiple lines:", height=120, key="batch_text_area")

if st.button("Translate All Lines"):
    lines = [line.strip() for line in batch_text.split("\n") if line.strip()]
    if not lines:
        st.warning("Enter at least one line.")
    else:
        results = []
        progress = st.progress(0.0)
        for i, line in enumerate(lines):
            real_source = resolve_source_code(line, source_code)
            mm_source = mymemory_lang_map.get(real_source, real_source)
            mm_target = mymemory_lang_map.get(target_code, target_code)
            try:
                translated_line = MyMemoryTranslator(source=mm_source, target=mm_target).translate(line)
            except Exception as e:
                translated_line = f"⚠️ Failed: {e}"
            results.append({"Original": line, "Translated": translated_line})
            progress.progress((i + 1) / len(lines))
            time.sleep(0.3)  # small pause so rapid-fire calls don't trip the free API's rate limit
        st.dataframe(results, use_container_width=True, hide_index=True)

st.divider()

# ---------------- Recent Translations ----------------
with st.expander(f"🕘 Recent Translations ({len(st.session_state.history)})"):
    if not st.session_state.history:
        st.caption("No translations yet — your last 5 will show up here.")
    else:
        for item in st.session_state.history:
            st.markdown(f"**{item['from']} → {item['to']}**")
            st.write(f"📝 {item['original']}")
            st.write(f"➡️ {item['translated']}")
            st.markdown("---")
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

st.divider()

# ---------------- Clear everything ----------------
st.button("🔄 Clear Form", on_click=clear_form, use_container_width=True)