# 🌐 Language Translation Tool

🔗 **Live Demo:** [language-translation-tool-speech.streamlit.app](https://language-translation-tool-speech.streamlit.app/)

A multi-language translation web app built with Python and Streamlit — supporting both typed and spoken input, with audio output for translations. Built as part of the **SAM AI Technologies Internship Program** (Artificial Intelligence track — Task 2).

## Features

- **Type-to-translate** — enter text and translate it instantly between languages
- **Speak-to-translate** — record your voice using the mic, convert speech to text, then translate it (speech-to-speech)
- **Batch translate** — paste multiple lines at once and get each one translated separately, shown in a table
- **Auto-detect source language** — pick "🔍 Detect Language" as the From language and it's guessed automatically from your text (offline, via `langdetect`)
- **Swap button (⇄)** — flip the From/To languages in one click
- **Audio output** — listen to the translated text using text-to-speech, and download it as an MP3
- **Play original text** — hear your input read aloud before translating it
- **Back-translation check** — every translation is translated back to the source language so you can spot a wrong result at a glance
- **Try Google Translate instead** — an on-demand button for a second opinion when a translation looks off
- **Recent Translations history** — your last 5 translations, viewable and clearable separately from the form
- **Clear Form button** — resets all inputs (text, languages, mic recording) in one click
- **20+ languages supported**, with a strong focus on Indian languages: Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Urdu, Odia, Assamese, Konkani, Sindhi, Sanskrit, Nepali — plus English, Spanish, French, German, Japanese, and Chinese
- Custom themed UI with a background image

## Tech Stack

- Python 3
- Streamlit — web UI
- deep-translator — translation, via **MyMemory** by default (with Google Translate available on demand as a manual fallback)
- langdetect — offline language auto-detection
- gTTS — text-to-speech
- SpeechRecognition — speech-to-text
- audio-recorder-streamlit — in-browser microphone recording

## How to Run Locally

1. Clone this repository:
   ```
   git clone https://github.com/saikeerthiambati/Language-Translation-Tool.git
   ```
2. Navigate into the project folder:
   ```
   cd Language-Translation-Tool
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the app:
   ```
   streamlit run app.py
   ```

## How It Works

1. **Text mode:** Type text (or let the app auto-detect the language), choose the To language, and click Translate. The app shows the translated text, a back-translation check, playable audio, and a download link for that audio. If a result looks wrong, click "Try Google Translate Instead" for a second opinion.
2. **Speech mode:** Click the mic, speak, then click again to stop recording. The recorded audio is converted to text using speech recognition, translated, and read back aloud in the target language.
3. **Batch mode:** Paste several lines of text (one phrase per line) and translate them all at once — results appear in a table.

### Why MyMemory instead of Google Translate by default?

Google Translate access in `deep-translator` relies on unofficial scraping, which hits frequent rate limits (HTTP 429) on shared hosting like Streamlit Community Cloud, since many apps share the same outbound IP. MyMemory is a real, supported translation API and doesn't have that problem, so it's used as the default. Its trade-off is that it's a translation-memory database rather than a live translation engine, so it can occasionally return an unrelated match for short conversational phrases — the back-translation check and the "Try Google Translate Instead" button exist to catch and work around exactly that.

## Author

Sai Keerthi Ambati