# Система сохранения результатов анализа эмоций

## Обзор

Система предоставляет возможность сохранения результатов анализа эмоций в различных форматах:
- **JSON** - для последующего сохранения в базу данных
- **PDF** - для экспорта отчетов с графиками и визуализациями

## Архитектура

### Модули

1. **`modules/visualization.py`** - `EmotionVisualizer`
   - Создание круговых диаграмм распределения эмоций
   - Создание столбчатых диаграмм частоты эмоций
   - Генерация визуализаций в формате base64 (для веб) и bytes (для PDF)

2. **`modules/analysis_results_handler.py`** - `AnalysisResultsHandler`
   - Сохранение результатов в JSON
   - Экспорт отчетов в PDF с графиками
   - Подготовка данных для сохранения в БД

3. **`modules/emotion_classifier.py`** - `RuBertEmotionAnalyzer`
   - Обновлен для использования `EmotionVisualizer`
   - Методы визуализации теперь делегируются в отдельный модуль

## Использование

### Базовый пример

```python
from modules.emotion_classifier import RuBertEmotionAnalyzer
from modules.text_preprocessing import TextPreprocessor
from modules.analysis_results_handler import AnalysisResultsHandler

# Инициализация
analyzer = RuBertEmotionAnalyzer()
preprocessor = TextPreprocessor()
results_handler = AnalysisResultsHandler()

# Загрузка модели
analyzer.load_model()

# Предобработка текста
comments = ["Я очень рад этому событию!", "Мне грустно и одиноко."]
preprocessed_data = []

for idx, comment in enumerate(comments):
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
analysis_results = analyzer.analyze_with_comments(preprocessed_data)

# Сохранение в JSON
results_handler.save_to_json(
    analysis_results, 
    "output/analysis_result.json"
)

# Экспорт в PDF
results_handler.export_to_pdf(
    analysis_results, 
    "output/analysis_report.pdf",
    include_sentence_details=True
)

# Подготовка для БД
db_data = results_handler.prepare_for_database(analysis_results)
```

### Сохранение только в JSON

```python
# Быстрое сохранение без PDF
results_handler.save_to_json(analysis_results, "output/result.json")
```

### Экспорт в PDF без деталей предложений

```python
# PDF только с общей статистикой (без деталей по каждому предложению)
results_handler.export_to_pdf(
    analysis_results, 
    "output/summary_report.pdf",
    include_sentence_details=False
)
```

### Использование визуализатора напрямую

```python
from modules.visualization import EmotionVisualizer

visualizer = EmotionVisualizer()

# Создание круговой диаграммы
probabilities = {
    "радость": 0.45,
    "грусть": 0.25,
    "злость": 0.15,
    "страх": 0.10,
    "удивление": 0.05
}

chart_base64 = visualizer.create_emotion_chart(
    probabilities, 
    "Распределение эмоций"
)

# Для PDF - получение в виде байтов
chart_bytes = visualizer.get_chart_as_bytes(
    probabilities,
    "Распределение эмоций"
)
```

## Структура данных

### Формат JSON

```json
{
  "metadata": {
    "timestamp": "2026-05-18T12:00:00",
    "version": "1.0.0"
  },
  "analysis": {
    "comments": [
      {
        "comment_index": 0,
        "original_text": "Текст комментария",
        "valid_sentences_count": 2,
        "skipped_sentences_count": 0,
        "comment_summary": {
          "emotion_counts": {"радость": 2},
          "dominant_emotion": "радость",
          "average_confidence": 0.89,
          "total_sentences": 2
        },
        "sentence_results": [
          {
            "text": "Предложение 1",
            "emotion": "радость",
            "confidence": 0.92,
            "all_probabilities": {
              "радость": 0.92,
              "грусть": 0.03,
              "злость": 0.02,
              "страх": 0.01,
              "удивление": 0.01,
              "любовь": 0.01
            },
            "sentence_index_in_comment": 0
          }
        ]
      }
    ],
    "overall_summary": {
      "emotion_counts": {"радость": 5, "грусть": 2},
      "dominant_emotion": "радость",
      "average_confidence": 0.87,
      "total_sentences": 7
    },
    "total_comments": 3,
    "total_analyzed_sentences": 7,
    "overall_statistics": {
      "emotion_counts": {"радость": 5, "грусть": 2},
      "total_sentences": 7
    }
  }
}
```

### Формат PDF

