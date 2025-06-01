# Тесты для Finance Bot

## Настройка PostgreSQL для тестов

### 1. Установка PostgreSQL

Для Windows:
```bash
# Скачайте PostgreSQL с официального сайта:
# https://www.postgresql.org/download/windows/
# Или через Chocolatey:
choco install postgresql
```

Для Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Для macOS:
```bash
brew install postgresql
brew services start postgresql
```

### 2. Создание тестовой базы данных

#### Автоматическое создание (рекомендуется)

**Для Windows:**
```cmd
# Запустите batch файл
scripts\setup_test_db.bat
```

**Для Linux/macOS:**
```bash
# Используйте SQL скрипт
psql -U postgres -f scripts/setup_test_db.sql
```

#### Ручное создание

**Для Windows:**
```cmd
# Откройте Command Prompt как администратор
# Подключитесь к PostgreSQL (замените путь на ваш)
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres

# В psql выполните:
CREATE DATABASE test_finance_bot;
\q
```

**Для Linux/macOS:**
```bash
# Создайте базу данных
sudo -u postgres createdb test_finance_bot

# Или через psql:
sudo -u postgres psql
CREATE DATABASE test_finance_bot;
\q
```

#### Быстрое создание одной командой

**Windows:**
```cmd
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -c "DROP DATABASE IF EXISTS test_finance_bot; CREATE DATABASE test_finance_bot;"
```

**Linux/macOS:**
```bash
psql -U postgres -f scripts/quick_setup.sql
```

### 3. Переменные окружения

**Для Windows (Command Prompt):**
```cmd
set TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_finance_bot
```

**Для Windows (PowerShell):**
```powershell
$env:TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_finance_bot"
```

**Для Linux/macOS:**
```bash
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_finance_bot
```

Или создайте файл `.env.test` в корне проекта:
```env
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_finance_bot
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 5. Запуск тестов

```bash
# Все тесты
pytest

# Только тесты базы данных
pytest -m database

# С покрытием кода
pytest --cov=app

# Подробный вывод
pytest -v

# Только определенный файл
pytest tests/test_models.py
```

## Структура тестов

- `conftest.py` - Конфигурация фикстур для PostgreSQL
- `test_models.py` - Тесты SQLAlchemy моделей
- `test_queries.py` - Тесты запросов к базе данных  
- `test_database.py` - Тесты настройки базы данных

## Скрипты для настройки

- `scripts/setup_test_db.sql` - Полный SQL скрипт создания тестовой БД
- `scripts/quick_setup.sql` - Быстрое создание БД (минимум команд)
- `scripts/setup_test_db.bat` - Batch файл для Windows (автопоиск psql)

## Покрытие тестами

Проект настроен на минимальное покрытие 80%. Отчет генерируется в `htmlcov/index.html`.

## Docker для тестов (альтернатива)

Если не хотите устанавливать PostgreSQL локально:

```bash
# Запуск PostgreSQL в Docker
docker run --name test-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=test_finance_bot \
  -p 5432:5432 \
  -d postgres:15

# Остановка контейнера
docker stop test-postgres
docker rm test-postgres
```

## Быстрый старт для Windows

1. Установите PostgreSQL
2. Запустите: `scripts\setup_test_db.bat`
3. Выполните:
```cmd
pip install -r requirements.txt
pytest
``` 