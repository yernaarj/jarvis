import subprocess
import logging

from core.platform import SYSTEM

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(self, rate: int = 150, volume: float = 0.9):
        self.rate = rate
        self.volume = volume
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        # ── CP-23 — Windows нативно ───────────────────────────────────────
        if SYSTEM == 'windows':
            self._init_pyttsx3()

        # ── WSL — PowerShell TTS ──────────────────────────────────────────
        elif SYSTEM == 'wsl':
            logger.info("WSL: используем PowerShell TTS")

        # ── CP-24 — Linux ─────────────────────────────────────────────────
        elif SYSTEM == 'linux':
            self._init_pyttsx3(fallback='espeak')

        # ── CP-25 — macOS ─────────────────────────────────────────────────
        elif SYSTEM == 'macos':
            self._init_pyttsx3(fallback='say')

    def _init_pyttsx3(self, fallback: str = None):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

            # Ищем русский голос
            for voice in self.engine.getProperty('voices'):
                if any(x in voice.name.lower() for x in ['russian', 'ru_ru', 'ru-ru', 'elena', 'irina']):
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"✅ TTS голос: {voice.name}")
                    break
            else:
                logger.warning("⚠️ Русский голос не найден, используется голос по умолчанию")

            logger.info(f"✅ TTS инициализирован (pyttsx3, {SYSTEM})")
        except Exception as e:
            logger.warning(f"⚠️ pyttsx3 недоступен: {e}")
            if fallback:
                logger.info(f"Используем fallback: {fallback}")
                self.engine = None
                self._fallback = fallback

    def speak(self, text: str) -> bool:
        logger.info(f"🔊 JARVIS: {text}")
        print(f"\n🤖 JARVIS: {text}\n")

        try:
            if self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
                return True

            # ── WSL — PowerShell ──────────────────────────────────────────
            elif SYSTEM == 'wsl':
                safe_text = text.replace('"', '""')
                cmd = (f'Add-Type -AssemblyName System.Speech; '
                       f'$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                       f'$s.Speak("{safe_text}")')
                subprocess.run(['powershell.exe', '-Command', cmd],
                               capture_output=True, timeout=120)
                return True

            # ── Linux fallback — espeak ───────────────────────────────────
            elif SYSTEM == 'linux' and getattr(self, '_fallback', None) == 'espeak':
                subprocess.run(['espeak', '-v', 'ru', text],
                               capture_output=True, timeout=30)
                return True

            # ── macOS fallback — say ──────────────────────────────────────
            elif SYSTEM == 'macos' and getattr(self, '_fallback', None) == 'say':
                subprocess.run(['say', text], capture_output=True, timeout=30)
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка TTS: {e}")

        return False

    def is_available(self) -> bool:
        if self.engine:
            return True
        if SYSTEM == 'wsl':
            return True
        if SYSTEM == 'linux' and getattr(self, '_fallback', None) == 'espeak':
            return True
        if SYSTEM == 'macos' and getattr(self, '_fallback', None) == 'say':
            return True
        return False
