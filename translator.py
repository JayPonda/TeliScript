# translator.py - Language detection and translation utilities
from googletrans import Translator
from langdetect import detect, LangDetectException

class AutoTranslator:
    def __init__(self):
        self.translator = Translator()

    def detect_language(self, text):
        """Detect the language of the given text"""
        if not text or not isinstance(text, str):
            return "unknown"

        try:
            language = detect(text)
            return language
        except LangDetectException:
            return "unknown"
        except Exception:
            return "unknown"

    def translate_to_english(self, text):
        """Automatically detect language and translate to English"""
        if not text or not isinstance(text, str):
            return ""

        try:
            # Detect the language first
            source_lang = self.detect_language(text)

            # If we can't detect the language or it's already English, return as is
            if source_lang == "unknown" or source_lang == "en":
                return text

            # Translate to English
            translated = self.translator.translate(text, src=source_lang, dest="en")
            return translated.text
        except Exception:
            # Return original text if translation fails
            return text

    def is_non_english(self, text):
        """Check if text is likely in a non-English language"""
        if not text or not isinstance(text, str):
            return False

        lang = self.detect_language(text)
        return lang != "unknown" and lang != "en"

    def translate_text(self, text):
        """Translate any non-English text to English"""
        return self.translate_to_english(text)