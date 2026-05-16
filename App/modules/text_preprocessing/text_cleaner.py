"""
Модуль очистки текста от лишних символов, пробелов и форматирования
"""
import re
from typing import Dict
from modules.logger import get_logger

class TextCleaner:
    def __init__(self):
        self.whitespace_pattern = r'\s+'
        self.special_chars_pattern = r'[^\w\s.!?,;:\-—]'
        self.multiple_punctuation_pattern = r'([.!?,.:;]){2,}'
        self.line_breaks_pattern = r'[\r\n]+'

    def remove_extra_whitespace(self, text: str) -> str:
        """Удаление множественных пробелов"""
        if not text:
            return text
        text = re.sub(self.whitespace_pattern, ' ', text)
        return text.strip()

    def remove_line_breaks(self, text: str) -> str:
        """Удаление переносов строк"""
        if not text:
            return text
        text = re.sub(self.line_breaks_pattern, ' ', text)
        return text

    def remove_special_chars(self, text: str, keep_punctuation: bool = True) -> str:
        """Удаление специальных символов"""
        if not text:
            return text

        if keep_punctuation:
            text = re.sub(self.special_chars_pattern, '', text)
        else:
            text = re.sub(r'[^\w\s]', '', text)

        return text

    def normalize_punctuation(self, text: str) -> str:
        """Нормализация знаков препинания (удаление множественных)"""
        if not text:
            return text

        text = re.sub(self.multiple_punctuation_pattern, r'\1', text)
        text = re.sub(r'\s+([.!?,;:])', r'\1', text)
        text = re.sub(r'([.!?,;:])\s*([.!?,;:])', r'\1 ', text)

        return text

    def remove_urls(self, text: str) -> str:
        """Удаление URL-адресов"""
        if not text:
            return text

        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(url_pattern, 'САЙТ', text)

        www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(www_pattern, 'САЙТ', text)

        return text

    def remove_emails(self, text: str) -> str:
        """Удаление email-адресов"""
        if not text:
            return text

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, 'ЭЛЕКТРОННАЯ ПОЧТА', text)

        return text

    def remove_numbers(self, text: str) -> str:
        """Удаление чисел"""
        if not text:
            return text

        text = re.sub(r'\d+', '', text)
        return text

    def remove_emojis(self, text: str) -> str:
        """Удаление эмодзи"""
        if not text:
            return text

        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # эмоции
            "\U0001F300-\U0001F5FF"  # символы и пиктограммы
            "\U0001F680-\U0001F6FF"  # транспорт и символы карт
            "\U0001F1E0-\U0001F1FF"  # флаги
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub(r'', text)
        return text

    def clean_text(
        self,
        text: str,
        remove_line_breaks: bool = True,
        remove_extra_whitespace: bool = True,
        remove_special_chars: bool = True,
        normalize_punctuation: bool = True,
        remove_urls: bool = False,
        remove_emails: bool = False,
        remove_numbers: bool = False,
        remove_emojis: bool = False
    ) -> str:
        """
        Комплексная очистка текста

        Args:
            text: Исходный текст
            remove_line_breaks: Удалить переносы строк
            remove_extra_whitespace: Удалить множественные пробелы
            remove_special_chars: Удалить специальные символы
            normalize_punctuation: Нормализовать знаки препинания
            remove_urls: Удалить URL-адреса
            remove_emails: Удалить email-адреса
            remove_numbers: Удалить числа
            remove_emojis: Удалить эмодзи

        Returns:
            Очищенный текст
        """
        if not text or not text.strip():
            return text

        if remove_line_breaks:
            text = self.remove_line_breaks(text)

        if remove_extra_whitespace:
            text = self.remove_extra_whitespace(text)
            
        if remove_urls:
            text = self.remove_urls(text)

        if remove_emails:
            text = self.remove_emails(text)

        if remove_emojis:
            text = self.remove_emojis(text)


        if remove_numbers:
            text = self.remove_numbers(text)

        if remove_special_chars:
            text = self.remove_special_chars(text, keep_punctuation=True)

        if normalize_punctuation:
            text = self.normalize_punctuation(text)

        return text

    def get_cleaning_stats(self, original_text: str, cleaned_text: str) -> Dict:
        """Получение статистики очистки"""
        return {
            "original_length": len(original_text),
            "cleaned_length": len(cleaned_text),
            "removed_chars": len(original_text) - len(cleaned_text),
            "original_words": len(original_text.split()),
            "cleaned_words": len(cleaned_text.split()),
            "removed_words": len(original_text.split()) - len(cleaned_text.split())
        }
