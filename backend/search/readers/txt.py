from .base import BaseReader


class TxtReader(BaseReader):
    def read(self, filepath: str) -> str:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def supported_extensions(self) -> list[str]:
        return ['.txt', '.md', '.csv', '.log']
