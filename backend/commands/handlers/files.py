import os
import time
import subprocess
import logging

logger = logging.getLogger(__name__)

IGNORED_DIRS = {
    'appdata', 'windows', 'program files', 'program files (x86)',
    'node_modules', '.git', '__pycache__', '.vscode', '.cache', 'venv',
    '$recycle.bin', 'system volume information', 'programdata', 'perflogs',
    'onedrive', 'temp', 'tmp', 'cache',
}

# Папки по умолчанию — ищем только здесь
SEARCH_DIRS = [
    '/mnt/c/Users/user/Desktop',
    '/mnt/c/Users/user/Downloads',
    '/mnt/c/Users/user/Documents',
]

TIMEOUT_SEC = 10
MAX_DEPTH = 5
MAX_RESULTS = 5


def _search_in_dir(filename_lower: str, search_path: str, found: list, deadline: float):
    """Поиск в одной папке с таймаутом и ограничением глубины"""
    if not os.path.exists(search_path):
        logger.info(f"  ⚠️ Папка не существует: {search_path}")
        return

    logger.info(f"  📂 Сканирую: {search_path}")
    base_depth = search_path.rstrip('/').count('/')

    for root, dirs, files in os.walk(search_path):
        # Таймаут
        if time.time() > deadline:
            logger.warning(f"  ⏱ Таймаут при сканировании {root}")
            return

        # Ограничение глубины
        current_depth = root.count('/') - base_depth
        if current_depth >= MAX_DEPTH:
            dirs.clear()
            continue

        dirs[:] = [d for d in dirs if d.lower() not in IGNORED_DIRS]

        for file in files:
            if filename_lower in file.lower():
                full_path = os.path.join(root, file)
                found.append(full_path)
                logger.info(f"  📄 Найден: {full_path}")
                if len(found) >= MAX_RESULTS:
                    return

        if len(found) >= MAX_RESULTS:
            return


def search_file(filename: str, search_path: str = None) -> str:
    """Ищет файлы по имени в Desktop/Downloads/Documents с таймаутом"""
    logger.info(f"▶ search_file: filename='{filename}'")

    if not filename:
        return "Не указано имя файла для поиска"

    filename_lower = filename.lower()
    found = []
    deadline = time.time() + TIMEOUT_SEC

    search_dirs = [search_path] if search_path else SEARCH_DIRS

    for directory in search_dirs:
        if time.time() > deadline:
            logger.warning("⏱ Общий таймаут поиска")
            break
        _search_in_dir(filename_lower, directory, found, deadline)
        if found:
            break

    if not found:
        logger.info(f"⚠️ Файл '{filename}' не найден")
        return f"Файл '{filename}' не найден"

    logger.info(f"✅ Найдено {len(found)}. Открываю: {found[0]}")

    # Открываем первый найденный файл через explorer.exe
    try:
        win_path = found[0].replace('/mnt/c/', 'C:\\').replace('/', '\\')
        logger.info(f"🖥 explorer.exe {win_path}")
        subprocess.Popen(['explorer.exe', win_path])
    except Exception as e:
        logger.error(f"❌ Не удалось открыть файл: {e}", exc_info=True)

    result = f"Нашёл {len(found)} файлов по запросу '{filename}':\n"
    result += "\n".join(found)
    return result
