import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Mock версия распознавания речи для тестирования без микрофона"""
    
    def __init__(self, language: str = "ru-RU"):
        self.language = language
        logger.info("✅ SpeechRecognizer инициализирован (mock режим)")
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """Mock - возвращаем None (будем использовать API для команд)"""
        logger.warning("Микрофон недоступен. Используй API /api/command")
        return None