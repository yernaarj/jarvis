import pdfplumber
from .base import BaseReader


class PdfReader(BaseReader):
    def read(self, filepath: str) -> str:
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return '\n'.join(text)

    def supported_extensions(self) -> list[str]:
        return ['.pdf']
