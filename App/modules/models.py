"""
Центральный модуль для импорта всех моделей базы данных.
Импортируйте модели из этого модуля, а не напрямую из user.py
"""
from App.modules.user import User, TextAnalysis

__all__ = ['User', 'TextAnalysis']
