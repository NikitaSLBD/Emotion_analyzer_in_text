"""
Модуль валидации текста с использованием pymorphy3
"""
import re
from typing import Dict, List
import pymorphy3
from modules.logger import get_logger

logger = get_logger("text_validator")

class TextValidator:
    def __init__(self):
        try:
            self.morph = pymorphy3.MorphAnalyzer()
            logger.info("TextValidator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing pymorphy3: {e}")
            self.morph = None

        self.min_sentence_length = 3
        self.min_words_in_sentence = 2

    def is_russian_word(self, word: str) -> bool:
        """Проверка, является ли слово русским"""
        if not word:
            return False
        russian_chars = re.findall(r'[а-яА-ЯёЁ]', word)
        return len(russian_chars) / len(word) > 0.5

    def check_word_validity(self, word: str) -> Dict:
        """Проверка корректности слова с помощью морфологического анализа"""
        if not self.morph or not word:
            return {"valid": True, "suggestions": []}

        if not self.is_russian_word(word):
            return {"valid": False, "reason": "не русское слово", "suggestions": []}

        parsed = self.morph.parse(word)
        if not parsed:
            return {"valid": False, "reason": "слово не распознано", "suggestions": []}

        best_parse = parsed[0]
        if best_parse.score < 0.1:
            return {"valid": False, "reason": "низкая уверенность распознавания", "suggestions": []}

        return {"valid": True, "parse": best_parse}

    def is_valid_sentence(self, sentence: str) -> Dict:
        """Проверка, является ли текст полноценным предложением на русском языке"""
        if not sentence or len(sentence.strip()) < self.min_sentence_length:
            return {
                "valid": False,
                "reason": "слишком короткое предложение",
                "sentence": sentence
            }

        words = re.findall(r'\b\w+\b', sentence)
        if len(words) < self.min_words_in_sentence:
            return {
                "valid": False,
                "reason": "недостаточно слов в предложении",
                "sentence": sentence
            }

        russian_words = [w for w in words if self.is_russian_word(w)]
        if len(russian_words) / len(words) < 0.5:
            return {
                "valid": False,
                "reason": "недостаточно русских слов",
                "sentence": sentence
            }

        has_ending = bool(re.search(r'[.!?]$', sentence.strip()))

        return {
            "valid": True,
            "has_ending": has_ending,
            "word_count": len(words),
            "russian_word_count": len(russian_words),
            "sentence": sentence
        }

    def validate_text(self, text: str) -> Dict:
        """Валидация текста без исправлений"""
        if not text or not text.strip():
            return {
                "valid": False,
                "reason": "пустой текст",
                "text": text,
                "issues": []
            }

        words = re.findall(r'\b\w+\b', text)
        russian_words = [w for w in words if self.is_russian_word(w)]

        if not russian_words:
            return {
                "valid": False,
                "reason": "нет русских слов",
                "text": text,
                "issues": []
            }

        return {
            "valid": True,
            "text": text,
            "word_count": len(words),
            "russian_word_count": len(russian_words),
            "issues": []
        }
