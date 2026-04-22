import os
import logging
from .base import BaseSource, FileInfo
from search.readers.registry import get_reader

logger = logging.getLogger(__name__)

IGNORED_DIRS = {
    'appdata', 'windows', 'program files', 'program files (x86)',
    'node_modules', '.git', '__pycache__', '.vscode', '.cache', 'venv',
    '$recycle.bin', 'system volume information', 'programdata', 'perflogs',
    'onedrive', 'temp', 'tmp', 'cache',
}


def _scandir_recursive(root: str, files: list[FileInfo], source_name: str):
    """
    DJ-37: рекурсивный обход через os.scandir().
    DirEntry кеширует stat-данные — 1 syscall вместо 2 (listdir + stat).
    """
    try:
        with os.scandir(root) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name.lower() not in IGNORED_DIRS:
                        _scandir_recursive(entry.path, files, source_name)
                elif entry.is_file(follow_symlinks=False):
                    if get_reader(entry.path) is None:
                        continue
                    try:
                        stat = entry.stat()
                    except OSError:
                        continue
                    files.append(FileInfo(
                        id=entry.path,
                        path=entry.path,
                        name=entry.name,
                        source=source_name,
                        modified_at=stat.st_mtime,
                        size=stat.st_size,        # DJ-37: сохраняем размер
                    ))
    except PermissionError:
        pass
    except OSError as e:
        logger.warning(f"Ошибка обхода {root}: {e}")


class LocalDiskSource(BaseSource):
    def __init__(self, search_dirs: list[str]):
        self.search_dirs = search_dirs
        self.source_name = 'local'

    def list_files(self) -> list[FileInfo]:
        files: list[FileInfo] = []
        for directory in self.search_dirs:
            if not os.path.exists(directory):
                logger.warning(f"Папка не существует: {directory}")
                continue
            _scandir_recursive(directory, files, self.source_name)
        logger.debug(f"list_files: найдено {len(files)} файлов")
        return files

    def read_file(self, file: FileInfo) -> str:
        reader = get_reader(file.path)
        if reader is None:
            return ''
        try:
            return reader.read(file.path)
        except Exception as e:
            logger.error(f"Ошибка чтения {file.path}: {e}")
            return ''
