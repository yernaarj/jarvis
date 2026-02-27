from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging

from core.logger import setup_logger
from core.speech import SpeechRecognizer
from core.tts import TextToSpeech
from commands.parser import CommandParser
from config import settings

# Настройка логирования
logger = setup_logger()

# Создаем FastAPI app
app = FastAPI(title="Jarvis Backend", version="0.1.0")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные компоненты
speech_recognizer = None
tts = None
parser = CommandParser()


# Pydantic модели
class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    success: bool
    command_type: str
    response: str
    original_text: str


@app.on_event("startup")
async def startup_event():
    """Инициализация при старте"""
    global speech_recognizer, tts
    
    logger.info("🚀 Запуск Jarvis Backend...")
    
    try:
        speech_recognizer = SpeechRecognizer(language=settings.SPEECH_LANGUAGE)
        tts = TextToSpeech(rate=settings.TTS_RATE, volume=settings.TTS_VOLUME)
        logger.info("✅ Все компоненты инициализированы")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "message": "Jarvis Backend is running",
        "version": "0.1.0"
    }


@app.get("/api/status")
async def get_status():
    """Статус системы"""
    return {
        "speech_recognizer": speech_recognizer is not None,
        "tts": tts is not None,
        "ready": speech_recognizer is not None and tts is not None,
        "microphone_available": speech_recognizer.is_available() if speech_recognizer else False,
        "tts_available": tts.is_available() if tts else False
    }


@app.post("/api/test-tts")
async def test_tts(text: str = "Привет, я Джарвис!"):
    """Тест синтеза речи"""
    if tts:
        success = tts.speak(text)
        return {"success": success, "text": text}
    return {"success": False, "error": "TTS not initialized"}


@app.get("/api/test-microphone")
async def test_microphone():
    """Тест микрофона - скажите что-нибудь"""
    if not speech_recognizer:
        return {"error": "Speech recognizer not initialized"}
    
    if not speech_recognizer.is_available():
        from core.speech import is_wsl
        return {"error": "Microphone not available", "wsl": is_wsl()}
    
    logger.info("🎤 Тест микрофона - говорите...")
    text = speech_recognizer.listen(timeout=5)
    
    return {
        "success": text is not None,
        "recognized_text": text,
        "message": "Микрофон работает!" if text else "Не удалось распознать"
    }


@app.post("/api/voice-command")
async def voice_command():
    """Слушает голосовую команду через микрофон"""
    if not speech_recognizer or not speech_recognizer.is_available():
        return {
            "success": False,
            "error": "Микрофон недоступен. Запустите проект в Windows или используйте /api/command"
        }
    
    # Слушаем команду
    logger.info("🎤 Ожидание голосовой команды...")
    text = speech_recognizer.listen(timeout=10, phrase_time_limit=10)
    
    if not text:
        return {
            "success": False,
            "error": "Не удалось распознать команду"
        }
    
    # Обрабатываем как обычную команду
    cmd = CommandRequest(text=text)
    response = await process_command(cmd)
    
    return response


