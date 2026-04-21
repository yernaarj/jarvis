from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
import threading

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

# Search компоненты
embedder = None
indexer = None
searcher = None
watcher = None
_indexing_in_progress = False


# Pydantic модели
class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    success: bool
    command_type: str
    response: str
    original_text: str


def _background_sync(indexer, source):
    """Фоновая синхронизация — не блокирует поиск"""
    try:
        logger.info("🔄 Фоновая синхронизация индекса...")
        indexer.sync(source)
        logger.info(f"✅ Синхронизация завершена: {indexer.total} файлов")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации: {e}")


def _init_search():
    """Инициализация search-компонентов в фоновом потоке"""
    global embedder, indexer, searcher, watcher, _indexing_in_progress
    try:
        from search.core.embedder import Embedder
        from search.core.indexer import Indexer
        from search.core.searcher import Searcher
        from search.core.watcher import Watcher
        from search.sources.local import LocalDiskSource

        logger.info("🔍 Загрузка модели embeddings...")
        embedder = Embedder()
        indexer = Indexer(index_dir=settings.SEARCH_INDEX_PATH, embedder=embedder)
        searcher = Searcher(indexer=indexer, embedder=embedder)
        source = LocalDiskSource(settings.SEARCH_DIRS)

        if indexer.total == 0:
            # Первый запуск — блокируем поиск до завершения
            logger.info("📂 Индекс пустой — полная индексация...")
            _indexing_in_progress = True
            indexer.reindex(source)
            _indexing_in_progress = False
            logger.info(f"✅ Индексация завершена: {indexer.total} файлов")
        else:
            # Индекс уже есть — поиск сразу доступен, sync идёт в фоне
            logger.info(f"✅ Индекс загружен: {indexer.total} файлов — поиск доступен")
            threading.Thread(target=_background_sync, args=(indexer, source), daemon=True).start()

        watcher = Watcher(indexer=indexer, source=source)
        watcher.start()
        logger.info("✅ Search готов к работе")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации search: {e}")


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

    # ── DJ-31 — запуск search в фоне ──────────────────────────────────────
    threading.Thread(target=_init_search, daemon=True).start()


@app.on_event("shutdown")
async def shutdown_event():
    if watcher:
        watcher.stop()


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


# ── DJ-32 — Search endpoints ───────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


@app.get("/api/search/status")
async def search_status():
    """Статус поискового индекса"""
    return {
        "ready": searcher is not None,
        "indexing": _indexing_in_progress,
        "total_files": indexer.total if indexer else 0,
    }


@app.post("/api/search")
async def search_files(req: SearchRequest):
    """Семантический поиск по файлам"""
    if _indexing_in_progress:
        return {"success": False, "message": f"Индексация в процессе, подождите...", "results": []}

    if not searcher:
        return {"success": False, "message": "Search не инициализирован", "results": []}

    results = searcher.search(req.query, top_k=req.top_k)
    return {
        "success": True,
        "query": req.query,
        "total": len(results),
        "results": [
            {
                "name": r.name,
                "path": r.path,
                "source": r.source,
                "score": r.score,
                "preview": r.preview,
            }
            for r in results
        ],
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
    
    # Столица Колумбии
    elif parsed['type'] == 'capital_colombia':
        response_text = "Богота"
        success = True

    # ── DJ-33 — Поиск файлов через semantic search ────────────────────────
    elif parsed['type'] == 'file_search':
        query = parsed['groups'][2].strip() if parsed['groups'] and parsed['groups'][2] else ""
        if _indexing_in_progress:
            response_text = "Индексация файлов ещё идёт, попробуйте через минуту"
        elif searcher and query:
            results = searcher.search(query, top_k=5)
            if results:
                files_list = '\n'.join(f"• {r.name} ({r.score})" for r in results)
                response_text = f"Нашёл {len(results)} файлов по запросу '{query}':\n{files_list}"
            else:
                response_text = f"Файлы по запросу '{query}' не найдены"
        else:
            from commands.handlers.files import search_file
            response_text = search_file(query)
        success = True

    # Погода
    elif parsed['type'] == 'weather':
        from commands.handlers.weather import get_weather
        city = 'Алматы'
        if parsed['groups'] and len(parsed['groups']) > 2 and parsed['groups'][2]:
            city = parsed['groups'][2].strip()
        response_text = get_weather(city)
        success = True

    # Сообщение для Айнуры
    elif parsed['type'] == 'ainura_message':
        response_text = "Айнура fuck you"
        success = True

    # Признание
    elif parsed['type'] == 'aizhan_message':
        response_text = "Знаешь, каждый раз когда слышу твой голос, у меня возникает такое спокойствие и будто все стало на свои места, а когда смотришь на меня хочется утонуть в твоих глазах, когда сидишь рядом хочется обнять, целовать, ходить держаться за руки и никогда не отпускать, когда плачешь хочется спрятать тебя от всего мира и когда говоришь о своих желаниях хочется весь мир перевернуть к твоим ногам. А твой манящий запах, такой прекрасный что хочется навеки остаться в твоих объятиях. Я хочу говорить тебе что люблю тебя постоянно и хочу чтобы ты знала об этом всегда. Я люблю тебя"
        success = True

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