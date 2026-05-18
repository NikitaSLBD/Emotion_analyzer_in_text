"""
Пример использования системы сохранения результатов анализа
"""

from pathlib import Path
from modules.emotion_classifier import RuBertEmotionAnalyzer
from modules.text_preprocessing import TextPreprocessor
from modules.analysis_results_handler import AnalysisResultsHandler


def example_analyze_and_save():
    """Пример анализа текста с сохранением результатов в JSON и PDF"""

    # Инициализация компонентов
    analyzer = RuBertEmotionAnalyzer()
    preprocessor = TextPreprocessor()
    results_handler = AnalysisResultsHandler()

    # Загрузка модели
    print("Загрузка модели...")
    if not analyzer.load_model():
        print("Ошибка загрузки модели")
        return

    # Пример текста для анализа
    sample_comments = [
        "Это был замечательный день! Я очень рад, что все получилось.",
        "Мне грустно и одиноко. Не знаю, что делать дальше.",
        "Я так зол на эту ситуацию! Это несправедливо!"
    ]

    # Предобработка комментариев
    print("\nПредобработка текста...")
    preprocessed_data = []
    for idx, comment in enumerate(sample_comments):
        sentences = preprocessor.split_into_sentences(comment)
        valid_sentences = [s for s in sentences if preprocessor.is_valid_sentence(s)]

        preprocessed_data.append({
            'comment_index': idx,
            'original_text': comment,
            'valid_sentences': valid_sentences,
            'skipped_sentences': [],
            'skipped_sentences_count': 0
        })

    # Анализ эмоций
    print("Анализ эмоций...")
    analysis_results = analyzer.analyze_with_comments(preprocessed_data)

    # Создание директории для результатов
    output_dir = Path("App/data/analysis_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Сохранение в JSON
    json_path = output_dir / "analysis_result.json"
    print(f"\nСохранение результатов в JSON: {json_path}")
    if results_handler.save_to_json(analysis_results, str(json_path)):
        print("✓ JSON файл успешно создан")
    else:
        print("✗ Ошибка создания JSON файла")

    # Экспорт в PDF
    pdf_path = output_dir / "analysis_report.pdf"
    print(f"\nЭкспорт в PDF: {pdf_path}")
    if results_handler.export_to_pdf(analysis_results, str(pdf_path), include_sentence_details=True):
        print("✓ PDF отчет успешно создан")
    else:
        print("✗ Ошибка создания PDF отчета")

    # Подготовка данных для БД
    print("\nПодготовка данных для БД...")
    db_data = results_handler.prepare_for_database(analysis_results)
    print(f"✓ Данные подготовлены: {len(db_data['analysis']['comments'])} комментариев")

    # Вывод краткой статистики
    print("\n" + "="*50)
    print("СТАТИСТИКА АНАЛИЗА")
    print("="*50)
    if 'overall_summary' in analysis_results:
        summary = analysis_results['overall_summary']
        print(f"Всего предложений: {summary.get('total_sentences', 0)}")
        print(f"Доминирующая эмоция: {summary.get('dominant_emotion', 'N/A')}")
        print(f"Средняя уверенность: {summary.get('average_confidence', 0)*100:.1f}%")

        if 'emotion_counts' in summary:
            print("\nРаспределение эмоций:")
            for emotion, count in summary['emotion_counts'].items():
                print(f"  {emotion}: {count}")

    print("\n✓ Анализ завершен!")


def example_json_only():
    """Пример быстрого сохранения только в JSON (без PDF)"""

    analyzer = RuBertEmotionAnalyzer()
    preprocessor = TextPreprocessor()
    results_handler = AnalysisResultsHandler()

    if not analyzer.load_model():
        return

    # Простой текст
    text = "Я очень счастлив сегодня!"

    # Предобработка
    sentences = preprocessor.split_into_sentences(text)
    valid_sentences = [s for s in sentences if preprocessor.is_valid_sentence(s)]

    preprocessed_data = [{
        'comment_index': 0,
        'original_text': text,
        'valid_sentences': valid_sentences,
        'skipped_sentences': [],
        'skipped_sentences_count': 0
    }]

    # Анализ
    analysis_results = analyzer.analyze_with_comments(preprocessed_data)

    # Сохранение только в JSON
    output_path = "App/data/analysis_results/quick_analysis.json"
    results_handler.save_to_json(analysis_results, output_path)
    print(f"Результаты сохранены в: {output_path}")


if __name__ == "__main__":
    print("="*50)
    print("ПРИМЕР ИСПОЛЬЗОВАНИЯ СИСТЕМЫ АНАЛИЗА ЭМОЦИЙ")
    print("="*50)

    # Запуск полного примера
    example_analyze_and_save()

    # Раскомментируйте для быстрого примера:
    # example_json_only()
