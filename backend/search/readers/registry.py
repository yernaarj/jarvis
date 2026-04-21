import os
from .base import BaseReader
from .txt import TxtReader
from .pdf import PdfReader
from .docx import DocxReader
from .xlsx import XlsxReader

_readers: list[BaseReader] = [
    TxtReader(),
    PdfReader(),
    DocxReader(),
    XlsxReader(),
]

_registry: dict[str, BaseReader] = {
    ext: reader
    for reader in _readers
    for ext in reader.supported_extensions()
}


def get_reader(filepath: str) -> BaseReader | None:
    ext = os.path.splitext(filepath)[1].lower()
    return _registry.get(ext)
