from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FileInfo:
    id: str        # уникальный идентификатор (обычно полный путь)
    path: str      # путь или ссылка на файл
    name: str      # имя файла
    source: str    # название источника: 'local', 'google_drive', etc.
    modified_at: float  # timestamp последнего изменения
    size: int = 0  # размер файла в байтах (DJ-37)


class BaseSource(ABC):
    @abstractmethod
    def list_files(self) -> list[FileInfo]:
        """Возвращает список всех файлов из источника"""
        pass

    @abstractmethod
    def read_file(self, file: FileInfo) -> str:
        """Читает текст из файла"""
        pass
