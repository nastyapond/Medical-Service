# Тесты проекта

## Основное

- `conftest.py` — общие фикстуры и конфигурация
- `requirements.txt` — зависимости для тестирования

### Pytest тесты (автоматические)

Эти тесты запускаются автоматически в CI/CD и при `pytest tests/`:

- `test_api.py` — тесты API endpoints и аутентификации
- `test_ml_service.py` — тесты ML сервиса  
- `test_models.py` — тесты ORM моделей (User, RefreshToken, etc.)
- `test_security.py` — функции безопасности и валидация
- `test_refresh_tokens.py` — токены обновления
- `test_runner.py` — тесты инференса RuBERT модели (пропускаются если модели не найдены)
- `test_integration.py`, `test_main.py`, `test_full_app.py`, `test_system.py` — интеграционные тесты

### Standalone скрипты (ручной запуск)

Эти скрипты предназначены для ручного тестирования и разработки (не собираются pytest):

- `test_model_simple.py` — простая проверка RuBERT модели (запустить: `python test_model_simple.py`)
- `test_model_ru.py` — расширенные тесты русскоязычной модели (запустить: `python test_model_ru.py`)
- `check_health.py` — проверка здоровья сервиса

## Установка

```bash
pip install -r requirements.txt
cd tests && pip install -r requirements.txt
```

## Запуск тестов

### Все pytest тесты (рекомендуется)

```bash
# Из корня проекта
pytest -v --cov=app --cov-report=xml

# Или из папки tests
cd tests && pytest .
```

### Конкретные тесты

```bash
# Только тесты API
pytest tests/test_api.py -v

# Только ML тесты
pytest tests/test_runner.py -v

# Только модели
pytest tests/test_models.py -v
```

### Standalone скрипты (ручной запуск)

```bash
# Проверка RuBERT модели (требует файлов модели)
python tests/test_model_simple.py

# Расширенные тесты
python tests/test_model_ru.py
```

## ML модель

Расположение обученной модели:

```
ml_service/medical_classifier_rubert/
├── pytorch_model.bin          # Веса модели
├── urgency_encoder.pkl        # Энкодер для urgency
├── request_type_encoder.pkl   # Энкодер для типа запроса
└── tokenizer.json             # Конфиг токенайзера
```

**Примечание:** Файлы модели исключены из git (`.gitignore`) и недоступны в CI.  
Тесты модели автоматически пропускаются если файлы не найдены.

## Переменные окружения

Для ML сервиса:

```bash
export MODEL_TYPE=rubert
```

Для frontend:

```bash
export REACT_APP_API_URL=http://localhost:8000
```

Для базы данных:

```bash
export DATABASE_URL=sqlite:///./test.db
```

Для CI/CD:

```bash
export SECRET_KEY="your-secret-key"
export REDIS_URL="redis://localhost:6379"
```

## CI/CD Pipeline

GitHub Actions автоматически запускает:

```bash
pytest -v --cov=app --cov-report=xml
```
 Собирает все 32 теста, пропускает тесты ML моделей если файлов нет, генерирует coverage отчет в `coverage.xml`
