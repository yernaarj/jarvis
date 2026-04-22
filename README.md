# DJarvis — Голосовой ИИ-ассистент

Голосовой ассистент с семантическим поиском по файлам. Принимает голосовые и текстовые команды, выполняет системные операции, ищет файлы по смыслу.

---

## Требования

- Python 3.12+
- 2GB RAM (для модели embeddings)
- ~1GB свободного места на диске

---

## Установка

### 1. Клонируй репозиторий

```bash
git clone <repo_url>
cd djarvis
```

### 2. Создай виртуальное окружение

```bash
python -m venv venv
```

### 3. Установи зависимости

```bash
pip install -r backend/requirements.txt
```

### 4. Создай `.env` файл

```bash
cd backend
cp .env.example .env
```

Открой `.env` и добавь ключ OpenWeatherMap (опционально):
```
OPENWEATHER_API_KEY=твой_ключ
```

---

## Запуск

### Windows (PowerShell)

```powershell
cd djarvis\backend
..\venv\Scripts\activate
python main.py
```

### Windows через WSL (Ubuntu)

```bash
cd ~/projects/djarvis/backend
source ../venv/bin/activate
python main.py
```

### Linux

```bash
cd djarvis/backend
source ../venv/bin/activate
python main.py
```

### macOS

```bash
cd djarvis/backend
source ../venv/bin/activate
python main.py
```

---

## Первый запуск

При первом запуске приложение автоматически проиндексирует файлы на:
- Desktop
- Downloads
- Documents

**Индексация занимает ~7 минут** (зависит от количества файлов). Это происходит **один раз** — при следующих запусках индекс загружается мгновенно.

Прогресс индексации можно отслеживать через:
```
GET http://127.0.0.1:49999/api/search/status
```

---

## API

После запуска документация доступна по адресу:
```
http://127.0.0.1:49999/docs
```

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/status` | Статус системы |
| GET | `/api/search/status` | Статус индекса |
| POST | `/api/search` | Семантический поиск по файлам |
| POST | `/api/command` | Текстовая команда |
| POST | `/api/voice-command` | Голосовая команда (микрофон) |
| POST | `/api/audio-command` | Голосовая команда (WAV файл) |

### Пример поиска

```bash
curl -X POST http://127.0.0.1:49999/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "договор с Яндексом", "top_k": 5}'
```

### Пример команды

```bash
curl -X POST http://127.0.0.1:49999/api/command \
  -H "Content-Type: application/json" \
  -d '{"text": "открой браузер"}'
```

---

## Поддерживаемые команды

| Команда | Пример |
|---------|--------|
| Браузер | "открой браузер" |
| Поиск Google | "найди котики" |
| YouTube | "ютуб найди музыка" |
| VS Code | "открой vscode" |
| Discord | "запусти discord" |
| Spotify | "включи spotify" |
| Калькулятор | "открой калькулятор" |
| Блокнот | "открой блокнот" |
| Проводник | "открой проводник" |
| Время | "который час" |
| Дата | "какое сегодня число" |
| Громкость | "громче / тише / отключи звук" |
| Скриншот | "сделай скриншот" |
| Блокировка | "заблокируй компьютер" |
| Погода | "какая погода в Алматы" |
| Поиск файлов | "найди файл договор" |

---

## Поддерживаемые форматы файлов для поиска

- `.txt`, `.md`, `.csv`, `.log`
- `.pdf`
- `.docx`
- `.xlsx`, `.xlsm`

---

## Платформы

| Платформа | Статус | Микрофон |
|-----------|--------|----------|
| Windows (нативно) | ✅ | ✅ |
| WSL (Ubuntu) | ✅ | ❌ (только API) |
| Linux | ✅ | ✅ |
| macOS | ✅ | ✅ |

---

## Структура проекта

```
djarvis/
├── backend/
│   ├── commands/          # Обработчики команд
│   │   └── handlers/
│   │       ├── apps.py    # Запуск приложений
│   │       ├── browser.py # Браузер и поиск
│   │       ├── system.py  # Системные команды
│   │       └── weather.py # Погода
│   ├── core/              # Ядро
│   │   ├── platform.py    # Определение платформы
│   │   ├── speech.py      # Распознавание речи
│   │   └── tts.py         # Синтез речи
│   ├── search/            # Семантический поиск
│   │   ├── core/          # Embedder, Indexer, Searcher, Watcher
│   │   ├── readers/       # Чтение PDF, DOCX, XLSX, TXT
│   │   └── sources/       # Источники (Local, Google Drive...)
│   ├── main.py            # Точка входа
│   ├── config.py          # Конфигурация
│   └── requirements.txt   # Зависимости
└── frontend/              # Фронтенд (отдельный репозиторий)
```
