import re
from typing import List

class TextPreprocessor:
    def __init__(self):
        self.sentence_endings = r'[.!?]+'
        self.abbreviations = {
            'т.д.', 'т.п.', 'др.', 'пр.', 'стр.', 'рис.', 'ст.', 'г.', 
            'см.', 'н.э.', 'и т.д.', 'и т.п.', 'т.е.', 'т.к.'
        }
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Разделение текста на предложения с учетом аббревиатур"""
        if not text or not text.strip():
            return []
        
        # Временная замена аббревиатур
        temp_abbreviations = {}
        for i, abbr in enumerate(self.abbreviations):
            if abbr in text:
                temp_key = f"__ABBR_{i}__"
                temp_abbreviations[temp_key] = abbr
                text = text.replace(abbr, temp_key)
        
        # Разделение на предложения
        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Восстановление аббревиатур
        final_sentences = []
        for sentence in sentences:
            for temp_key, abbr in temp_abbreviations.items():
                sentence = sentence.replace(temp_key, abbr)
            final_sentences.append(sentence)
        
        return final_sentences
    
    def clean_text(self, text: str) -> str:
        """Очистка текста от лишних пробелов и символов"""
        text = re.sub(r'\s+', ' ', text)  # Удаление множественных пробелов
        text = re.sub(r'[^\w\s.!?,;:]', '', text)  # Удаление специальных символов
        return text.strip()