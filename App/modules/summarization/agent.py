from openai import OpenAI
from typing import List, Dict
import json

from App.infrastructure.config import settings

# Подключаемся к локальному шлюзу OmniRoute
client = OpenAI(
    api_key=settings.OMNIROUTE_API_KEY,
    base_url=settings.OMNIROUTE_ENDPOINT
)

SYSTEM_PROMPT = """Ты — эксперт по анализу пользовательских комментариев и отзывов. Твоя задача — провести глубокий анализ комментариев к видео/контенту и предоставить структурированную суммаризацию.

**Твои обязанности:**

1. **Анализ тональности**: Определи общее настроение аудитории (позитивное, негативное, нейтральное, смешанное)

2. **Что понравилось пользователям**:
   - Выдели ключевые аспекты, которые получили положительные отзывы
   - Укажи конкретные моменты, темы или элементы контента, которые хвалят
   - Процитируй наиболее показательные комментарии (если есть)

3. **Что не понравилось пользователям**:
   - Определи основные претензии и критику
   - Выяви повторяющиеся проблемы или недовольства
   - Укажи конструктивную критику отдельно от простого негатива

4. **Ключевые темы и инсайты**:
   - Найди повторяющиеся темы в обсуждениях
   - Выдели неожиданные или интересные наблюдения пользователей
   - Определи вопросы, которые задают чаще всего

5. **Рекомендации**:
   - На основе анализа предложи, что можно улучшить
   - Укажи, какие сильные стороны стоит развивать

**Формат ответа:**

Предоставь анализ в формате JSON со следующей структурой:
```json
{
  "overall_sentiment": "позитивное/негативное/нейтральное/смешанное",
  "sentiment_distribution": {
    "positive_percent": 0-100,
    "negative_percent": 0-100,
    "neutral_percent": 0-100
  },
  "liked": {
    "summary": "краткое описание того, что понравилось",
    "key_points": ["пункт 1", "пункт 2", "..."],
    "notable_comments": ["цитата 1", "цитата 2"]
  },
  "disliked": {
    "summary": "краткое описание того, что не понравилось",
    "key_points": ["пункт 1", "пункт 2", "..."],
    "notable_comments": ["цитата 1", "цитата 2"]
  },
  "key_themes": ["тема 1", "тема 2", "..."],
  "common_questions": ["вопрос 1", "вопрос 2", "..."],
  "recommendations": ["рекомендация 1", "рекомендация 2", "..."],
  "insights": "дополнительные важные наблюдения"
}
```

**Важно:**
- Будь объективным и основывайся только на данных из комментариев
- Если комментариев мало, укажи это и будь осторожен с выводами
- Игнорируй спам и нерелевантные сообщения
- Отвечай только на русском языке
- Возвращай ТОЛЬКО валидный JSON без дополнительного текста"""


def analyze_comments(comments: List[Dict[str, str]], context: str = "") -> Dict:
    """
    Анализирует список комментариев и возвращает структурированную суммаризацию.

    Args:
        comments: Список словарей с комментариями. Каждый словарь должен содержать:
                 - 'text': текст комментария
                 - 'author': автор (опционально)
                 - 'likes': количество лайков (опционально)
        context: Дополнительный контекст (название видео, тема и т.д.)

    Returns:
        Dict с результатами анализа
    """
    # Формируем текст для анализа
    comments_text = "\n\n".join([
        f"Комментарий {i+1}:\n"
        f"Автор: {comment.get('author', 'Неизвестно')}\n"
        f"Текст: {comment['text']}\n"
        f"Лайков: {comment.get('likes', 0)}"
        for i, comment in enumerate(comments)
    ])

    user_message = f"""Контекст: {context}

Всего комментариев для анализа: {len(comments)}

Комментарии:
{comments_text}

Проанализируй эти комментарии и предоставь структурированную суммаризацию в формате JSON."""

    try:
        response = client.chat.completions.create(
            model=settings.LLM,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,  # Немного выше для более творческого анализа
            max_tokens=2000
        )

        result_text = response.choices[0].message.content

        # Пытаемся распарсить JSON
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # Если модель вернула текст с markdown, пытаемся извлечь JSON
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
                result = json.loads(result_text)
                return result
            else:
                raise

    except Exception as e:
        return {
            "error": str(e),
            "message": "Не удалось проанализировать комментарии"
        }


# Пример использования
if __name__ == "__main__":
    # Тестовые данные
    test_comments = [
        {
            "author": "Иван",
            "text": "Отличное видео! Очень понравилось объяснение, все четко и по делу.",
            "likes": 15
        },
        {
            "author": "Мария",
            "text": "Хорошо, но звук немного тихий. Пришлось прибавлять громкость.",
            "likes": 8
        },
        {
            "author": "Петр",
            "text": "Спасибо за контент! Когда будет продолжение?",
            "likes": 23
        },
        {
            "author": "Анна",
            "text": "Не понравилось. Слишком много воды, можно было короче.",
            "likes": 3
        },
        {
            "author": "Дмитрий",
            "text": "Супер! Именно то, что искал. Подписался!",
            "likes": 42
        }
    ]

    result = analyze_comments(
        comments=test_comments,
        context="Обучающее видео по программированию на Python"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))