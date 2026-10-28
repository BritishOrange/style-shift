# StyleShift

Локальный сервис смены стиля текста. Работает на вашем компьютере, использует
предобученную модель Qwen2.5-1.5B-Instruct.

## Что нужно

- Python **3.12–3.14**
- [Poetry](https://python-poetry.org/docs/#installation) 2.x
- ~3–4 ГБ свободного места на диске (зависимости + модель)
- Интернет при первом запуске (скачивание модели с Hugging Face)
- Рекомендуется 8+ ГБ оперативной памяти

## Быстрый старт (Windows)

1. Склонируйте репозиторий и перейдите в каталог:

```bash
git clone https://github.com/BritishOrange/style-shift.git
cd style-shift
```

2. Запустите `start.bat` двойным кликом
   или в терминале:

```bash
start.bat
```

Скрипт создаст in-project виртуальное окружение `.venv`, установит зависимости
через Poetry и запустит сервис.

3. Дождитесь в консоли сообщения `Model is ready.`
   При первом запуске загрузка модели может занять несколько минут.

4. Откройте в браузере: [http://localhost:3000](http://localhost:3000)

## Установка и запуск через Poetry

```bash
git clone https://github.com/BritishOrange/style-shift.git
cd style-shift

# Poetry создаёт .venv внутри репозитория (см. poetry.toml)
poetry install

# Одноразово: подключить git-хуки линтеров
poetry run pre-commit install

# Запуск сервиса
poetry run styleshift
# или:
poetry run python -m styleshift
```

Откройте [http://localhost:3000](http://localhost:3000).

Активация окружения вручную (опционально):

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

## Качество кода

Проект использует production-стек для Python ML:

| Инструмент   | Назначение                                      |
|--------------|-------------------------------------------------|
| **Poetry**   | зависимости, lock-файл, in-project `.venv`      |
| **Ruff**     | линтер + форматтер                              |
| **Mypy**     | статическая проверка типов                      |
| **pre-commit** | хуки перед каждым коммитом                    |

Проверка вручную:

```bash
poetry run ruff check src
poetry run ruff format --check src
poetry run mypy
poetry run pre-commit run --all-files
```

## Как пользоваться

1. Введите текст.
2. Выберите стиль (академический, деловой, неформальный и т.д.).
3. Дождитесь статуса «Модель готова».
4. Нажмите «Перефразировать».

## Важно

- Модель **не входит** в репозиторий: она скачивается при первом запуске.
- Повторные запуски быстрее — модель берётся из кэша Hugging Face.
- Сервис слушает только `localhost`.
- На CPU генерация может занимать несколько секунд.
- Виртуальное окружение `.venv` создаётся **внутри** репозитория (`poetry.toml`),
  но сами бинарные пакеты в Git не коммитятся — воспроизводимость даёт
  `poetry.lock`.

## Структура

```
pyproject.toml          # Poetry: зависимости и настройки линтеров
poetry.lock             # зафиксированные версии (коммитится в Git)
poetry.toml             # in-project virtualenv (.venv в корне репо)
.pre-commit-config.yaml # git-хуки: ruff, mypy, базовые проверки
src/styleshift/         # пакет приложения
  __main__.py           # точка входа
  app.py                # Flask factory + API
  model.py              # загрузка модели и инференс
  styles.py             # описания стилей
  config.py             # конфигурация из env
public/                 # веб-интерфейс
start.bat               # быстрый запуск на Windows
app.py                  # совместимый лаунчер
```

## Переменные окружения

Скопируйте `.env.example` → `.env` при необходимости:

- `STYLESHIFT_MODEL_ID` — Hugging Face model id
- `STYLESHIFT_HOST` / `STYLESHIFT_PORT` — адрес сервера
- `STYLESHIFT_MAX_TEXT_LENGTH` — лимит длины текста
