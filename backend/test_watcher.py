"""
Тест Этапа 6 — Watcher
Запуск: python test_watcher.py
"""
import os
import sys
import time
import shutil
sys.path.insert(0, os.path.dirname(__file__))

from search.core.embedder import Embedder
from search.core.indexer import Indexer
from search.core.searcher import Searcher
from search.core.watcher import Watcher
from search.sources.local import LocalDiskSource

INDEX_DIR = "/tmp/test_jarvis_watcher"
WATCH_DIR = "/tmp/test_jarvis_files"

if os.path.exists(INDEX_DIR):
    shutil.rmtree(INDEX_DIR)
if os.path.exists(WATCH_DIR):
    shutil.rmtree(WATCH_DIR)
os.makedirs(WATCH_DIR)

embedder = Embedder()
indexer = Indexer(index_dir=INDEX_DIR, embedder=embedder)
source = LocalDiskSource([WATCH_DIR])
searcher = Searcher(indexer=indexer, embedder=embedder)
watcher = Watcher(indexer=indexer, source=source)

watcher.start()
print("Watcher запущен\n")

# 1. DJ-28 — создание файла
print("=== DJ-28: создаём файл ===")
with open(f"{WATCH_DIR}/яндекс.txt", 'w', encoding='utf-8') as f:
    f.write("Договор с компанией Яндекс на поставку услуг.")
time.sleep(2)
print(f"Файлов в индексе: {indexer.total} (ожидается 1)")

# 2. Поиск по новому файлу
print("\n=== Поиск после создания ===")
results = searcher.search("Яндекс", top_k=5)
for r in results:
    print(f"  [{r.score}] {r.name}")

# 3. DJ-29 — изменение файла
print("\n=== DJ-29: изменяем файл ===")
with open(f"{WATCH_DIR}/яндекс.txt", 'w', encoding='utf-8') as f:
    f.write("Обновлённый договор с Яндексом. Добавлены новые условия.")
time.sleep(2)
results = searcher.search("Яндекс", top_k=5)
print(f"Файлов в индексе: {indexer.total} (ожидается 1, не 2)")
for r in results:
    print(f"  [{r.score}] {r.name} — {r.preview[:60]}")

# 4. DJ-30 — удаление файла
print("\n=== DJ-30: удаляем файл ===")
os.remove(f"{WATCH_DIR}/яндекс.txt")
time.sleep(2)
print(f"Файлов в индексе: {indexer.total} (ожидается 0)")

watcher.stop()

shutil.rmtree(INDEX_DIR)
shutil.rmtree(WATCH_DIR)

print("\n✅ Этап 6 — OK")
