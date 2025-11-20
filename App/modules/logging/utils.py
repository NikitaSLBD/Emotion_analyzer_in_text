import logging
import time
from functools import wraps
from typing import Callable, Any

def get_logger(name: str = None) -> logging.Logger:
    """
    Возвращает логгер для указанного имени.
    
    Args:
        name: Имя логгера. Если None, возвращает корневой логгер.
    
    Returns:
        Настроенный логгер
    """
    if name:
        return logging.getLogger(f"emotion_analyzer.{name}")
    return logging.getLogger("emotion_analyzer")

def log_function_call(logger_name: str = "function_calls"):
    """
    Декоратор для логирования выполнения функций.
    
    Args:
        logger_name: Имя логгера для записи
    
    Returns:
        Декоратор функции
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger(logger_name)
            logger.debug(f"Вызов функции: {func.__name__}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.debug(
                    f"Функция {func.__name__} выполнена успешно "
                    f"(время: {execution_time:.3f} сек)"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Ошибка в функции {func.__name__} "
                    f"(время: {execution_time:.3f} сек): {str(e)}"
                )
                raise
        
        return wrapper
    return decorator

def log_model_operation(operation: str, model_name: str, success: bool, details: dict = None):
    """
    Логирование операций с моделью.
    
    Args:
        operation: Тип операции (загрузка, предсказание и т.д.)
        model_name: Имя модели
        success: Успешность операции
        details: Дополнительные детали
    """
    logger = get_logger("model")
    level = logging.INFO if success else logging.ERROR
    message = f"Модель {model_name}: {operation} {'успешно' if success else 'с ошибкой'}"
    if details:
        message += f" - {details}"
    logger.log(level, message)

def log_web_request(method: str, endpoint: str, status_code: int, processing_time: float):
    """
    Логирование веб-запросов.
    
    Args:
        method: HTTP метод
        endpoint: Эндпоинт
        status_code: Код статуса
        processing_time: Время обработки
    """
    logger = get_logger("web")
    level = logging.INFO if status_code < 400 else logging.WARNING
    logger.log(
        level,
        f"HTTP {method} {endpoint} - Status: {status_code} - Time: {processing_time:.3f} сек"
    )

def log_text_processing(operation: str, input_length: int, output_length: int = None):
    """
    Логирование обработки текста.
    
    Args:
        operation: Тип операции
        input_length: Длина входного текста
        output_length: Длина выходного текста (опционально)
    """
    logger = get_logger("text_processing")
    message = f"Обработка текста: {operation}, вход: {input_length} символов"
    if output_length is not None:
        message += f", выход: {output_length} символов"
    logger.info(message)

def log_error(error_type: str, error_msg: str, logger_name: str = "errors", details: dict = None):
    """
    Логирование ошибок с дополнительным контекстом.
    
    Args:
        error_type: Тип ошибки
        error_msg: Сообщение об ошибке
        logger_name: Имя логгера
        details: Дополнительные детали
    """
    logger = get_logger(logger_name)
    error_context = {
        "custom_fields": {
            "error_type": error_type,
            "details": details or {}
        }
    }
    logger.error(f"Ошибка {error_type}: {error_msg}", extra=error_context)