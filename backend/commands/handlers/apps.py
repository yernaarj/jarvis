import subprocess
import logging
import os

from core.platform import SYSTEM, is_wsl, is_windows, is_linux, is_macos, get_home_dir

logger = logging.getLogger(__name__)

# ── CP-04/05/06/07 — Словарь приложений под каждую платформу ──────────────
APPS = {
    'vscode': {
        'windows': 'code',
        'wsl':     'code',
        'linux':   'code',
        'macos':   'code',
    },
    'code': {
        'windows': 'code',
        'wsl':     'code',
        'linux':   'code',
        'macos':   'code',
    },
    'discord': {
        'windows': r'C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe',
        'wsl':     r'C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe',
        'linux':   'discord',
        'macos':   'Discord',
    },
    'spotify': {
        'windows': 'spotify',
        'wsl':     'spotify',
        'linux':   'spotify',
        'macos':   'Spotify',
    },
    'notepad': {
        'windows': 'notepad',
        'wsl':     'notepad.exe',
        'linux':   'gedit',
        'macos':   'TextEdit',
    },
    'блокнот': {
        'windows': 'notepad',
        'wsl':     'notepad.exe',
        'linux':   'gedit',
        'macos':   'TextEdit',
    },
    'калькулятор': {
        'windows': 'calc',
        'wsl':     'calc.exe',
        'linux':   'gnome-calculator',
        'macos':   'Calculator',
    },
    'calculator': {
        'windows': 'calc',
        'wsl':     'calc.exe',
        'linux':   'gnome-calculator',
        'macos':   'Calculator',
    },
    'проводник': {
        'windows': 'explorer',
        'wsl':     'explorer.exe',
        'linux':   'nautilus',
        'macos':   'Finder',
    },
    'explorer': {
        'windows': 'explorer',
        'wsl':     'explorer.exe',
        'linux':   'nautilus',
        'macos':   'Finder',
    },
}


def open_application(app_name: str) -> bool:
    """Открывает приложение по имени — кросс-платформенно"""
    app_name_lower = app_name.lower()

    if app_name_lower not in APPS:
        logger.warning(f"Приложение '{app_name}' не найдено в списке")
        return False

    cmd = APPS[app_name_lower].get(SYSTEM)
    if not cmd:
        logger.warning(f"Приложение '{app_name}' не поддерживается на {SYSTEM}")
        return False

    try:
        # ── CP-04 — Windows нативно ────────────────────────────────────────
        if SYSTEM == 'windows':
            subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        # ── WSL — запускаем Windows приложение через cmd.exe ───────────────
        elif SYSTEM == 'wsl':
            subprocess.Popen(['cmd.exe', '/c', 'start', '', cmd],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        # ── CP-05 — Linux ──────────────────────────────────────────────────
        elif SYSTEM == 'linux':
            subprocess.Popen(cmd.split(),
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        # ── CP-06 — macOS ──────────────────────────────────────────────────
        elif SYSTEM == 'macos':
            subprocess.Popen(['open', '-a', cmd],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        logger.info(f"✅ Приложение {app_name} запущено ({SYSTEM})")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка запуска приложения {app_name}: {e}")
        return False


def open_folder(path: str = None) -> bool:
    """Открывает папку в проводнике — кросс-платформенно"""
    try:
        if path is None:
            path = get_home_dir()

        if SYSTEM == 'wsl':
            if path.startswith('/mnt/c'):
                windows_path = path.replace('/mnt/c', 'C:', 1).replace('/', '\\')
            else:
                windows_path = path
            subprocess.Popen(['explorer.exe', windows_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        elif SYSTEM == 'windows':
            os.startfile(path)

        elif SYSTEM == 'linux':
            subprocess.Popen(['xdg-open', path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        elif SYSTEM == 'macos':
            subprocess.Popen(['open', path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)

        logger.info(f"✅ Папка открыта: {path}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка открытия папки: {e}")
        return False
