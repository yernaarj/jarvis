import logging
import numpy as np
from dataclasses import dataclass

from search.core.embedder import Embedder
from search.core.indexer import Indexer

logger = logging.getLogger(__name__)

MIN_SCORE = 0.89


@dataclass
class SearchResult:
    file_id: str
    name: str
    path: str
    source: str
    score: float
    preview: str


class Searcher:
    def __init__(self, indexer: Indexer, embedder: Embedder):
        self._indexer = indexer
        self._embedder = embedder

    # ── DJ-24 ─────────────────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        if self._indexer.total == 0:
            logger.warning("Индекс пустой")
            return []

        vector = self._embedder.encode(query)
        vec_np = np.array([vector], dtype='float32')

        k = min(top_k, self._indexer.total)
        scores, ids = self._indexer._index.search(vec_np, k)

        results = []
        for score, fid in zip(scores[0], ids[0]):
            if fid == -1:
                continue

            # ── DJ-25 — порог score ────────────────────────────────────────
            if score < MIN_SCORE:
                continue

            file_id = self._indexer._id_map.get(int(fid))
            if file_id is None:
                continue

            meta = self._indexer._meta.get(file_id)
            if meta is None:
                continue

            # ── DJ-26 — полный Result ──────────────────────────────────────
            results.append(SearchResult(
                file_id=file_id,
                name=meta['name'],
                path=meta['path'],
                source=meta['source'],
                score=round(float(score), 4),
                preview=meta['preview'],
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        logger.info(f"Запрос '{query}': найдено {len(results)} результатов")
        return results
