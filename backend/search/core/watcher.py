import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent

from search.core.indexer import Indexer
from search.sources.local import LocalDiskSource
from search.readers.registry import get_reader

logger = logging.getLogger(__name__)


class _FileEventHandler(FileSystemEventHandler):
    def __init__(self, indexer: Indexer, source: LocalDiskSource):
        self._indexer = indexer
        self._source = source

    # ── DJ-28 — новый файл ────────────────────────────────────────────────
    def on_created(self, event):
        if event.is_directory:
            return
        if get_reader(event.src_path) is None:
            return
        logger.info(f"Новый файл: {event.src_path}")
        self._index_file(event.src_path)

    # ── DJ-29 — файл изменён ──────────────────────────────────────────────
    def on_modified(self, event):
        if event.is_directory:
            return
        if get_reader(event.src_path) is None:
            return
        logger.info(f"Файл изменён: {event.src_path}")
        self._index_file(event.src_path)

    # ── DJ-30 — файл удалён ───────────────────────────────────────────────
    def on_deleted(self, event):
        if event.is_directory:
            return
        logger.info(f"Файл удалён: {event.src_path}")
        self._indexer.remove_file(event.src_path)
        self._indexer.save()

    def _index_file(self, path: str):
        from search.sources.base import FileInfo
        import os
        try:
            modified_at = os.path.getmtime(path)
        except OSError:
            return
        file = FileInfo(
            id=path,
            path=path,
            name=os.path.basename(path),
            source='local',
            modified_at=modified_at,
        )
        text = self._source.read_file(file)
        if text.strip():
            self._indexer.add_file(file, text)
            self._indexer.save()


class Watcher:
    def __init__(self, indexer: Indexer, source: LocalDiskSource):
        self._indexer = indexer
        self._source = source
        self._observer = Observer()
        self._thread: threading.Thread | None = None

    # ── DJ-31 — запуск фоновым потоком ───────────────────────────────────
    def start(self):
        handler = _FileEventHandler(self._indexer, self._source)
        for directory in self._source.search_dirs:
            self._observer.schedule(handler, directory, recursive=True)
            logger.info(f"Watcher следит за: {directory}")
        self._observer.start()
        logger.info("Watcher запущен")

    def stop(self):
        self._observer.stop()
        self._observer.join()
        logger.info("Watcher остановлен")
