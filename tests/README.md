# Тесты проекта

## Основное

- `tests/conftest.py` содержит общие фикстуры
- `tests/requirements.txt` содержит зависимости для тестирования
- `tests/test_api.py` проверяет API
- `tests/test_ml_service.py` проверяет ML сервис
- `tests/test_model_simple.py` проверяет обученную RuBERT модель
- `tests/test_model_ru.py` содержит дополнительные проверки русскоязычной модели
- `tests/test_runner.py` запускает набор тестов модели
- `tests/test_models.py`, `tests/test_security.py`, `tests/test_refresh_tokens.py` проверяют бизнес-логику
- `tests/test_system.py` и `tests/test_integration.py` проверяют взаимодействие компонентов

## Установка

```bash
pip install -r requirements.txt
cd tests && pip install -r requirements.txt
```

## Запуск тестов

Из корня проекта:

```bash
pytest tests/
```

Из папки `tests`:

```bash
cd tests && pytest .
```

Запуск с коротким выводом:

```bash
pytest tests/ -v --tb=short
```

Запуск конкретного теста:

```bash
pytest tests/test_api.py -v
pytest tests/test_model_simple.py -v
```

## ML модель

Расположение обученной модели:

- `ml_service/medical_classifier_rubert/`

Проверка модели:

```bash
python tests/test_model_simple.py
```

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

## Быстрая проверка путей

```bash
python -c "import torch, transformers; print('ok')"
python tests/test_model_simple.py
pytest tests/test_api.py -v
pytest tests/ -v --tb=short
```
