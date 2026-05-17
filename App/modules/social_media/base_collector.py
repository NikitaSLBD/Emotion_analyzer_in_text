"""
Базовый класс для коллекторов комментариев из социальных сетей
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from modules.logger import get_logger

logger = get_logger("base_collector")


@dataclass
class Comment:
    """Структура данных для комментария"""
    text: str
    author: str
    timestamp: datetime
    likes: int = 0
    replies_count: int = 0
    comment_id: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


class BaseCollector(ABC):
    """Абстрактный базовый класс для всех коллекторов"""

    def __init__(self, credentials: Optional[Dict] = None):
        """
        Инициализация коллектора

        Args:
            credentials: Словарь с учетными данными для API
        """
        self.credentials = credentials or {}
        self._validate_credentials()
        logger.info(f"{self.get_source_name()} collector initialized")

    @abstractmethod
    def _validate_credentials(self) -> None:
        """
        Проверяет наличие необходимых учетных данных

        Raises:
            ValueError: Если отсутствуют обязательные учетные данные
        """
        pass

    @abstractmethod
    def collect_comments(
        self,
        source_url: str,
        max_comments: int = 100,
        include_replies: bool = False
    ) -> List[Comment]:
        """
        Собирает комментарии из указанного источника

        Args:
            source_url: URL источника (видео, пост, канал)
            max_comments: Максимальное количество комментариев
            include_replies: Включать ли ответы на комментарии

        Returns:
            Список объектов Comment

        Raises:
            ValueError: Если URL некорректный
            ConnectionError: Если не удалось подключиться к API
        """
        pass

    @abstractmethod
    def extract_id_from_url(self, url: str) -> str:
        """
        Извлекает ID ресурса из URL

        Args:
            url: URL источника

        Returns:
            ID ресурса

        Raises:
            ValueError: Если URL некорректный
        """
        pass

    def get_source_name(self) -> str:
        """
        Возвращает название источника

        Returns:
            Название социальной сети
        """
        return self.__class__.__name__.replace('Collector', '')

    def format_comments_as_text(self, comments: List[Comment]) -> str:
        """
        Форматирует комментарии в единый текст для анализа

        Args:
            comments: Список комментариев

        Returns:
            Объединенный текст всех комментариев
        """
        return f'\n{"_" * 2}\n'.join([
            f"{comment.text}. "
            for comment in comments
        ])

    def get_statistics(self, comments: List[Comment]) -> Dict:
        """
        Получает статистику по собранным комментариям

        Args:
            comments: Список комментариев

        Returns:
            Словарь со статистикой
        """

        avg_length = sum(len(c.text) for c in comments) / len(comments) if comments else 0

        stats = {
            'total_comments': len(comments),
            'average_comment_length': round(avg_length, 2),
            'authors': len(set(c.author for c in comments)),
            'source': self.get_source_name()
        }

        logger.info(f"Statistics calculated: {stats}")
        return stats
