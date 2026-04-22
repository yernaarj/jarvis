import webbrowser
import subprocess
import logging

from core.platform import SYSTEM

logger = logging.getLogger(__name__)


def _open_url(url: str) -> bool:
    """Открывает URL кросс-платформенно — CP-09/10/11/12"""
    try:
        if SYSTEM == 'wsl':
            subprocess.Popen(['cmd.exe', '/c', 'start', url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        elif SYSTEM == 'windows':
            webbrowser.open(url)

        elif SYSTEM == 'linux':
            subprocess.Popen(['xdg-open', url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        elif SYSTEM == 'macos':
            subprocess.Popen(['open', url],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        else:
            webbrowser.open(url)

        logger.info(f"✅ Открыт URL ({SYSTEM}): {url}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка открытия URL: {e}")
        return False


def open_browser() -> bool:
    return _open_url('https://www.google.com')


def google_search(query: str) -> bool:
    return _open_url(f'https://www.google.com/search?q={query}')


def youtube_search(query: str = '') -> bool:
    url = f'https://www.youtube.com/results?search_query={query}' if query else 'https://www.youtube.com'
    return _open_url(url)
