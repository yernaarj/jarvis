from docx import Document
from .base import BaseReader


class DocxReader(BaseReader):
    def read(self, filepath: str) -> str:
        doc = Document(filepath)
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())

    def supported_extensions(self) -> list[str]:
        return ['.docx', '.doc']
