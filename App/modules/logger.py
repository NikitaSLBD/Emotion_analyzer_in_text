"""
Основной модуль логгера для обратной совместимости.
Импортирует все из подмодулей logging.
"""

from App.modules.logging.base_logger import EmotionAnalyzerLogger
from App.modules.logging.utils import (
    get_logger,
    log_function_call,
    log_model_operation,
    log_web_request,
    log_text_processing,
    log_error
)

# Создаем глобальный экземпляр логгера
logger_instance = EmotionAnalyzerLogger()
app_logger = logger_instance.get_logger()

__all__ = [
    'EmotionAnalyzerLogger',
    'app_logger',
    'get_logger',
    'log_function_call',
    'log_model_operation',
    'log_web_request',
    'log_text_processing',
    'log_error'
]

if __name__ == "__main__":
    # Тестирование логгера
    logger = get_logger("test")
    logger.info("Тестовое сообщение INFO")
    logger.warning("Тестовое сообщение WARNING")
    logger.error("Тестовое сообщение ERROR")
    
    # Тестирование специальных методов
    logger_instance.log_startup()
    logger_instance.log_model_loading("test_model.pt", True)
    logger_instance.log_shutdown()