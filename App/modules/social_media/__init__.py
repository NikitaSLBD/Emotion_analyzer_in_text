"""
Модуль для сбора комментариев из социальных сетей
"""
from .base_collector import BaseCollector, Comment
from .youtube_collector import YouTubeCollector
from .telegram_collector import TelegramCollector
from .collector_factory import CollectorFactory

__all__ = [
    'BaseCollector',
    'Comment',
    'YouTubeCollector',
    'TelegramCollector',
    'CollectorFactory',
]
