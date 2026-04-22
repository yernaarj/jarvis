import os
import json
import logging
import numpy as np
import faiss
from concurrent.futures import ThreadPoolExecutor, as_completed

from search.core.embedder import Embedder
from search.sources.base import BaseSource, FileInfo

logger = logging.getLogger(__name__)

FAISS_FILE = "faiss.index"
META_FILE  = "metadata.json"

# DJ-38: количество потоков для параллельного чтения файлов
READ_WORKERS = 8
# Размер батча для энкодера
ENCODE_BATCH = 64


def _file_id_to_int(file_id: str) -> int:
    """Хэш строкового ID в int64 для FAISS"""
    return abs(hash(file_id)) % (2 ** 63)


def _read_one(args) -> tuple[FileInfo, str]:
    """Воркер для ThreadPoolExecutor: читает один файл, возвращает (FileInfo, text)"""
    source, file = args
    try:
        text = source.read_file(file)
    except Exception as e:
        logger.error(f"Ошибка чтения {file.path}: {e}")
        text = ''
    return file, text


def _parallel_read(source: BaseSource, files: list[FileInfo]) -> list[tuple[FileInfo, str]]:
    """
    DJ-38: параллельное чтение файлов через ThreadPoolExecutor.
    executor.map сохраняет порядок — файлы и тексты останутся в одинаковом порядке.
    Возвращает только пары с непустым текстом.
    """
    if not files:
        return []

    logger.info(f"Читаем {len(files)} файлов в {READ_WORKERS} потоках...")
    args = [(source, f) for f in files]

    valid = []
    with ThreadPoolExecutor(max_workers=READ_WORKERS) as ex:
        for file, text in ex.map(_read_one, args):
            if text.strip():
                valid.append((file, text))

    logger.info(f"  Прочитано с текстом: {len(valid)}/{len(files)}")
    return valid


