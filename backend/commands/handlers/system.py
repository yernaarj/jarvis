import logging
import subprocess
from datetime import datetime

from core.platform import SYSTEM

logger = logging.getLogger(__name__)


def get_current_time() -> str:
    return datetime.now().strftime("%H:%M")


def get_current_date() -> str:
    now = datetime.now()
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    return f"{now.day} {months[now.month - 1]} {now.year} года"


# ── CP-13/14/15 — Громкость ────────────────────────────────────────────────

def _ps_key(key_code: int):
    """Отправляет клавишу через PowerShell (Windows/WSL)"""
    cmd = f"(New-Object -ComObject WScript.Shell).SendKeys([char]{key_code})"
    subprocess.run(['powershell.exe', '-Command', cmd], check=False)


def volume_up() -> bool:
    try:
        if SYSTEM in ('wsl', 'windows'):
            _ps_key(175)  # VK_VOLUME_UP
        elif SYSTEM == 'linux':
            subprocess.run(['amixer', 'set', 'Master', '5%+'], check=False)
        elif SYSTEM == 'macos':
            subprocess.run(['osascript', '-e',
                            'set volume output volume (output volume of (get volume settings) + 10)'],
                           check=False)
        logger.info("✅ Громкость увеличена")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось изменить громкость: {e}")
        return False


def volume_down() -> bool:
    try:
        if SYSTEM in ('wsl', 'windows'):
            _ps_key(174)  # VK_VOLUME_DOWN
        elif SYSTEM == 'linux':
            subprocess.run(['amixer', 'set', 'Master', '5%-'], check=False)
        elif SYSTEM == 'macos':
            subprocess.run(['osascript', '-e',
                            'set volume output volume (output volume of (get volume settings) - 10)'],
                           check=False)
        logger.info("✅ Громкость уменьшена")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось изменить громкость: {e}")
        return False


def volume_mute() -> bool:
    try:
        if SYSTEM in ('wsl', 'windows'):
            _ps_key(173)  # VK_VOLUME_MUTE
        elif SYSTEM == 'linux':
            subprocess.run(['amixer', 'set', 'Master', 'toggle'], check=False)
        elif SYSTEM == 'macos':
            subprocess.run(['osascript', '-e',
                            'set volume output muted not (output muted of (get volume settings))'],
                           check=False)
        logger.info("✅ Звук переключен")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Не удалось переключить звук: {e}")
        return False


# ── CP-16 — Скриншот ───────────────────────────────────────────────────────

def take_screenshot() -> bool:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"

        if SYSTEM in ('wsl', 'windows'):
            cmd = (
                f'Add-Type -AssemblyName System.Windows.Forms; '
                f'$b = New-Object System.Drawing.Bitmap '
                f'([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width), '
                f'([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); '
                f'$g = [System.Drawing.Graphics]::FromImage($b); '
                f'$g.CopyFromScreen(0,0,0,0,$b.Size); '
                f'$b.Save("$env:USERPROFILE\\Desktop\\{filename}"); '
                f'$b.Dispose(); $g.Dispose()'
            )
            subprocess.run(['powershell.exe', '-Command', cmd], check=False)

        elif SYSTEM == 'linux':
            subprocess.run(['scrot', filename], check=False)

        elif SYSTEM == 'macos':
            subprocess.run(['screencapture', f'-f{filename}'], check=False)

        logger.info(f"✅ Скриншот сохранён: {filename}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка скриншота: {e}")
        return False


# ── CP-17/18/19 — Блокировка ──────────────────────────────────────────────

def lock_pc() -> bool:
    try:
        if SYSTEM in ('wsl', 'windows'):
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
        elif SYSTEM == 'linux':
            # Пробуем несколько вариантов
            for cmd in [['loginctl', 'lock-session'],
                        ['xdg-screensaver', 'lock'],
                        ['gnome-screensaver-command', '-l']]:
                try:
                    subprocess.run(cmd, check=True,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                    break
                except Exception:
                    continue
        elif SYSTEM == 'macos':
            subprocess.run(['osascript', '-e',
                            'tell application "System Events" to keystroke "q" '
                            'using {command down, control down}'],
                           check=False)
        logger.info("✅ Компьютер заблокирован")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка блокировки: {e}")
        return False


# ── CP-20/21/22 — Выключение ──────────────────────────────────────────────

def shutdown_pc() -> bool:
    try:
        if SYSTEM in ('wsl', 'windows'):
            subprocess.run(['powershell.exe', '-Command', 'Stop-Computer -Force'], check=False)
        elif SYSTEM == 'linux':
            subprocess.run(['shutdown', '-h', 'now'], check=False)
        elif SYSTEM == 'macos':
            subprocess.run(['osascript', '-e',
                            'tell app "System Events" to shut down'],
                           check=False)
        logger.info("✅ Выключение ПК...")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка выключения: {e}")
        return False