PDF отчет включает:
1. **Титульная страница** с датой создания
2. **Общая статистика**
   - Количество комментариев
   - Количество проанализированных предложений
   - Доминирующая эмоция
   - Средняя уверенность модели
   - Таблица распределения эмоций
3. **Общие визуализации**
   - Круговая диаграмма общего распределения эмоций
   - Столбчатая диаграмма частоты эмоций
4. **Детальный анализ комментариев** (опционально)
   - Текст каждого комментария
   - Статистика по комментарию
   - Диаграмма распределения эмоций в комментарии

## API методы

### AnalysisResultsHandler

#### `save_to_json(analysis_data: Dict, output_path: str) -> bool`
Сохраняет результаты анализа в JSON файл.

**Параметры:**
- `analysis_data` - результаты анализа от `analyzer.analyze_with_comments()`
- `output_path` - путь для сохранения JSON файла

**Возвращает:** `True` при успехе, `False` при ошибке

#### `export_to_pdf(analysis_data: Dict, output_path: str, include_sentence_details: bool = True) -> bool`
Экспортирует результаты в PDF отчет.

**Параметры:**
- `analysis_data` - результаты анализа
- `output_path` - путь для сохранения PDF файла
- `include_sentence_details` - включать ли детали по каждому предложению

**Возвращает:** `True` при успехе, `False` при ошибке

#### `prepare_for_database(analysis_data: Dict) -> Dict`
Подготавливает данные для сохранения в БД (удаляет base64 изображения).

**Параметры:**
- `analysis_data` - результаты анализа

**Возвращает:** Очищенные данные в формате словаря

### EmotionVisualizer

#### `create_emotion_chart(probabilities: Dict[str, float], title: str) -> str`
Создает круговую диаграмму в формате base64 data URI.

#### `create_frequency_chart(emotion_counts: Dict[str, int]) -> str`
Создает столбчатую диаграмму частоты в формате base64 data URI.

#### `get_chart_as_bytes(probabilities: Dict[str, float], title: str) -> bytes`
Создает круговую диаграмму и возвращает PNG в виде байтов (для PDF).

#### `get_frequency_chart_as_bytes(emotion_counts: Dict[str, int]) -> bytes`
Создает столбчатую диаграмму и возвращает PNG в виде байтов (для PDF).

## Интеграция с FastAPI

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os

@app.post("/analyze/export/json")
async def export_analysis_json(text: str):
    """Анализ текста и возврат JSON"""
    # ... выполнить анализ ...
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        results_handler.save_to_json(analysis_results, f.name)
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        media_type='application/json',
        filename='analysis_result.json'
    )

@app.post("/analyze/export/pdf")
async def export_analysis_pdf(text: str, include_details: bool = True):
    """Анализ текста и возврат PDF отчета"""
    # ... выполнить анализ ...
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        results_handler.export_to_pdf(
            analysis_results, 
            f.name,
            include_sentence_details=include_details
        )
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        media_type='application/pdf',
        filename='analysis_report.pdf'
    )
```

## Примеры

Полные рабочие примеры доступны в файле `App/example_usage.py`:

```bash
# Запуск примера
cd App
python example_usage.py
```

Результаты будут сохранены в `App/data/analysis_results/`:
- `analysis_result.json` - JSON с результатами
- `analysis_report.pdf` - PDF отчет с графиками

## Требования

- Python 3.8+
- reportlab >= 4.0.0 (для PDF)
- matplotlib >= 3.0.0 (для визуализаций)
- torch, transformers (для модели)

## Логирование

Все модули используют систему логирования проекта:
- `visualization` - логи создания визуализаций
- `analysis_results_handler` - логи сохранения файлов

Логи доступны в `App/logs/`.

## Обработка ошибок

Все методы обрабатывают исключения и возвращают:
- `bool` для операций сохранения (True/False)
- Пустые строки/байты для визуализаций при ошибке
- Логируют ошибки через систему логирования

## Производительность

- JSON сохранение: ~10-50ms для типичного анализа
- PDF генерация: ~500-2000ms в зависимости от количества графиков
- Визуализации кэшируются в памяти во время генерации PDF

## Будущие улучшения

- [ ] Поддержка других форматов экспорта (Excel, CSV)
- [ ] Настраиваемые темы для PDF отчетов
- [ ] Сжатие изображений в PDF для уменьшения размера файла
- [ ] Асинхронная генерация PDF для больших отчетов
- [ ] Шаблоны отчетов с возможностью кастомизации
