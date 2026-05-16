"""
Фабрика для создания коллекторов социальных сетей
"""
from typing import Dict, Optional
from .base_collector import BaseCollector
from .youtube_collector import YouTubeCollector
from .telegram_collector import TelegramCollector
from modules.logger import get_logger

logger = get_logger("collector_factory")


class CollectorFactory:
    """Фабрика для создания коллекторов на основе типа источника"""

    _COLLECTORS = {
        'youtube': YouTubeCollector,
        'telegram': TelegramCollector,
    }

    _URL_PATTERNS = {
        'youtube': ['youtube.com', 'youtu.be'],
        'telegram': ['t.me', 'telegram.me', '@'],
    }

    @classmethod
    def create_collector(
        cls,
        source_type: str,
        credentials: Optional[Dict] = None
    ) -> BaseCollector:
        """
        Создает коллектор для указанного типа источника

        Args:
            source_type: Тип источника ('youtube', 'telegram')
            credentials: Учетные данные для API

        Returns:
            Экземпляр коллектора

        Raises:
            ValueError: Если тип источника не поддерживается
        """
        source_type = source_type.lower()
        collector_class = cls._COLLECTORS.get(source_type)

        if collector_class is None:
            supported = ', '.join(cls._COLLECTORS.keys())
            logger.error(f"Unsupported source type: {source_type}")
            raise ValueError(
                f"Неподдерживаемый тип источника: {source_type}. "
                f"Поддерживаемые типы: {supported}"
            )

        logger.info(f"Creating collector for source type: {source_type}")
        return collector_class(credentials)

    @classmethod
    def detect_source_type(cls, url: str) -> Optional[str]:
        """
        Определяет тип источника по URL

        Args:
            url: URL источника

        Returns:
            Тип источника или None если не удалось определить

        Examples:
            >>> CollectorFactory.detect_source_type('https://youtube.com/watch?v=123')
            'youtube'
            >>> CollectorFactory.detect_source_type('https://t.me/channel')
            'telegram'
        """
        url_lower = url.lower()

        for source_type, patterns in cls._URL_PATTERNS.items():
            if any(pattern in url_lower for pattern in patterns):
                logger.debug(f"Detected source type: {source_type} from URL: {url}")
                return source_type

        logger.warning(f"Could not detect source type from URL: {url}")
        return None

    @classmethod
    def create_from_url(
        cls,
        url: str,
        credentials: Optional[Dict] = None
    ) -> BaseCollector:
        """
        Создает коллектор автоматически определяя тип по URL

        Args:
            url: URL источника
            credentials: Учетные данные для API

        Returns:
            Экземпляр коллектора

        Raises:
            ValueError: Если не удалось определить тип источника
        """
        source_type = cls.detect_source_type(url)

        if source_type is None:
            logger.error(f"Could not determine source type from URL: {url}")
            raise ValueError(
                f"Не удалось определить тип источника по URL: {url}. "
                f"Поддерживаемые источники: {', '.join(cls._COLLECTORS.keys())}"
            )

        logger.info(f"Creating collector from URL: {url} (detected type: {source_type})")
        return cls.create_collector(source_type, credentials)

    @classmethod
    def get_supported_sources(cls) -> list:
        """
        Возвращает список поддерживаемых источников

        Returns:
            Список названий источников
        """
        return list(cls._COLLECTORS.keys())

    @classmethod
    def get_required_credentials(cls, source_type: str) -> Dict:
        """
        Возвращает информацию о необходимых учетных данных

        Args:
            source_type: Тип источника

        Returns:
            Словарь с описанием необходимых учетных данных

        Raises:
            ValueError: Если тип источника не поддерживается
        """
        credentials_info = {
            'youtube': {
                'api_key': {
                    'required': True,
                    'description': 'API ключ YouTube Data API v3',
                    'how_to_get': 'https://console.cloud.google.com/'
                }
            },
            'telegram': {
                'api_id': {
                    'required': True,
                    'description': 'API ID приложения Telegram',
                    'how_to_get': 'https://my.telegram.org/apps'
                },
                'api_hash': {
                    'required': True,
                    'description': 'API Hash приложения Telegram',
                    'how_to_get': 'https://my.telegram.org/apps'
                }
            }
        }

        source_type = source_type.lower()
        if source_type not in credentials_info:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type}")

        return credentials_info[source_type]
