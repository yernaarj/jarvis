import webbrowser
import logging
import subprocess
import platform

logger = logging.getLogger(__name__)


def is_wsl():
    """Проверяет запущен ли код в WSL"""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False


def open_url_in_windows(url: str):
    """Открывает URL в браузере Windows из WSL"""
    try:
        # Используем cmd.exe для открытия URL в Windows
        subprocess.run(['cmd.exe', '/c', 'start', url], check=True)
        logger.info(f"✅ Открыт URL в Windows браузере: {url}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка открытия в Windows: {e}")
        # Fallback на explorer.exe
        try:
            subprocess.run(['explorer.exe', url], check=True)
            return True
        except:
            return False


def open_browser():
    """Открывает браузер по умолчанию"""
    url = 'https://www.google.com'
    
    try:
        if is_wsl():
            return open_url_in_windows(url)
        else:
            webbrowser.open(url)
            logger.info("✅ Браузер открыт")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка открытия браузера: {e}")
        return False


def google_search(query: str):
    """Поиск в Google"""
    search_url = f"https://www.google.com/search?q={query}"
    
    try:
        if is_wsl():
            return open_url_in_windows(search_url)
        else:
            webbrowser.open(search_url)
            logger.info(f"✅ Поиск в Google: {query}")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        return False


def youtube_search(query: str = ""):
    """Поиск на YouTube"""
    if query:
        youtube_url = f"https://www.youtube.com/results?search_query={query}"
    else:
        youtube_url = "https://www.youtube.com"
    
    try:
        if is_wsl():
            return open_url_in_windows(youtube_url)
        else:
            webbrowser.open(youtube_url)
            logger.info(f"✅ YouTube открыт: {query or 'главная страница'}")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка открытия YouTube: {e}")
        return False