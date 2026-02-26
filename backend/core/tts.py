import logging

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Mock версия TTS для тестирования без звука"""
    
    def __init__(self, rate: int = 150, volume: float = 0.9):
        logger.info("✅ TTS инициализирован (mock режим - текст в консоль)")
    
    def speak(self, text: str) -> bool:
        """Mock - выводим в консоль вместо озвучки"""
        logger.info(f"🔊 JARVIS: {text}")
        print(f"\n🤖 JARVIS: {text}\n")
        return True