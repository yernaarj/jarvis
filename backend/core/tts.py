import pyttsx3
import logging
from typing import Optional
import platform

logger = logging.getLogger(__name__)


def is_wsl():
    """Проверяет запущен ли код в WSL"""
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except:
        return False


class TextToSpeech:
    def __init__(self, rate: int = 150, volume: float = 0.9):
        self.engine = None
        self.wsl_mode = is_wsl()
        
        try:
            if self.wsl_mode:
                logger.warning("WSL обнаружен. TTS может работать нестабильно.")
                logger.info("Для лучшего качества запустите проект в Windows")
                # В WSL используем консольный вывод + можно попробовать Windows TTS
                self.engine = None
            else:
                # Инициализируем pyttsx3
                logger.info("Инициализация TTS...")
                self.engine = pyttsx3.init()
                
                # Настройка скорости речи
                self.engine.setProperty('rate', rate)
                
                # Настройка громкости (0.0 - 1.0)
                self.engine.setProperty('volume', volume)
                
                # Пытаемся найти русский голос
                voices = self.engine.getProperty('voices')
                russian_voice = None
                
                for voice in voices:
                    # Проверяем разные варианты русских голосов
                    if any(x in voice.name.lower() for x in ['russian', 'ru_ru', 'ru-ru', 'elena', 'irina']):
                        russian_voice = voice.id
                        logger.info(f"✅ Найден русский голос: {voice.name}")
                        break
                
                if russian_voice:
                    self.engine.setProperty('voice', russian_voice)
                else:
                    logger.warning("⚠️ Русский голос не найден, используется голос по умолчанию")
                
                logger.info("✅ TTS инициализирован успешно")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации TTS: {e}")
            logger.info("Будет использоваться текстовый вывод в консоль")
            self.engine = None
    
    def speak(self, text: str) -> bool:
        """Произносит текст голосом"""
        # Всегда выводим в консоль (для логов)
        logger.info(f"🔊 JARVIS: {text}")
        print(f"\n🤖 JARVIS: {text}\n")
        
        # Если TTS доступен - говорим вслух
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка озвучивания: {e}")
                return False
        else:
            # В WSL или если TTS недоступен - только текст
            if self.wsl_mode:
                # Можно попробовать вызвать Windows TTS через PowerShell
                try:
                    import subprocess
                    # Экранируем кавычки в тексте
                    safe_text = text.replace('"', '""')
                    ps_command = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{safe_text}")'
                    subprocess.run(
                        ['powershell.exe', '-Command', ps_command],
                        capture_output=True,
                        timeout=120
                    )
                    return True
                except Exception as e:
                    logger.debug(f"Windows TTS через PowerShell недоступен: {e}")
                    return False
            
            return False
    
    def is_available(self) -> bool:
        """Проверяет доступен ли TTS"""
        return self.engine is not None