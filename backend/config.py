from pydantic_settings import BaseSettings
from typing import Optional
from core.platform import get_search_dirs


class Settings(BaseSettings):
    # API настройки
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 49999
    API_RELOAD: bool = True

    # Голосовые настройки
    SPEECH_LANGUAGE: str = "ru-RU"
    TTS_RATE: int = 150
    TTS_VOLUME: float = 0.9

    # Пути
    LOG_FILE: str = "logs/jarvis.log"

    # Внешние API
    OPENWEATHER_API_KEY: str = ""

    # Semantic Search
    SEARCH_INDEX_PATH: str = "search/index"
    SEARCH_MODEL_NAME: str = "intfloat/multilingual-e5-small"
    SEARCH_DIRS: list = get_search_dirs()
    SEARCH_MAX_RESULTS: int = 10
    SEARCH_CHUNK_SIZE: int = 512

    # Режим работы
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()