@app.post("/api/command", response_model=CommandResponse)
async def process_command(cmd: CommandRequest):
    """Обработка текстовой команды"""
    logger.info(f"📥 Получена команда: {cmd.text}")
    
    # Парсим команду
    parsed = parser.parse(cmd.text)
    logger.info(f"📊 Тип команды: {parsed['type']}")
    
    # Импортируем обработчики
    from commands.handlers import (
        open_browser, google_search, youtube_search
    )
    from commands.handlers.system import (
        get_current_time, get_current_date,
        volume_up, volume_down, volume_mute,
        take_screenshot, lock_pc, shutdown_pc
    )
    from commands.handlers.apps import open_application, open_folder
    
    # Выполняем команду и генерируем ответ
    success = False
    
    # Браузер и поиск
    if parsed['type'] == 'browser':
        success = open_browser()
        response_text = "Открываю браузер..." if success else "Не удалось открыть браузер"
        
    elif parsed['type'] == 'search':
        query = parsed['groups'][1] if parsed['groups'] and len(parsed['groups']) > 1 else ""
        if query:
            success = google_search(query)
            response_text = f"Ищу в Google: {query}" if success else "Не удалось выполнить поиск"
        else:
            response_text = "Не указан запрос для поиска"
            
    elif parsed['type'] == 'youtube':
        query = ""
        if parsed['groups'] and len(parsed['groups']) > 2:
            query = parsed['groups'][2] if parsed['groups'][2] else ""
        success = youtube_search(query)
        response_text = "Открываю YouTube..." if success else "Не удалось открыть YouTube"
    
    # Приложения
    elif parsed['type'] == 'app_vscode':
        success = open_application('vscode')
        response_text = "Запускаю VS Code..." if success else "Не удалось запустить VS Code"
        
    elif parsed['type'] == 'app_discord':
        success = open_application('discord')
        response_text = "Запускаю Discord..." if success else "Не удалось запустить Discord"
        
    elif parsed['type'] == 'app_telegram':
        success = open_application('telegram')
        response_text = "Запускаю Telegram..." if success else "Не удалось запустить Telegram"
        
    elif parsed['type'] == 'app_spotify':
        success = open_application('spotify')
        response_text = "Запускаю Spotify..." if success else "Не удалось запустить Spotify"
        
    elif parsed['type'] == 'app_notepad':
        success = open_application('notepad')
        response_text = "Открываю блокнот..." if success else "Не удалось открыть блокнот"
        
    elif parsed['type'] == 'app_calc':
        success = open_application('calculator')
        response_text = "Открываю калькулятор..." if success else "Не удалось открыть калькулятор"
        
    elif parsed['type'] == 'app_explorer':
        success = open_folder()
        response_text = "Открываю проводник..." if success else "Не удалось открыть проводник"
    
    # Время и дата
    elif parsed['type'] == 'time':
        current_time = get_current_time()
        response_text = f"Сейчас {current_time}"
        success = True
        
    elif parsed['type'] == 'date':
        current_date = get_current_date()
        response_text = f"Сегодня {current_date}"
        success = True
    
    # Управление громкостью
    elif parsed['type'] == 'volume_up':
        success = volume_up()
        response_text = "Увеличиваю громкость" if success else "Не удалось увеличить громкость"
        
    elif parsed['type'] == 'volume_down':
        success = volume_down()
        response_text = "Уменьшаю громкость" if success else "Не удалось уменьшить громкость"
        
    elif parsed['type'] == 'volume_mute':
        success = volume_mute()
        response_text = "Переключаю звук" if success else "Не удалось переключить звук"
    
    # Скриншот и система
    elif parsed['type'] == 'screenshot':
        success = take_screenshot()
        response_text = "Делаю скриншот..." if success else "Не удалось сделать скриншот"
        
    elif parsed['type'] == 'lock':
        success = lock_pc()
        response_text = "Блокирую компьютер..." if success else "Не удалось заблокировать"
        
    elif parsed['type'] == 'shutdown':
        response_text = "Команда выключения отключена для безопасности. Раскомментируйте код для активации."
        success = False
        # success = shutdown_pc()
        # response_text = "Выключаю компьютер..." if success else "Не удалось выключить"
    
    # Выход
    elif parsed['type'] == 'exit':
        response_text = "До свидания!"
        success = True
    
    # Неизвестная команда
    else:
        response_text = f"Извините, я не понял команду '{cmd.text}'. Попробуйте другую формулировку."
        success = False
    
    # Озвучиваем ответ
    if tts:
        tts.speak(response_text)
    
    return CommandResponse(
        success=success,
        command_type=parsed['type'],
        response=response_text,
        original_text=cmd.text
    )

from fastapi import UploadFile, File
import tempfile
import os

@app.post("/api/audio-command")
async def audio_command(audio: UploadFile = File(...)):
    """Принимает аудио файл, распознаёт и выполняет команду"""
    if not speech_recognizer:
        return {"success": False, "error": "Speech recognizer not initialized"}
    
    temp_path = None
    try:
        # Сохраняем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"📥 Получен аудио файл")
        
        # Распознаём через SpeechRecognition
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=settings.SPEECH_LANGUAGE)
        
        os.unlink(temp_path)
        logger.info(f"✅ Распознано: {text}")
        
        # Обрабатываем команду
        cmd = CommandRequest(text=text.lower())
        response = await process_command(cmd)
        return response
        
    except sr.UnknownValueError:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        return {"success": False, "error": "Не удалось распознать речь"}
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"❌ Ошибка: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=49999,
        reload=False
    )