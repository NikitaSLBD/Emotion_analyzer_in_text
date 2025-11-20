import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Форматтер для JSON логов"""
    
    def format(self, record: logging.LogRecord):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем исключение если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Добавляем дополнительные поля
        if hasattr(record, 'custom_fields'):
            log_entry.update(record.custom_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Форматтер с цветами для консоли"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m'    # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


class DetailedFileFormatter(logging.Formatter):
    """Подробный форматтер для файловых логов"""
    
    def __init__(self):
        super().__init__(
            '%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )