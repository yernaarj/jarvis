from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API настройки
    API_HOST: str = "127.0.0.1"  # ← ИЗМЕНЕНО с 0.0.0.0 на 127.0.0.1
    API_PORT: int = 49999          # ← Другой порт
    API_RELOAD: bool = True
    
    # Голосовые настройки
    SPEECH_LANGUAGE: str = "ru-RU"
    TTS_RATE: int = 150
    TTS_VOLUME: float = 0.9
    
    # Пути
    LOG_FILE: str = "logs/jarvis.log"
    
    # Режим работы
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()