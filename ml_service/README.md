# ML Classification Service

Сервис машинного обучения для классификации текстовых обращений пациентов с использованием современных моделей глубокого обучения.

## Поддерживаемые модели

### 1. RuBERT по умолчанию — РЕКОМЕНДУЕТСЯ

- **Модель**: DeepPavlov/rubert-base-cased
- **Структура**: BERT - двунаправленный трансформер
- **Метод**: Zero-shot классификация, не требует дообучения
- **Преимущества**:
  -  Высокая точность без дообучения
  -  Понимает контекст на русском языке
  -  Работает с неизвестными паттернами
  -  Не требует предварительной подготовки данных
- **Недостатки**:
  - Медленнее, примерно 2-3 сек на GPU, медленнее на CPU
  - Требует больше памяти

### 2. FastText

- **Модель**: Facebook FastText с эмбеддингами на русском
- **Структура**: Мелкая нейросеть с n-граммами
- **Метод**: Supervised learning, требует дообучения
- **Преимущества**:
  -  Очень быстрая inference (~10-50ms)
  -  Потребляет мало памяти
  -  Хорошо работает на маленьких датасетах
  -  Легко переобучать на новые данные
- **Недостатки**:
  - Требует дообучение на специфических данных
  - Не понимает контекст так хорошо как BERT

### 3. Mock (тестирование)

- Простая классификация по ключевым словам
- Используется для тестирования и резервного варианта

## Быстрый старт

### С RuBERT (рекомендуется)

```bash
# установка зависимостей
pip install -r requirements.txt

# запуск zero-shot RuBERT
MODEL_TYPE=rubert python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

### Fine-tune RuBERT на актуальном датасете

```bash
python train_rubert.py
python -m uvicorn main_finetuned:app --host 0.0.0.0 --port 5000
```

Модель использует данные из `../datasets/medical-symptom-triage/processed_ru.csv`.

### С FastText

```bash
# установка зависимостей для Windows
pip install -r requirements.txt
pip install fasttext

# обучение модели
python train_fasttext.py

# запуск
MODEL_TYPE=fasttext python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

### Docker

```bash
# RuBERT
docker build -t ml-service .
docker run -p 5000:5000 -e MODEL_TYPE=rubert ml-service

# FastText
docker run -p 5000:5000 -e MODEL_TYPE=fasttext ml-service
```

## API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "ok",
  "model_type": "rubert",
  "models_loaded": {
    "rubert": true,
    "fasttext_urgency": false,
    "fasttext_type": false
  }
}
```

### Classification
```
POST /classify
```

Request:
```json
{
  "text": "У меня болит голова, нужно срочно к врачу"
}
```

Response:
```json
{
  "urgency": "Экстренное",
  "request_type": "Запись на прием",
  "confidence": "Высокая"
}
```

## Классификационные категории

### Уровень срочности (urgency)

- **Экстренное**: Критическое состояние, требует немедленной помощи
  - Ключевые слова: "боль", "срочно", "немедленно", "скорая"
- **Срочное**: Требует внимания в течение дня
  - Ключевые слова: "сегодня", "быстро", "важно"
- **Плановое**: Можно отложить на несколько дней
  - Ключевые слова: "завтра", "скоро", "планово"
- **Консультационное**: Информационный запрос
  - Ключевые слова: "вопрос", "справка", "консультация"

### Тип обращения (request_type)

- **Запись на прием**: запись к врачу
- **Вызов врача**: Запрос вызова медработника на дом
- **Перенаправление в экстренные службы**: Требуется скорая помощь
- **Консультация или вопрос**: Просьба совета или информации
- **Наблюдение**: Запрос на диспансеризацию

### Уровень уверенности (confidence)

- **Высокая**: > 80% уверенность
- **Средняя**: 60-80% уверенности
- **Низкая**: < 60% уверенности

## Обучение FastText

### Подготовка данных

Создайте файл `data/urgency_train.txt` с форматом:
```
__label__Экстренное У меня критическая боль в груди
__label__Срочное Температура 40 градусов нужно к врачу
__label__Плановое Хочу приходить на прием завтра
```

### Обучение

```bash
python train_fasttext.py
```

Это создаст модели в папке `models/`:
- `models/urgency_model.bin` - модель классификации срочности
- `models/type_model.bin` - модель классификации типа запроса

### Использование обученных моделей

```bash
MODEL_TYPE=fasttext python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

## Логирование

Включено логирование на уровне INFO. Смотрите логи для отладки:

```
INFO:__main__:Classifying: У меня болит голова...
INFO:__main__:RuBERT: urgency=Экстренное (0.95), type=Запись на прием (0.87)
```

### Тестирование

```bash
# Локально
python -c "import requests; print(requests.post('http://localhost:5000/classify', json={'text': 'болит голова'}).json())"

# Через curl
curl -X POST http://localhost:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"text":"У меня боль в спине"}'
```

## Troubleshooting

### RuBERT не загружается

```
Failed to load RuBERT: ...
```

Решение: 
- Проверьте интернет соединение (требуется для скачивания модели)
- Убедитесь что установлены зависимости: `pip install -r requirements.txt`

### FastText ошибка на Windows

```
RuntimeError: pybind11 install failed
```

Решение:
- Установите Visual C++ Build Tools
- Или используйте RuBERT (рекомендуется для Windows)

## Production Deployment

### Docker Compose

```yaml
ml-service:
  build: ./ml_service
  ports:
    - "5000:5000"
  environment:
    - MODEL_TYPE=rubert
  restart: always
```

### Environment Variables

- `MODEL_TYPE`: "rubert", "fasttext", или "mock"
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (по умолчанию INFO)
```json
{
  "urgency": "Экстренное",
  "request_type": "Вызов врача",
  "confidence": "Высокая"
}
```

## Модели

Текущая реализация использует keyword-based классификацию.
Для продакшена интегрировать:
- FastText для быстрой baseline классификации
- RuBERT для точной трансформерной модели

## Запуск

```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

Или через Docker:
```bash
docker build -t ml-service .
docker run -p 5000:5000 ml-service
```