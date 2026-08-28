# 🌐 Language Translation Tool

🔗 **Live Demo:** [language-translation-tool-speech.streamlit.app](https://language-translation-tool-speech.streamlit.app/)

A multi-language translation web app built with Python and Streamlit — supporting both typed and spoken input, with audio output for translations.

## Features

- **Type-to-translate** — enter text and translate it instantly between languages
- **Speak-to-translate** — record your voice using the mic, convert speech to text, then translate it (speech-to-speech)
- **Audio output** — listen to the translated text using text-to-speech
- **20+ languages supported**, with a strong focus on Indian languages: Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Urdu, Odia, Assamese, Konkani, Sindhi, Sanskrit, Nepali — plus English, Spanish, French, German, Japanese, and Chinese
- Custom themed UI with a background image

## Tech Stack

- Python 3
- Streamlit — web UI
- deep-translator — text translation (Google Translate backend)
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

1. **Text mode:** Type text, choose source and target languages, and click Translate. The app calls the translation API and shows the result along with a playable audio version.
2. **Speech mode:** Click the mic, speak in the source language, then click again to stop recording. The recorded audio is converted to text using speech recognition, translated, and read back aloud in the target language.

## Author

Sai Keerthi Ambati
