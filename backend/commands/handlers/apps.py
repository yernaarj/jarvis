import subprocess
import logging
import os
import platform

logger = logging.getLogger(__name__)


def is_wsl():
    """Проверяет запущен ли код в WSL"""
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except:
        return False


def open_application(app_name: str):
    """Открывает приложение по имени"""
    
    # Словарь приложений и их путей/команд
    apps = {
        'vscode': {
            'windows': 'code',
            'linux': 'code'
        },
        'code': {
            'windows': 'code',
            'linux': 'code'
        },
        'discord': {
            'windows': r'C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe',
            'linux': 'discord'
        },
        'telegram': {
            'windows': 'telegram',
            'linux': 'telegram-desktop'
        },
        'spotify': {
            'windows': 'spotify',
            'linux': 'spotify'
        },
        'notepad': {
            'windows': 'notepad',
            'linux': 'gedit'
        },
        'блокнот': {
            'windows': 'notepad',
            'linux': 'gedit'
        },
        'калькулятор': {
            'windows': 'calc',
            'linux': 'gnome-calculator'
        },
        'calculator': {
            'windows': 'calc',
            'linux': 'gnome-calculator'
        },
        'проводник': {
            'windows': 'explorer',
            'linux': 'nautilus'
        },
        'explorer': {
            'windows': 'explorer',
            'linux': 'nautilus'
        }
    }
    
    app_name_lower = app_name.lower()
    
    if app_name_lower not in apps:
        logger.warning(f"Приложение '{app_name}' не найдено в списке")
        return False
    
    try:
        if is_wsl():
            # Запускаем через Windows из WSL
            cmd = apps[app_name_lower]['windows']
            # Расширяем переменные окружения
            cmd = os.path.expandvars(cmd)
            subprocess.Popen(['cmd.exe', '/c', 'start', '', cmd], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            logger.info(f"✅ Приложение {app_name} запущено (WSL)")
            return True
        else:
            # Нативный запуск
            system = platform.system()
            cmd = apps[app_name_lower].get('windows' if system == 'Windows' else 'linux')
            
            if system == 'Windows':
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(cmd.split())
            
            logger.info(f"✅ Приложение {app_name} запущено")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска приложения {app_name}: {e}")
        return False


def open_folder(path: str = None):
    """Открывает папку в проводнике"""
    try:
        if path is None:
            # Открываем домашнюю папку
            if is_wsl():
                path = '/mnt/c/Users'
            else:
                path = os.path.expanduser('~')
        
        if is_wsl():
            # Конвертируем WSL путь в Windows путь если нужно
            if path.startswith('/mnt/c'):
                windows_path = path.replace('/mnt/c', 'C:', 1).replace('/', '\\')
            else:
                windows_path = path
            
            subprocess.run(['explorer.exe', windows_path], check=True)
        else:
            if platform.system() == 'Windows':
                os.startfile(path)
            else:
                subprocess.run(['xdg-open', path])
        
        logger.info(f"✅ Папка открыта: {path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка открытия папки: {e}")
        return False