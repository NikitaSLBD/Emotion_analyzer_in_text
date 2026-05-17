"""
Модуль-оркестратор для предобработки текста
Объединяет функционал валидации, автоисправления и очистки
"""
import re
from typing import List, Dict
from .text_validator import TextValidator
from .autocorrector import AutoCorrector
from .text_cleaner import TextCleaner
from modules.logger import get_logger

logger = get_logger("text_preprocessor")

class TextPreprocessor:
    def __init__(self):
        self.sentence_endings = r'[.!?]+'
        self.abbreviations = {
            'т.д.', 'т.п.', 'др.', 'пр.', 'стр.', 'рис.', 'ст.', 'г.',
            'см.', 'н.э.', 'и т.д.', 'и т.п.', 'т.е.', 'т.к.'
        }

        self.validator = TextValidator()
        self.corrector = AutoCorrector()
        self.cleaner = TextCleaner()
        logger.info("TextPreprocessor initialized successfully")

    def split_into_sentences(self, text: str) -> List[str]:
        """Разделение текста на предложения с учетом аббревиатур"""
        if not text or not text.strip():
            return []

        temp_abbreviations = {}
        for i, abbr in enumerate(self.abbreviations):
            if abbr in text:
                temp_key = f"__ABBR_{i}__"
                temp_abbreviations[temp_key] = abbr
                text = text.replace(abbr, temp_key)

        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        final_sentences = []
        for sentence in sentences:
            for temp_key, abbr in temp_abbreviations.items():
                sentence = sentence.replace(temp_key, abbr)
            final_sentences.append(sentence)

        return final_sentences

    def split_into_comments(self, text: str) -> List[str]:
        """Разделение текста на комментарии по разделителю"""
        if not text or not text.strip():
            return []

        separator = '\n' + '_' * 2 + '\n'
        comments = text.split(separator)
        comments = [c.strip() for c in comments if c.strip()]

        logger.info(f"Split text into {len(comments)} comments")
        return comments



    def validate_and_correct_text(
        self,
        text: str,
        auto_correct: bool = False,
        use_speller: bool = True,
        skip_invalid: bool = False
    ) -> Dict:
        """
        Комплексная проверка и исправление текста

        Args:
            text: Исходный текст
            auto_correct: Автоматически исправлять ошибки
            use_speller: Использовать Yandex Speller для проверки
            skip_invalid: Пропускать невалидные предложения вместо отклонения всего текста

        Returns:
            Словарь с результатами валидации и исправления
        """
        if not text or not text.strip():
            return {
                "valid": False,
                "reason": "пустой текст",
                "original_text": text,
                "corrected_text": text,
                "valid_sentences": [],
                "skipped_sentences": [],
                "issues": []
            }

        logger.info(f"Текст до очистки: {text}")

        cleaned_text = self.cleaner.clean_text(text)

        logger.info(f"Текст после очистки: {cleaned_text}")

        logger.info(f"Статистика по очистке: {self.cleaner.get_cleaning_stats(text, cleaned_text)}")

        spell_corrections = []
        if auto_correct and use_speller and self.corrector.is_available():
            spell_result = self.corrector.auto_correct_text(cleaned_text)
            cleaned_text = spell_result['corrected_text']
            spell_corrections = spell_result.get('corrections', [])


        sentences = self.split_into_sentences(cleaned_text)

        issues = []
        corrected_sentences = []
        valid_sentences = []
        skipped_sentences = []
        all_valid = True

        for i, sentence in enumerate(sentences):
            validation = self.validator.is_valid_sentence(sentence)

            if not validation["valid"]:
                all_valid = False
                issue = {
                    "sentence_index": i,
                    "sentence": sentence,
                    "reason": validation["reason"]
                }
                issues.append(issue)

                if skip_invalid:
                    # Пропускаем невалидное предложение
                    skipped_sentences.append(issue)
                    logger.warning(f"Пропущено неккоректное предложение {i}: {validation['reason']}")
                    continue
                else:
                    # Сохраняем невалидное предложение в старом режиме
                    corrected_sentences.append(sentence)
                    continue

            # Предложение валидно
            if auto_correct and not use_speller:
                corrected_sentence, corrections = self.corrector.correct_sentence_basic(sentence)
                corrected_sentences.append(corrected_sentence)
                valid_sentences.append(corrected_sentence)

                for corr in corrections:
                    issues.append({
                        "sentence_index": i,
                        "type": "auto_correction",
                        "original_word": corr['original'],
                        "corrected_word": corr['corrected']
                    })
            else:
                corrected_sentences.append(sentence)
                valid_sentences.append(sentence)

        corrected_text = ' '.join(corrected_sentences)

        if spell_corrections:
            for correction in spell_corrections:
                issues.append({
                    "type": "spell_correction",
                    "original_word": correction['original'],
                    "corrected_word": correction['corrected'],
                    "suggestions": correction.get('all_suggestions', [])
                })

        # Определяем валидность результата
        is_valid = all_valid if not skip_invalid else len(valid_sentences) > 0

        result = {
            "valid": is_valid,
            "original_text": text,
            "corrected_text": corrected_text,
            "sentences_count": len(sentences),
            "valid_sentences_count": len(valid_sentences),
            "skipped_sentences_count": len(skipped_sentences),
            "valid_sentences": valid_sentences,
            "skipped_sentences": skipped_sentences,
            "issues": issues,
            "spell_corrections": spell_corrections,
            "has_corrections": (auto_correct and len(issues) > 0) or len(spell_corrections) > 0
        }

        if skip_invalid and skipped_sentences:
            logger.info(f"Валидация: {len(valid_sentences)}/{len(sentences)} sentences valid, {len(skipped_sentences)} skipped")

        return result

    def validate_and_correct_text_with_comments(
        self,
        text: str,
        auto_correct: bool = False,
        use_speller: bool = True,
        skip_invalid: bool = False
    ) -> Dict:
        """
        Комплексная проверка и исправление текста с разделением на комментарии

        Args:
            text: Исходный текст с комментариями, разделенными '\n____________________\n'
            auto_correct: Автоматически исправлять ошибки
            use_speller: Использовать Yandex Speller для проверки
            skip_invalid: Пропускать невалидные предложения вместо отклонения всего текста

        Returns:
            Словарь с иерархической структурой: комментарии -> предложения
        """
        if not text or not text.strip():
            return {
                "valid": False,
                "reason": "пустой текст",
                "original_text": text,
                "comments": []
            }

        logger.info("Starting hierarchical validation with comments")

        # Разделяем на комментарии
        comments = self.split_into_comments(text)

        if not comments:
            logger.warning("No comments found, treating as single text")
            comments = [text]

        all_comments_data = []
        total_valid_sentences = 0
        total_skipped_sentences = 0
        all_valid_sentences = []

        for comment_index, comment_text in enumerate(comments):
            logger.info(f"Processing comment {comment_index + 1}/{len(comments)}")

            # Валидация и исправление комментария
            comment_result = self.validate_and_correct_text(
                comment_text,
                auto_correct=auto_correct,
                use_speller=use_speller,
                skip_invalid=skip_invalid
            )

            # Собираем данные по комментарию
            comment_data = {
                "comment_index": comment_index,
                "original_text": comment_text,
                "corrected_text": comment_result['corrected_text'],
                "valid": comment_result['valid'],
                "sentences_count": comment_result['sentences_count'],
                "valid_sentences_count": comment_result['valid_sentences_count'],
                "skipped_sentences_count": comment_result['skipped_sentences_count'],
                "valid_sentences": comment_result['valid_sentences'],
                "skipped_sentences": comment_result['skipped_sentences'],
                "issues": comment_result['issues'],
                "spell_corrections": comment_result.get('spell_corrections', [])
            }

            all_comments_data.append(comment_data)
            total_valid_sentences += comment_result['valid_sentences_count']
            total_skipped_sentences += comment_result['skipped_sentences_count']
            all_valid_sentences.extend(comment_result['valid_sentences'])

        # Общая валидность - есть ли хотя бы одно валидное предложение
        is_valid = total_valid_sentences > 0

        result = {
            "valid": is_valid,
            "original_text": text,
            "comments_count": len(comments),
            "total_sentences_count": sum(c['sentences_count'] for c in all_comments_data),
            "total_valid_sentences_count": total_valid_sentences,
            "total_skipped_sentences_count": total_skipped_sentences,
            "all_valid_sentences": all_valid_sentences,
            "comments": all_comments_data,
            "has_corrections": any(c.get('spell_corrections') for c in all_comments_data)
        }

        logger.info(f"Hierarchical validation completed: {len(comments)} comments, "
                   f"{total_valid_sentences} valid sentences, {total_skipped_sentences} skipped")

        return result
