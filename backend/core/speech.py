import speech_recognition as sr
from typing import Optional
import logging

from core.platform import SYSTEM

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    def __init__(self, language: str = "ru-RU"):
        self.recognizer = sr.Recognizer()
        self.language = language
        self.microphone = None
        self._init_microphone()

    def _init_microphone(self):
        # ── CP-27/28/29 — микрофон на всех платформах ─────────────────────
        if SYSTEM == 'wsl':
            # WSL не имеет прямого доступа к микрофону
            logger.warning("WSL: микрофон недоступен, используйте /api/command")
            return

        # Windows, Linux, macOS — прямой доступ
        try:
            logger.info("Инициализация микрофона...")
            self.microphone = sr.Microphone()
            with self.microphone as source:
                logger.info("Калибровка микрофона (2 сек)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            logger.info(f"✅ Микрофон готов ({SYSTEM})")
        except Exception as e:
            # ── CP-30 — fallback: только API режим ────────────────────────
            logger.warning(f"⚠️ Микрофон недоступен: {e}")
            logger.info("Доступен только режим через /api/command")
            self.microphone = None

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        if not self.microphone:
            logger.error("Микрофон не инициализирован")
            return None

        try:
            with self.microphone as source:
                logger.info("🎤 Слушаю...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            logger.info("📡 Распознаю речь...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"✅ Распознано: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            logger.warning("⏱️ Тайм-аут")
            return None
        except sr.UnknownValueError:
            logger.warning("❓ Не удалось распознать речь")
            return None
        except sr.RequestError as e:
            logger.error(f"❌ Ошибка сервиса: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return None

    def is_available(self) -> bool:
        return self.microphone is not None
