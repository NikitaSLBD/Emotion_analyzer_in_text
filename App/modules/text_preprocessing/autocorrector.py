"""
Модуль автоисправления текста с использованием Yandex Speller (pyaspeller)
"""
import re
from typing import Dict, List
from modules.logger import get_logger

logger = get_logger("autocorrector")

try:
    from pyaspeller import YandexSpeller
except ImportError:
    YandexSpeller = None


class AutoCorrector:
    def __init__(self):
        if YandexSpeller:
            try:
                self.speller = YandexSpeller()
                logger.info("YandexSpeller initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing YandexSpeller: {e}")
                self.speller = None
        else:
            logger.warning("pyaspeller not installed. Install with: pip install pyaspeller")
            self.speller = None

        self.common_typos = {
            'прівет': 'привет',
            'спосибо': 'спасибо',
            'здраствуйте': 'здравствуйте',
            'пожалуста': 'пожалуйста',
            'извените': 'извините',
        }

    def is_available(self) -> bool:
        """Проверка доступности корректора"""
        return self.speller is not None

    def correct_word_basic(self, word: str) -> str:
        """Базовое автоисправление слова по словарю"""
        if not word:
            return word

        word_lower = word.lower()

        if word_lower in self.common_typos:
            corrected = self.common_typos[word_lower]
            if word[0].isupper():
                return corrected.capitalize()
            return corrected

        return word

    def spell_check_text(self, text: str) -> Dict:
        """Проверка орфографии с помощью Yandex Speller"""
        if not self.speller:
            logger.warning("Yandex Speller not available for spell check")
            return {
                "has_errors": False,
                "errors": [],
                "message": "Yandex Speller не доступен"
            }

        try:
            changes = self.speller.spell(text)

            errors = []
            for change in changes:
                errors.append({
                    "word": change['word'],
                    "position": change['pos'],
                    "suggestions": change.get('s', []),
                    "code": change.get('code', 0)
                })

            logger.debug(f"Spell check completed: {len(errors)} errors found")
            return {
                "has_errors": len(errors) > 0,
                "errors": errors,
                "error_count": len(errors)
            }
        except Exception as e:
            logger.error(f"Spell check error: {str(e)}")
            return {
                "has_errors": False,
                "errors": [],
                "message": f"Ошибка проверки: {str(e)}"
            }

    def auto_correct_text(self, text: str) -> Dict:
        """Автоматическое исправление текста с помощью Yandex Speller"""
        if not self.speller:
            logger.warning("Yandex Speller not available for auto correction")
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": [],
                "message": "Yandex Speller не доступен"
            }

        try:
            corrected_text = text
            changes = self.speller.spell(text)
            corrections = []

            for change in changes:
                word = change['word']
                suggestions = change.get('s', [])

                if suggestions:
                    best_suggestion = suggestions[0]
                    corrected_text = corrected_text.replace(word, best_suggestion, 1)
                    corrections.append({
                        "original": word,
                        "corrected": best_suggestion,
                        "position": change['pos'],
                        "all_suggestions": suggestions
                    })

            logger.info(f"Auto correction completed: {len(corrections)} corrections made")
            return {
                "original_text": text,
                "corrected_text": corrected_text,
                "corrections": corrections,
                "correction_count": len(corrections)
            }
        except Exception as e:
            logger.error(f"Auto correction error: {str(e)}")
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": [],
                "message": f"Ошибка исправления: {str(e)}"
            }

    def correct_sentence_basic(self, sentence: str) -> tuple[str, List[Dict]]:
        """Базовое исправление предложения по словарю"""
        words = re.findall(r'\b\w+\b', sentence)
        corrections = []
        corrected_sentence = sentence

        for word in words:
            corrected_word = self.correct_word_basic(word)
            if corrected_word != word:
                corrected_sentence = re.sub(r'\b' + re.escape(word) + r'\b', corrected_word, corrected_sentence)
                corrections.append({
                    "original": word,
                    "corrected": corrected_word
                })

        return corrected_sentence, corrections
