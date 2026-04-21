import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from config import settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self):
        logger.info(f"Загрузка модели {settings.SEARCH_MODEL_NAME}...")
        self._model = SentenceTransformer(settings.SEARCH_MODEL_NAME)
        logger.info("Модель загружена")

    def encode(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()

    def chunk_text(self, text: str) -> list[str]:
        """Разбивает текст на чанки по SEARCH_CHUNK_SIZE слов с перекрытием 50 слов"""
        words = text.split()
        size = settings.SEARCH_CHUNK_SIZE
        overlap = 50
        if len(words) <= size:
            return [text]
        chunks = []
        start = 0
        while start < len(words):
            chunk = ' '.join(words[start:start + size])
            chunks.append(chunk)
            start += size - overlap
        return chunks

    def encode_document(self, text: str) -> list[float]:
        """Кодирует документ с учётом chunking — возвращает усреднённый вектор"""
        chunks = self.chunk_text(text)
        if len(chunks) == 1:
            return self.encode(chunks[0])
        vectors = self.encode_batch(chunks)
        avg = np.mean(vectors, axis=0)
        avg = avg / np.linalg.norm(avg)
        return avg.tolist()
