"""
Коллектор сообщений из Telegram через Telethon
"""
import re
from typing import List, Optional, Dict
from datetime import datetime
from .base_collector import BaseCollector, Comment
from modules.logger import get_logger

logger = get_logger("telegram_collector")


class TelegramCollector(BaseCollector):
    """Коллектор сообщений из публичных каналов Telegram"""

    def _validate_credentials(self) -> None:
        """Проверяет наличие API ID и Hash для Telegram"""
        required = ['api_id', 'api_hash']
        missing = [key for key in required if key not in self.credentials]

        if missing:
            logger.error(f"Missing Telegram credentials: {', '.join(missing)}")
            raise ValueError(
                f"Отсутствуют учетные данные: {', '.join(missing)}. "
                "Получите их на https://my.telegram.org/apps"
            )
        logger.info("Telegram API credentials validated")

    def extract_id_from_url(self, url: str) -> str:
        """
        Извлекает username канала или ID поста из URL Telegram

        Args:
            url: URL канала или поста Telegram

        Returns:
            Username канала или ID поста

        Raises:
            ValueError: Если URL некорректный

        Примеры URL:
            - https://t.me/channel_name
            - https://t.me/channel_name/123
            - @channel_name
        """
        # Убираем @ если есть
        if url.startswith('@'):
            channel = url[1:]
            logger.debug(f"Extracted channel from @mention: {channel}")
            return channel

        # Паттерны для t.me
        patterns = [
            r't\.me/([a-zA-Z0-9_]+)(?:/(\d+))?',
            r'telegram\.me/([a-zA-Z0-9_]+)(?:/(\d+))?',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                channel = match.group(1)
                post_id = match.group(2) if match.lastindex >= 2 else None
                result = f"{channel}/{post_id}" if post_id else channel
                logger.debug(f"Extracted from URL: {result}")
                return result

        logger.error(f"Failed to extract channel name from URL: {url}")
        raise ValueError(f"Не удалось извлечь имя канала из URL: {url}")

    async def _collect_comments_async(
        self,
        source_url: str,
        max_comments: int = 100,
        include_replies: bool = False
    ) -> List[Comment]:
        """
        Асинхронный метод сбора сообщений из Telegram

        Args:
            source_url: URL канала или поста
            max_comments: Максимальное количество сообщений
            include_replies: Включать ли ответы (не поддерживается в публичных каналах)

        Returns:
            Список объектов Comment
        """
        try:
            from telethon import TelegramClient
            from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError
        except ImportError:
            logger.error("telethon library not installed")
            raise ImportError(
                "Установите библиотеку: pip install telethon"
            )

        channel_info = self.extract_id_from_url(source_url)

        # Проверяем, есть ли ID конкретного поста
        if '/' in channel_info:
            channel_name, post_id = channel_info.split('/')
            post_id = int(post_id)
        else:
            channel_name = channel_info
            post_id = None

        logger.info(f"Starting to collect messages from Telegram channel: {channel_name}, max_comments: {max_comments}")

        client = TelegramClient(
            'session_' + channel_name,
            self.credentials['api_id'],
            self.credentials['api_hash']
        )

        try:
            await client.start()

            comments = []

            if post_id:
                # Получаем комментарии к конкретному посту
                try:
                    # Получаем сам пост
                    message = await client.get_messages(channel_name, ids=post_id)
                    if message:
                        # Получаем обсуждение поста (если есть)
                        async for msg in client.iter_messages(
                            channel_name,
                            reply_to=post_id,
                            limit=max_comments
                        ):
                            comment = self._message_to_comment(msg, channel_name)
                            if comment:
                                comments.append(comment)
                except Exception:
                    # Если нет обсуждений, просто возвращаем сам пост
                    if message:
                        comment = self._message_to_comment(message, channel_name)
                        if comment:
                            comments.append(comment)
            else:
                # Получаем последние сообщения из канала
                async for message in client.iter_messages(channel_name, limit=max_comments):
                    comment = self._message_to_comment(message, channel_name)
                    if comment:
                        comments.append(comment)

            logger.info(f"Successfully collected {len(comments)} messages from Telegram channel: {channel_name}")
            return comments

        except ChannelPrivateError:
            logger.error(f"Channel is private: {channel_name}")
            raise ConnectionError(f"Канал {channel_name} является приватным")
        except UsernameNotOccupiedError:
            logger.error(f"Channel not found: {channel_name}")
            raise ValueError(f"Канал {channel_name} не найден")
        except Exception as e:
            logger.error(f"Telegram API error: {str(e)}")
            raise ConnectionError(f"Ошибка Telegram API: {str(e)}")
        finally:
            await client.disconnect()

    def _message_to_comment(self, message, channel_name: str) -> Optional[Comment]:
        """
        Преобразует сообщение Telegram в объект Comment

        Args:
            message: Объект сообщения Telethon
            channel_name: Имя канала

        Returns:
            Объект Comment или None если сообщение пустое
        """
        if not message.text:
            return None

        # Получаем имя автора
        if message.sender:
            author = getattr(message.sender, 'username', None) or \
                     getattr(message.sender, 'first_name', 'Unknown')
        else:
            author = channel_name

        return Comment(
            text=message.text,
            author=author,
            timestamp=message.date,
            likes=getattr(message.reactions, 'results', [{}])[0].get('count', 0) if message.reactions else 0,
            replies_count=getattr(message, 'replies', None).replies if hasattr(message, 'replies') and message.replies else 0,
            comment_id=str(message.id),
            source='Telegram',
            url=f"https://t.me/{channel_name}/{message.id}"
        )

    def collect_comments(
        self,
        source_url: str,
        max_comments: int = 100,
        include_replies: bool = False
    ) -> List[Comment]:
        """
        Собирает сообщения из канала Telegram (синхронная обертка)

        Args:
            source_url: URL канала или поста
            max_comments: Максимальное количество сообщений
            include_replies: Включать ли ответы

        Returns:
            Список объектов Comment
        """
        import asyncio

        # Создаем новый event loop если его нет
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self._collect_comments_async(source_url, max_comments, include_replies)
        )

    async def get_channel_info_async(self, channel_url: str) -> Dict:
        """
        Получает информацию о канале (асинхронно)

        Args:
            channel_url: URL канала

        Returns:
            Словарь с информацией о канале
        """
        try:
            from telethon import TelegramClient
        except ImportError:
            raise ImportError("Установите библиотеку: pip install telethon")

        channel_name = self.extract_id_from_url(channel_url)
        if '/' in channel_name:
            channel_name = channel_name.split('/')[0]

        client = TelegramClient(
            'session_' + channel_name,
            self.credentials['api_id'],
            self.credentials['api_hash']
        )

        try:
            await client.start()
            entity = await client.get_entity(channel_name)

            return {
                'title': getattr(entity, 'title', channel_name),
                'username': getattr(entity, 'username', channel_name),
                'subscribers': getattr(entity, 'participants_count', 0),
                'description': getattr(entity, 'about', ''),
                'url': f"https://t.me/{channel_name}"
            }
        finally:
            await client.disconnect()

    def get_channel_info(self, channel_url: str) -> Dict:
        """
        Получает информацию о канале (синхронная обертка)

        Args:
            channel_url: URL канала

        Returns:
            Словарь с информацией о канале
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.get_channel_info_async(channel_url))
