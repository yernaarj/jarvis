import os
import json
import logging
import numpy as np
import faiss

from search.core.embedder import Embedder
from search.sources.base import BaseSource, FileInfo

logger = logging.getLogger(__name__)

FAISS_FILE = "faiss.index"
META_FILE = "metadata.json"


def _file_id_to_int(file_id: str) -> int:
    """Хэш строкового ID в int64 для FAISS"""
    return abs(hash(file_id)) % (2 ** 63)


class Indexer:
    def __init__(self, index_dir: str, embedder: Embedder):
        self.index_dir = index_dir
        self.embedder = embedder
        self._faiss_path = os.path.join(index_dir, FAISS_FILE)
        self._meta_path = os.path.join(index_dir, META_FILE)

        # metadata: file_id -> {name, path, source, modified_at, preview}
        self._meta: dict[str, dict] = {}
        # обратный маппинг: faiss_int_id -> file_id
        self._id_map: dict[int, str] = {}

        os.makedirs(index_dir, exist_ok=True)
        self._index = self._load_or_create()

    # ── DJ-17 ─────────────────────────────────────────────────────────────
    def _load_or_create(self) -> faiss.Index:
        if os.path.exists(self._faiss_path) and os.path.exists(self._meta_path):
            return self._load()
        logger.info("Создаём новый FAISS индекс")
        dim = 384  # multilingual-e5-small
        base = faiss.IndexFlatIP(dim)
        index = faiss.IndexIDMap(base)
        return index

    # ── DJ-18 ─────────────────────────────────────────────────────────────
    def save(self):
        faiss.write_index(self._index, self._faiss_path)
        with open(self._meta_path, 'w', encoding='utf-8') as f:
            json.dump({'meta': self._meta, 'id_map': {str(k): v for k, v in self._id_map.items()}}, f, ensure_ascii=False)
        logger.info(f"Индекс сохранён: {self._index.ntotal} векторов")

    # ── DJ-19 ─────────────────────────────────────────────────────────────
    def _load(self) -> faiss.Index:
        logger.info("Загружаем существующий индекс...")
        index = faiss.read_index(self._faiss_path)
        with open(self._meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._meta = data['meta']
        self._id_map = {int(k): v for k, v in data['id_map'].items()}
        logger.info(f"Индекс загружен: {index.ntotal} векторов")
        return index

    # ── DJ-20 ─────────────────────────────────────────────────────────────
    def add_file(self, file: FileInfo, text: str):
        if not text.strip():
            return

        fid = _file_id_to_int(file.id)

        # Если файл уже есть — удаляем старый вектор
        if file.id in self._meta:
            self._remove_by_fid(fid)

        vector = self.embedder.encode_document(text)
        vec_np = np.array([vector], dtype='float32')
        ids_np = np.array([fid], dtype='int64')
        self._index.add_with_ids(vec_np, ids_np)

        self._meta[file.id] = {
            'name': file.name,
            'path': file.path,
            'source': file.source,
            'modified_at': file.modified_at,
            'preview': text[:200],
        }
        self._id_map[fid] = file.id
        logger.info(f"Добавлен: {file.name}")

    # ── DJ-21 ─────────────────────────────────────────────────────────────
    def remove_file(self, file_id: str):
        if file_id not in self._meta:
            return
        fid = _file_id_to_int(file_id)
        self._remove_by_fid(fid)
        self._meta.pop(file_id, None)
        self._id_map.pop(fid, None)
        logger.info(f"Удалён из индекса: {file_id}")

    def _remove_by_fid(self, fid: int):
        ids = faiss.IDSelectorArray(np.array([fid], dtype='int64'))
        self._index.remove_ids(ids)

    # ── DJ-22 ─────────────────────────────────────────────────────────────
    def reindex(self, source: BaseSource):
        logger.info("Полная переиндексация...")
        self._index.reset()
        self._meta.clear()
        self._id_map.clear()

        files = source.list_files()
        logger.info(f"Файлов для индексации: {len(files)}")

        # Шаг 1: читаем все файлы
        valid_files = []
        valid_texts = []
        for file in files:
            text = source.read_file(file)
            if text.strip():
                valid_files.append(file)
                valid_texts.append(text)

        logger.info(f"Файлов с текстом: {len(valid_files)}")

        # Шаг 2: обрезаем до 512 слов и кодируем батчами
        from config import settings
        truncated = [' '.join(t.split()[:settings.SEARCH_CHUNK_SIZE]) for t in valid_texts]

        BATCH = 64
        all_vectors = []
        for i in range(0, len(truncated), BATCH):
            vecs = self.embedder.encode_batch(truncated[i:i + BATCH])
            all_vectors.extend(vecs)
            logger.info(f"  Закодировано {min(i + BATCH, len(truncated))}/{len(truncated)}")

        # Шаг 3: добавляем все векторы в FAISS за один раз
        import numpy as np
        vec_np = np.array(all_vectors, dtype='float32')
        ids_np = np.array([_file_id_to_int(f.id) for f in valid_files], dtype='int64')
        self._index.add_with_ids(vec_np, ids_np)

        for file, text in zip(valid_files, valid_texts):
            fid = _file_id_to_int(file.id)
            self._meta[file.id] = {
                'name': file.name,
                'path': file.path,
                'source': file.source,
                'modified_at': file.modified_at,
                'preview': text[:200],
            }
            self._id_map[fid] = file.id

        self.save()
        logger.info(f"Переиндексация завершена: {self._index.ntotal} векторов")

    # ── DJ-36 — умная синхронизация (пропуск неизменённых) ────────────────
    def sync(self, source: BaseSource):
        """Индексирует только новые/изменённые файлы, удаляет исчезнувшие"""
        logger.info("Синхронизация индекса...")
        files = source.list_files()
        current_ids = {f.id for f in files}

        # Удаляем файлы которых больше нет
        removed = [fid for fid in list(self._meta.keys()) if fid not in current_ids]
        for fid in removed:
            self.remove_file(fid)
            logger.info(f"Удалён: {fid}")

        # Индексируем только новые или изменённые
        to_index = []
        for file in files:
            existing = self._meta.get(file.id)
            if existing is None or existing['modified_at'] != file.modified_at:
                to_index.append(file)

        logger.info(f"Новых/изменённых: {len(to_index)}, пропущено: {len(files) - len(to_index)}")

        if not to_index:
            logger.info("Индекс актуален, ничего не изменилось")
            return

        valid_files = []
        valid_texts = []
        for file in to_index:
            text = source.read_file(file)
            if text.strip():
                valid_files.append(file)
                valid_texts.append(text)

        if not valid_files:
            self.save()
            logger.info("Синхронизация завершена: нет новых файлов")
            return

        from config import settings
        truncated = [' '.join(t.split()[:settings.SEARCH_CHUNK_SIZE]) for t in valid_texts]

        BATCH = 64
        all_vectors = []
        for i in range(0, len(truncated), BATCH):
            vecs = self.embedder.encode_batch(truncated[i:i + BATCH])
            all_vectors.extend(vecs)

        import numpy as np
        vec_np = np.array(all_vectors, dtype='float32')
        ids_np = np.array([_file_id_to_int(f.id) for f in valid_files], dtype='int64')

        # Удаляем старые версии перед добавлением новых
        for file in valid_files:
            if file.id in self._meta:
                self._remove_by_fid(_file_id_to_int(file.id))

        self._index.add_with_ids(vec_np, ids_np)

        for file, text in zip(valid_files, valid_texts):
            fid = _file_id_to_int(file.id)
            self._meta[file.id] = {
                'name': file.name,
                'path': file.path,
                'source': file.source,
                'modified_at': file.modified_at,
                'preview': text[:200],
            }
            self._id_map[fid] = file.id

        self.save()
        logger.info(f"Синхронизация завершена: добавлено {len(valid_files)}, итого {self._index.ntotal}")

    @property
    def total(self) -> int:
        return self._index.ntotal
