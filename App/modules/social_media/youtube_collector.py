"""
Коллектор комментариев из YouTube через YouTube Data API v3
"""
import re
from typing import List, Optional, Dict
from datetime import datetime
from .base_collector import BaseCollector, Comment
from modules.logger import get_logger

logger = get_logger("youtube_collector")


class YouTubeCollector(BaseCollector):
    """Коллектор комментариев из YouTube"""

    def _validate_credentials(self) -> None:
        """Проверяет наличие API ключа YouTube"""
        if 'api_key' not in self.credentials:
            logger.error("YouTube API key is missing")
            raise ValueError(
                "Отсутствует API ключ YouTube. "
                "Получите ключ на https://console.cloud.google.com/"
            )
        logger.info("YouTube API credentials validated")

    def extract_id_from_url(self, url: str) -> str:
        """
        Извлекает video_id из URL YouTube

        Args:
            url: URL видео YouTube

        Returns:
            ID видео

        Raises:
            ValueError: Если URL некорректный

        Примеры URL:
            - https://www.youtube.com/watch?v=VIDEO_ID
            - https://youtu.be/VIDEO_ID
            - https://www.youtube.com/embed/VIDEO_ID
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.debug(f"Extracted video_id: {video_id} from URL: {url}")
                return video_id

        logger.error(f"Failed to extract video_id from URL: {url}")
        raise ValueError(f"Не удалось извлечь video_id из URL: {url}")

    def collect_comments(
        self,
        source_url: str,
        max_comments: int = 100,
        include_replies: bool = False
    ) -> List[Comment]:
        """
        Собирает комментарии из видео YouTube

        Args:
            source_url: URL видео YouTube
            max_comments: Максимальное количество комментариев
            include_replies: Включать ли ответы на комментарии

        Returns:
            Список объектов Comment

        Raises:
            ImportError: Если не установлена библиотека google-api-python-client
            ValueError: Если URL некорректный
            ConnectionError: Если не удалось подключиться к API
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
        except ImportError:
            logger.error("google-api-python-client not installed")
            raise ImportError(
                "Установите библиотеку: pip install google-api-python-client"
            )

        video_id = self.extract_id_from_url(source_url)
        logger.info(f"Starting to collect comments from video: {video_id}, max_comments: {max_comments}")

        try:
            youtube = build('youtube', 'v3', developerKey=self.credentials['api_key'])

            comments = []
            next_page_token = None

            while len(comments) < max_comments:
                request = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    pageToken=next_page_token,
                    textFormat='plainText',
                    order='relevance'
                )

                response = request.execute()

                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']

                    comment = Comment(
                        text=snippet['textDisplay'],
                        author=snippet['authorDisplayName'],
                        timestamp=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                        likes=snippet.get('likeCount', 0),
                        replies_count=item['snippet'].get('totalReplyCount', 0),
                        comment_id=item['id'],
                        source='YouTube',
                        url=f"https://www.youtube.com/watch?v={video_id}&lc={item['id']}"
                    )
                    comments.append(comment)

                    # Добавляем ответы, если требуется
                    if include_replies and 'replies' in item:
                        for reply_item in item['replies']['comments']:
                            reply_snippet = reply_item['snippet']
                            reply = Comment(
                                text=reply_snippet['textDisplay'],
                                author=reply_snippet['authorDisplayName'],
                                timestamp=datetime.fromisoformat(reply_snippet['publishedAt'].replace('Z', '+00:00')),
                                likes=reply_snippet.get('likeCount', 0),
                                replies_count=0,
                                comment_id=reply_item['id'],
                                source='YouTube',
                                url=f"https://www.youtube.com/watch?v={video_id}&lc={reply_item['id']}"
                            )
                            comments.append(reply)

                            if len(comments) >= max_comments:
                                break

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            logger.info(f"Successfully collected {len(comments)} comments from video: {video_id}")
            return comments[:max_comments]

        except HttpError as e:
            if e.resp.status == 403:
                logger.error(f"YouTube API authentication error for video: {video_id}")
                raise ConnectionError(
                    "API ключ недействителен или превышен лимит запросов. "
                    "Проверьте ключ и квоты на https://console.cloud.google.com/"
                )
            elif e.resp.status == 404:
                logger.error(f"Video not found or comments disabled: {video_id}")
                raise ValueError(f"Видео не найдено или комментарии отключены: {video_id}")
            else:
                logger.error(f"YouTube API error: {str(e)}")
                raise ConnectionError(f"Ошибка YouTube API: {str(e)}")

    def get_video_info(self, video_url: str) -> Dict:
        """
        Получает информацию о видео

        Args:
            video_url: URL видео

        Returns:
            Словарь с информацией о видео
        """
        try:
            from googleapiclient.discovery import build
        except ImportError:
            logger.error("google-api-python-client not installed")
            raise ImportError(
                "Установите библиотеку: pip install google-api-python-client"
            )

        video_id = self.extract_id_from_url(video_url)
        logger.info(f"Fetching video info for: {video_id}")

        youtube = build('youtube', 'v3', developerKey=self.credentials['api_key'])

        request = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )

        response = request.execute()

        if not response.get('items'):
            logger.error(f"Video not found: {video_id}")
            raise ValueError(f"Видео не найдено: {video_id}")

        item = response['items'][0]
        snippet = item['snippet']
        statistics = item['statistics']

        video_info = {
            'title': snippet['title'],
            'channel': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'views': int(statistics.get('viewCount', 0)),
            'likes': int(statistics.get('likeCount', 0)),
            'comments_count': int(statistics.get('commentCount', 0)),
            'video_id': video_id,
            'url': video_url
        }

        logger.info(f"Video info retrieved: {video_info['title']} by {video_info['channel']}")
        return video_info
