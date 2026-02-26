import logging
from datetime import datetime
import subprocess
import platform
import os

logger = logging.getLogger(__name__)


def is_wsl():
    """Проверяет запущен ли код в WSL"""
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except:
        return False


def get_current_time():
    """Возвращает текущее время"""
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    return time_str


def get_current_date():
    """Возвращает текущую дату"""
    now = datetime.now()
    # Форматируем на русском
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    day = now.day
    month = months[now.month - 1]
    year = now.year
    return f"{day} {month} {year} года"


def volume_up():
    """Увеличить громкость"""
    try:
        if is_wsl():
            # Используем PowerShell для управления громкостью Windows
            cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"  # VK_VOLUME_UP
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Windows":
            # Используем nircmd если установлен, иначе PowerShell
            try:
                subprocess.run(["nircmd.exe", "changesysvolume", "2000"], check=False)
            except:
                cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"
                subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Linux":
            subprocess.run(["amixer", "set", "Master", "5%+"], check=False)
        
        logger.info("✅ Громкость увеличена")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось изменить громкость: {e}")
        return False


def volume_down():
    """Уменьшить громкость"""
    try:
        if is_wsl():
            cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"  # VK_VOLUME_DOWN
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Windows":
            try:
                subprocess.run(["nircmd.exe", "changesysvolume", "-2000"], check=False)
            except:
                cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
                subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Linux":
            subprocess.run(["amixer", "set", "Master", "5%-"], check=False)
        
        logger.info("✅ Громкость уменьшена")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось изменить громкость: {e}")
        return False


def volume_mute():
    """Отключить/включить звук"""
    try:
        if is_wsl():
            cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"  # VK_VOLUME_MUTE
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Windows":
            try:
                subprocess.run(["nircmd.exe", "mutesysvolume", "2"], check=False)
            except:
                cmd = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                subprocess.run(['powershell.exe', '-Command', cmd], check=False)
        elif platform.system() == "Linux":
            subprocess.run(["amixer", "set", "Master", "toggle"], check=False)
        
        logger.info("✅ Звук переключен")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось переключить звук: {e}")
        return False


def take_screenshot():
    """Делает скриншот экрана"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if is_wsl():
            # Скриншот через Windows
            filename = f"screenshot_{timestamp}.png"
            # Сохраняем на рабочий стол Windows
            desktop_path = "/mnt/c/Users/$env:USERNAME/Desktop"
            cmd = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds | Out-Null; $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size); $bitmap.Save("$env:USERPROFILE\\Desktop\\{filename}"); $bitmap.Dispose(); $graphics.Dispose()'
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)
            logger.info(f"✅ Скриншот сохранен: {filename}")
            return True
        elif platform.system() == "Windows":
            # Windows скриншот
            filename = f"screenshot_{timestamp}.png"
            cmd = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds | Out-Null; $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size); $bitmap.Save("$env:USERPROFILE\\Desktop\\{filename}"); $bitmap.Dispose(); $graphics.Dispose()'
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)
            logger.info(f"✅ Скриншот сохранен на рабочем столе")
            return True
        else:
            # Linux скриншот
            subprocess.run(["scrot", f"screenshot_{timestamp}.png"], check=False)
            logger.info(f"✅ Скриншот сделан")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания скриншота: {e}")
        return False


def shutdown_pc():
    """Выключает компьютер"""
    try:
        if is_wsl():
            subprocess.run(['powershell.exe', '-Command', 'Stop-Computer -Force'], check=False)
        elif platform.system() == "Windows":
            subprocess.run(['shutdown', '/s', '/t', '0'], check=False)
        else:
            subprocess.run(['shutdown', '-h', 'now'], check=False)
        
        logger.info("✅ Выключение ПК...")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка выключения: {e}")
        return False


def lock_pc():
    """Блокирует компьютер"""
    try:
        if is_wsl():
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
        elif platform.system() == "Windows":
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
        else:
            subprocess.run(['gnome-screensaver-command', '-l'], check=False)
        
        logger.info("✅ Компьютер заблокирован")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка блокировки: {e}")
        return False