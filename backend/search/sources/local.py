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


class LocalDiskSource(BaseSource):
    def __init__(self, search_dirs: list[str]):
        self.search_dirs = search_dirs
        self.source_name = 'local'

    def list_files(self) -> list[FileInfo]:
        files = []
        for directory in self.search_dirs:
            if not os.path.exists(directory):
                logger.warning(f"Папка не существует: {directory}")
                continue
            for root, dirs, filenames in os.walk(directory):
                dirs[:] = [d for d in dirs if d.lower() not in IGNORED_DIRS]
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    if get_reader(filepath) is None:
                        continue
                    try:
                        modified_at = os.path.getmtime(filepath)
                    except OSError:
                        continue
                    files.append(FileInfo(
                        id=filepath,
                        path=filepath,
                        name=filename,
                        source=self.source_name,
                        modified_at=modified_at,
                    ))
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
