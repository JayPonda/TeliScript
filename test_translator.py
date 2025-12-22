#!/usr/bin/env python3
"""
Test script for the new translation functionality
"""

from translator import AutoTranslator

def test_translations():
    """Test the AutoTranslator with various languages"""
    translator = AutoTranslator()

    # Test cases in different languages
    test_cases = [
        ("Hello, how are you?", "English"),
        ("Bonjour, comment allez-vous?", "French"),
        ("Hola, ¿cómo estás?", "Spanish"),
        ("Привет, как дела?", "Russian"),
        ("سلام، چطوری؟", "Persian"),
        ("こんにちは、元気ですか？", "Japanese"),
        ("你好吗？", "Chinese")
    ]

    print("Testing AutoTranslator functionality:")
    print("=" * 50)

    for text, language in test_cases:
        print(f"\nOriginal ({language}): {text}")

        # Detect language
        detected_lang = translator.detect_language(text)
        print(f"Detected language: {detected_lang}")

        # Translate to English
        translated = translator.translate_to_english(text)
        print(f"Translated: {translated}")

        # Check if it's non-English
        is_non_english = translator.is_non_english(text)
        print(f"Is non-English: {is_non_english}")

if __name__ == "__main__":
    test_translations()