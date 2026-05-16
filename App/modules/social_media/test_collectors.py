"""
Тестовый скрипт для проверки работы коллекторов социальных сетей
"""
import os
import sys
from pathlib import Path

from App.modules.config import settings

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

from App.modules.social_media import CollectorFactory


def test_youtube():
    """Тестирует YouTube коллектор"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ YOUTUBE КОЛЛЕКТОРА")
    print("="*60)

    api_key = settings.YOUTUBE_API_KEY
    if not api_key:
        print("❌ YOUTUBE_API_KEY не установлен в переменных окружения")
        print("   Установите: set YOUTUBE_API_KEY=your_key")
        return

    try:
        collector = CollectorFactory.create_collector('youtube', {'api_key': api_key})
        print("✓ YouTube коллектор создан")

        # Тестовое видео (замените на реальное)
        test_url = input("\nВведите URL YouTube видео (или Enter для пропуска): ").strip()
        if not test_url:
            print("⊘ Тест пропущен")
            return

        print(f"\nСбор комментариев из: {test_url}")
        comments = collector.collect_comments(test_url, max_comments=100)

        print(f"✓ Собрано комментариев: {len(comments)}")

        if comments:
            print("\nПервые 3 комментария:")
            for i, comment in enumerate(comments[:3], 1):
                print(f"\n{i}. {comment.author}")
                print(f"   {comment.text[:100]}...")
                print(f"   Лайков: {comment.likes}, Ответов: {comment.replies_count}")

            stats = collector.get_statistics(comments)
            print(f"\nСтатистика:")
            print(f"  - Всего комментариев: {stats['total_comments']}")
            print(f"  - Уникальных авторов: {stats['authors']}")
            print(f"  - Всего лайков: {stats['total_likes']}")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


def test_telegram():
    """Тестирует Telegram коллектор"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ TELEGRAM КОЛЛЕКТОРА")
    print("="*60)

    api_id = settings.TELEGRAM_API_ID
    api_hash = settings.TELEGRAM_API_HASH

    if not api_id or not api_hash:
        print("❌ TELEGRAM_API_ID или TELEGRAM_API_HASH не установлены")
        print("   Установите: set TELEGRAM_API_ID=your_id")
        print("   Установите: set TELEGRAM_API_HASH=your_hash")
        return

    try:
        collector = CollectorFactory.create_collector('telegram', {
            'api_id': int(api_id),
            'api_hash': api_hash
        })
        print("✓ Telegram коллектор создан")

        # Тестовый канал
        test_url = input("\nВведите URL Telegram канала (или Enter для пропуска): ").strip()
        if not test_url:
            print("⊘ Тест пропущен")
            return

        print(f"\nСбор сообщений из: {test_url}")
        print("⚠ Первый запуск может потребовать авторизации в Telegram")

        messages = collector.collect_comments(test_url, max_comments=10)

        print(f"✓ Собрано сообщений: {len(messages)}")

        if messages:
            print("\nПервые 3 сообщения:")
            for i, msg in enumerate(messages[:3], 1):
                print(f"\n{i}. {msg.author}")
                print(f"   {msg.text[:100]}...")
                print(f"   Дата: {msg.timestamp}")

            stats = collector.get_statistics(messages)
            print(f"\nСтатистика:")
            print(f"  - Всего сообщений: {stats['total_comments']}")
            print(f"  - Уникальных авторов: {stats['authors']}")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


def test_factory():
    """Тестирует фабрику коллекторов"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ФАБРИКИ КОЛЛЕКТОРОВ")
    print("="*60)

    # Тест определения типа по URL
    test_urls = [
        "https://youtube.com/watch?v=123",
        "https://youtu.be/456",
        "https://t.me/channel",
        "@channel_name",
        "https://invalid.com/test"
    ]

    print("\nОпределение типа источника по URL:")
    for url in test_urls:
        source_type = CollectorFactory.detect_source_type(url)
        status = "✓" if source_type else "❌"
        print(f"{status} {url} → {source_type or 'не определен'}")

    # Список поддерживаемых источников
    print(f"\nПоддерживаемые источники: {', '.join(CollectorFactory.get_supported_sources())}")

    # Информация о credentials
    print("\nНеобходимые учетные данные:")
    for source in CollectorFactory.get_supported_sources():
        print(f"\n{source.upper()}:")
        creds = CollectorFactory.get_required_credentials(source)
        for key, info in creds.items():
            print(f"  - {key}: {info['description']}")
            print(f"    Получить: {info['how_to_get']}")


if __name__ == "__main__":
    print("="*60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ СБОРА КОММЕНТАРИЕВ")
    print("="*60)

    # Проверяем переменные окружения
    print("\nПроверка переменных окружения:")
    print(f"  YOUTUBE_API_KEY: {'✓ установлен' if os.getenv('YOUTUBE_API_KEY') else '❌ не установлен'}")
    print(f"  TELEGRAM_API_ID: {'✓ установлен' if os.getenv('TELEGRAM_API_ID') else '❌ не установлен'}")
    print(f"  TELEGRAM_API_HASH: {'✓ установлен' if os.getenv('TELEGRAM_API_HASH') else '❌ не установлен'}")

    # Тестируем фабрику
    test_factory()

    # Тестируем коллекторы
    test_youtube()
    test_telegram()

    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)
