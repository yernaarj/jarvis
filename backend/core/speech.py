import speech_recognition as sr
from typing import Optional
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def is_wsl():
    """Проверяет запущен ли код в WSL"""
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except:
        return False


class SpeechRecognizer:
    def __init__(self, language: str = "ru-RU"):
        self.recognizer = sr.Recognizer()
        self.language = language
        self.microphone = None
        
        try:
            # Пытаемся инициализировать микрофон
            logger.info("Инициализация микрофона...")
            
            if is_wsl():
                # В WSL микрофон может быть недоступен напрямую
                logger.warning("WSL обнаружен. Микрофон может быть недоступен.")
                logger.info("Для полноценной работы запустите проект в Windows или используйте API /api/command")
                self.microphone = None
            else:
                # Прямой доступ к микрофону (Windows/Linux)
                self.microphone = sr.Microphone()
                
                # Калибровка микрофона
                with self.microphone as source:
                    logger.info("Калибровка микрофона (подождите 2 секунды)...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    logger.info("✅ Микрофон готов!")
                    
        except Exception as e:
            logger.warning(f"⚠️ Не удалось инициализировать микрофон: {e}")
            logger.info("Будет доступен только режим через API")
            self.microphone = None
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Слушает команду через микрофон"""
        if not self.microphone:
            logger.error("Микрофон не инициализирован. Используйте API /api/command")
            return None
            
        try:
            with self.microphone as source:
                logger.info("🎤 Слушаю... (говорите сейчас)")
                
                # Слушаем аудио
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
            logger.info("📡 Распознаю речь...")
            
            # Распознаем через Google Speech API
            text = self.recognizer.recognize_google(audio, language=self.language)
            
            logger.info(f"✅ Распознано: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            logger.warning("⏱️ Тайм-аут: не услышал команду")
            return None
            
        except sr.UnknownValueError:
            logger.warning("❓ Не удалось распознать речь (говорите четче)")
            return None
            
        except sr.RequestError as e:
            logger.error(f"❌ Ошибка сервиса распознавания: {e}")
            logger.info("Проверьте подключение к интернету")
            return None
            
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            return None
    
    def is_available(self) -> bool:
        """Проверяет доступен ли микрофон"""
        return self.microphone is not None