from abc import ABC, abstractmethod


class BaseReader(ABC):
    @abstractmethod
    def read(self, filepath: str) -> str:
        """Читает файл и возвращает текст"""
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Возвращает список поддерживаемых расширений"""
        pass
