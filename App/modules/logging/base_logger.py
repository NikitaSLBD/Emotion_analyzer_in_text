import logging
from pathlib import Path
from datetime import datetime
from .handlers import setup_handlers

class EmotionAnalyzerLogger:
    """Основной класс логгера для приложения анализа эмоций"""
    
    def __init__(self, name="emotion_analyzer", log_dir="logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка логирования"""
        # Создаем директорию для логов если не существует
        self.log_dir.mkdir(exist_ok=True)
        
        # Создаем логгер
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Настраиваем обработчики
        setup_handlers(self.logger, self.log_dir, self.name)
    
    def get_logger(self):
        """Возвращает настроенный логгер"""
        return self.logger
    
    def log_startup(self):
        """Логирование запуска приложения"""
        self.logger.info("=" * 50)
        self.logger.info("Запуск приложения анализа эмоций")
        self.logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 50)
    
    def log_shutdown(self):
        """Логирование завершения работы приложения"""
        self.logger.info("=" * 50)
        self.logger.info("Завершение работы приложения анализа эмоций")
        self.logger.info(f"Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 50)
    
    def log_model_loading(self, model_path: str, success: bool, error_msg: str = None):
        """Логирование загрузки модели"""
        if success:
            self.logger.info(f"Модель успешно загружена: {model_path}")
        else:
            self.logger.error(f"Ошибка загрузки модели {model_path}: {error_msg}")
    
    def log_analysis_request(self, text_length: int, sentence_count: int):
        """Логирование запроса на анализ"""
        self.logger.info(
            f"Получен запрос на анализ. "
            f"Длина текста: {text_length} символов, "
            f"Количество предложений: {sentence_count}"
        )
    
    def log_analysis_result(self, sentence_results: list, processing_time: float):
        """Логирование результатов анализа"""
        emotion_counts = {}
        for result in sentence_results:
            emotion = result.get('emotion', 'unknown')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        self.logger.info(
            f"Анализ завершен. "
            f"Время обработки: {processing_time:.2f} сек, "
            f"Распределение эмоций: {emotion_counts}"
        )