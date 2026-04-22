import os
import platform
import logging

logger = logging.getLogger(__name__)


def get_system() -> str:
    """Возвращает: 'windows', 'linux', 'macos', 'wsl'"""
    system = platform.system().lower()

    if system == 'linux':
        try:
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return 'wsl'
        except Exception:
            pass
        return 'linux'

    if system == 'darwin':
        return 'macos'

    if system == 'windows':
        return 'windows'

    return 'unknown'


# Определяем один раз при импорте
SYSTEM = get_system()
logger.info(f"Платформа: {SYSTEM}")


def get_home_dir() -> str:
    if SYSTEM == 'wsl':
        user = os.environ.get('USER', 'user')
        return f'/mnt/c/Users/{user}'
    return os.path.expanduser('~')


def get_desktop() -> str:
    return os.path.join(get_home_dir(), 'Desktop')


def get_downloads() -> str:
    return os.path.join(get_home_dir(), 'Downloads')


def get_documents() -> str:
    return os.path.join(get_home_dir(), 'Documents')


def get_search_dirs() -> list[str]:
    return [get_desktop(), get_downloads(), get_documents()]


def is_wsl() -> bool:
    return SYSTEM == 'wsl'


def is_windows() -> bool:
    return SYSTEM in ('windows', 'wsl')


def is_linux() -> bool:
    return SYSTEM == 'linux'


def is_macos() -> bool:
    return SYSTEM == 'macos'