class Indexer:
    def __init__(self, index_dir: str, embedder: Embedder):
        self.index_dir = index_dir
        self.embedder = embedder
        self._faiss_path = os.path.join(index_dir, FAISS_FILE)
        self._meta_path  = os.path.join(index_dir, META_FILE)

        # metadata: file_id -> {name, path, source, modified_at, size, preview}
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
        dim  = 384  # multilingual-e5-small
        base = faiss.IndexFlatIP(dim)
        return faiss.IndexIDMap(base)

    # ── DJ-18 ─────────────────────────────────────────────────────────────
    def save(self):
        faiss.write_index(self._index, self._faiss_path)
        with open(self._meta_path, 'w', encoding='utf-8') as f:
            json.dump(
                {'meta': self._meta,
                 'id_map': {str(k): v for k, v in self._id_map.items()}},
                f, ensure_ascii=False,
            )
        logger.info(f"Индекс сохранён: {self._index.ntotal} векторов")

    # ── DJ-19 ─────────────────────────────────────────────────────────────
    def _load(self) -> faiss.Index:
        logger.info("Загружаем существующий индекс...")
        index = faiss.read_index(self._faiss_path)
        with open(self._meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._meta   = data['meta']
        self._id_map = {int(k): v for k, v in data['id_map'].items()}
        logger.info(f"Индекс загружен: {index.ntotal} векторов")
        return index

    # ── DJ-20 ─────────────────────────────────────────────────────────────
    def add_file(self, file: FileInfo, text: str):
        if not text.strip():
            return

        fid = _file_id_to_int(file.id)

        if file.id in self._meta:
            self._remove_by_fid(fid)

        vector = self.embedder.encode_document(text)
        vec_np = np.array([vector], dtype='float32')
        ids_np = np.array([fid],    dtype='int64')
        self._index.add_with_ids(vec_np, ids_np)

        self._meta[file.id] = {
            'name':        file.name,
            'path':        file.path,
            'source':      file.source,
            'modified_at': file.modified_at,
            'size':        file.size,          # DJ-37
            'preview':     text[:200],
        }
        self._id_map[fid] = file.id
        logger.info(f"Добавлен: {file.name}")

    # ── DJ-21 ─────────────────────────────────────────────────────────────
    def remove_file(self, file_id: str):
        if file_id not in self._meta:
            return
        fid = _file_id_to_int(file_id)
        self._remove_by_fid(fid)
        self._meta.pop(file_id,  None)
        self._id_map.pop(fid, None)
        logger.info(f"Удалён из индекса: {file_id}")

    def _remove_by_fid(self, fid: int):
        ids = faiss.IDSelectorArray(np.array([fid], dtype='int64'))
        self._index.remove_ids(ids)

    # ── DJ-22 — полная переиндексация ─────────────────────────────────────
    def reindex(self, source: BaseSource):
        logger.info("Полная переиндексация...")
        self._index.reset()
        self._meta.clear()
        self._id_map.clear()

        files = source.list_files()
        logger.info(f"Файлов для индексации: {len(files)}")

        # DJ-38: параллельное чтение
        pairs = _parallel_read(source, files)
        if not pairs:
            self.save()
            logger.info("Нет файлов с текстом для индексации")
            return

        valid_files = [f for f, _ in pairs]
        valid_texts = [t for _, t in pairs]

        # DJ-37: обрезаем по SEARCH_CHUNK_SIZE и кодируем батчами
        from config import settings
        truncated = [' '.join(t.split()[:settings.SEARCH_CHUNK_SIZE]) for t in valid_texts]

        all_vectors = []
        for i in range(0, len(truncated), ENCODE_BATCH):
            vecs = self.embedder.encode_batch(truncated[i:i + ENCODE_BATCH])
            all_vectors.extend(vecs)
            logger.info(f"  Закодировано {min(i + ENCODE_BATCH, len(truncated))}/{len(truncated)}")

        vec_np = np.array(all_vectors, dtype='float32')
        ids_np = np.array([_file_id_to_int(f.id) for f in valid_files], dtype='int64')
        self._index.add_with_ids(vec_np, ids_np)

        for file, text in zip(valid_files, valid_texts):
            fid = _file_id_to_int(file.id)
            self._meta[file.id] = {
                'name':        file.name,
                'path':        file.path,
                'source':      file.source,
                'modified_at': file.modified_at,
                'size':        file.size,       # DJ-37
                'preview':     text[:200],
            }
            self._id_map[fid] = file.id

        self.save()
        logger.info(f"Переиндексация завершена: {self._index.ntotal} векторов")

    # ── DJ-36 + DJ-37 — умная синхронизация ──────────────────────────────
    def sync(self, source: BaseSource):
        """
        Индексирует только новые/изменённые файлы, удаляет исчезнувшие.
        DJ-37: изменение определяется по mtime И size — оба должны совпасть,
               чтобы файл считался неизменённым.
        DJ-38: новые/изменённые файлы читаются параллельно.
        """
        logger.info("Синхронизация индекса...")
        files = source.list_files()
        current_ids = {f.id for f in files}

        # Удаляем файлы которых больше нет
        removed = [fid for fid in list(self._meta.keys()) if fid not in current_ids]
        for fid in removed:
            self.remove_file(fid)
            logger.info(f"Удалён: {fid}")

        # DJ-37: определяем изменённые по mtime + size
        to_index = []
        for file in files:
            stored = self._meta.get(file.id)
            if stored is None:
                to_index.append(file)
            else:
                mtime_changed = stored['modified_at'] != file.modified_at
                # DJ-37: если size ранее не сохранялся — считаем его совпавшим
                # (миграция со старого индекса без поля size)
                size_changed  = stored.get('size', file.size) != file.size
                if mtime_changed or size_changed:
                    to_index.append(file)

        skipped = len(files) - len(to_index)
        logger.info(f"Новых/изменённых: {len(to_index)}, пропущено: {skipped}")

        if not to_index:
            logger.info("Индекс актуален, ничего не изменилось")
            return

        # DJ-38: параллельное чтение только изменённых
        pairs = _parallel_read(source, to_index)

        if not pairs:
            self.save()
            logger.info("Синхронизация завершена: нет новых файлов с текстом")
            return

        valid_files = [f for f, _ in pairs]
        valid_texts = [t for _, t in pairs]

        from config import settings
        truncated = [' '.join(t.split()[:settings.SEARCH_CHUNK_SIZE]) for t in valid_texts]

        all_vectors = []
        for i in range(0, len(truncated), ENCODE_BATCH):
            vecs = self.embedder.encode_batch(truncated[i:i + ENCODE_BATCH])
            all_vectors.extend(vecs)

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
                'name':        file.name,
                'path':        file.path,
                'source':      file.source,
                'modified_at': file.modified_at,
                'size':        file.size,       # DJ-37
                'preview':     text[:200],
            }
            self._id_map[fid] = file.id

        self.save()
        logger.info(f"Синхронизация завершена: +{len(valid_files)}, итого {self._index.ntotal}")

    @property
    def total(self) -> int:
        return self._index.ntotal
