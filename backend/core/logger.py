import logging
import sys
from pathlib import Path


def setup_logger(name: str = "jarvis", log_file: str = "logs/jarvis.log"):
    """Настройка логирования"""
    
    # Создаем папку для логов
    Path("logs").mkdir(exist_ok=True)
    
    # Создаем logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Добавляем handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger