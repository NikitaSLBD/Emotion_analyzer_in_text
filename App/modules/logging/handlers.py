import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from .formatters import JSONFormatter, ColoredConsoleFormatter, DetailedFileFormatter

def create_console_handler():
    """Создает обработчик для консоли"""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = ColoredConsoleFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    return console_handler

def create_file_handler(log_dir: Path, log_name: str):
    """Создает обработчик для файла с обычным текстом"""
    log_file = log_dir / f"{log_name}.log"
    file_handler = TimedRotatingFileHandler(
        log_file, 
        when='midnight', 
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(DetailedFileFormatter())
    
    return file_handler

def create_json_handler(log_dir: Path, log_name: str):
    """Создает обработчик для JSON логов"""
    json_log_file = log_dir / f"{log_name}_json.log"
    json_handler = TimedRotatingFileHandler(
        json_log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JSONFormatter())
    
    return json_handler

def create_error_handler(log_dir: Path, log_name: str):
    """Создает обработчик для ошибок"""
    error_log_file = log_dir / f"{log_name}_errors.log"
    error_handler = TimedRotatingFileHandler(
        error_log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(DetailedFileFormatter())
    
    return error_handler

def setup_handlers(logger: logging.Logger, log_dir: Path, log_name: str):
    """Настраивает все обработчики для логгера"""
    
    # Обработчик для консоли
    console_handler = create_console_handler()
    
    # Обработчик для файла с обычным текстом
    file_handler = create_file_handler(log_dir, log_name)
    
    # Обработчик для JSON логов
    json_handler = create_json_handler(log_dir, log_name)
    
    # Обработчик для ошибок
    error_handler = create_error_handler(log_dir, log_name)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(json_handler)
    logger.addHandler(error_handler)