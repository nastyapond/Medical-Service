# Медицинский Сервис Обработки Запросов

Полнофункциональная система медицинских запросов с интеграцией ML-классификации для анализа и маршрутизации обращений пациентов.

## Возможности

- Аутентификация: JWT токены, регистрация/авторизация пользователей
- ML Классификация: Анализ обращений пациентов с определением срочности и типа
- Управление записями: Создание и управление записями к врачам
- Уведомления: Система уведомлений для пользователей
- Справочник врачей: Просмотр информации о врачах
- Современный интерфейс: React + Ant Design с адаптивным дизайном
- Полное тестирование: Unit и интеграционные тесты
- Контейнеризация: Docker Compose для простого развертывания

## Быстрый старт

### Docker Compose (Рекомендуется)

Запуск из папки src/

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd medical-service

# 2. Запустить все сервисы
docker-compose up --build

# 3. Доступ к сервисам:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# ML Service: http://localhost:5000

# 4. Остановка
docker-compose down
```

### Локальный запуск

#### Требования
- Python 3.10+
- Node.js 16+
- PostgreSQL 14+ или SQLite
- Redis

#### 1. Backend (Python/FastAPI)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

cp .env.example .env

alembic upgrade head

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. ML Service

```bash
cd ml_service

pip install -r requirements.txt

# RuBERT (zero-shot)
MODEL_TYPE=rubert python -m uvicorn main:app --host 0.0.0.0 --port 5000

# RuBERT fine-tuned на текущем датасете
python train_rubert.py
python -m uvicorn main_finetuned:app --host 0.0.0.0 --port 5000

# FastText
python train_fasttext.py  # Обучение модели первый раз
MODEL_TYPE=fasttext python -m uvicorn main:app --host 0.0.0.0 --port 5000

# Mock для тестирования
MODEL_TYPE=mock python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

#### 3. Frontend (React)

```bash
cd frontend

npm install

npm start

npm run build
```


### Рекомендации по выбору модели:

- **RuBERT**: Лучший выбор для большинства медицинских приложений
- **FastText**: Для высоконагруженных систем с жесткими требованиями по latency
- **Mock**: Только для разработки и тестирования

## Тестирование

### Запуск тестов

```bash
venv\Scripts\activate

# Запуск всех unit тестов
pytest tests/ -v

# Запуск только API тестов
pytest tests/test_api.py -v

# Запуск только unit тестов моделей
pytest tests/test_models.py tests/test_security.py -v

# Запуск интеграционного теста (требует запущенных сервисов)
python test_integration.py
```

### Структура тестов

```
tests/
├── __init__.py
├── conftest.py              # Фикстуры для тестов (БД, клиенты)
├── test_models.py           # Unit тесты моделей (User, RefreshToken)
├── test_security.py         # Unit тесты безопасности (JWT, хэширование)
├── test_api.py              # API интеграционные тесты
├── test_ml_service.py       # Тесты ML сервиса
├── test_integration.py      # Полный интеграционный тест
├── test_both_models.py      # Сравнение ML моделей
└── README.md                # Документация по тестам
```

### Покрытие тестирования

- **Модели данных**: Создание, валидация, связи, уникальные ограничения
- **Безопасность**: JWT токены, хэширование паролей, refresh токены
- **API эндпоинты**: Аутентификация, авторизация, CRUD операции, rate limiting
- **ML интеграция**: Классификация текста, обработка ошибок, разные модели
- **Кэширование**: Redis интеграция, истечение кэша
- **Валидация**: Pydantic схемы, бизнес-правила, error handling

### Результаты

**Unit тесты (15 тестов):**
- Модели и безопасность: 7/7 пройдено
- API интеграция: 8/8 пройдено

**Интеграционные тесты:**
- Полная цепочка: Backend + ML Service + Database
- Кэширование результатов
- JWT аутентификация

### Интеграционный тест

```bash
python test_integration.py
```

Проверяет полную цепочку:
1. ML сервис классифицирует текст
2. Аутентификация через JWT токены
3. Backend API вызывает ML сервис
4. База данных сохраняет результаты
5. Кэширование результатов в Redis

### Сравнение ML моделей

```bash
cd ml_service
python benchmark.py
```

Сравнивает производительность:
- Время inference каждой модели
- Точность классификации на тестовых данных
- Ресурсопотребление (CPU, память)

## API Документация

### Аутентификация

```bash
# Регистрация пользователя
POST /auth/register
Content-Type: application/json

{
  "full_name": "Иванов Иван Иванович",
  "email": "user@example.com",
  "phone": "+71234567890",
  "password": "securepassword123"
}

# Вход в систему
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Обновление токена
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

### Классификация обращений

```bash
# Классификация медицинского запроса
POST /classify
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "text": "У меня болит голова срочно, нужна скорая помощь"
}

# ответ
{
  "urgency": "Экстренное",
  "request_type": "Перенаправление в экстренные службы",
  "confidence": "Высокая"
}
```

### Управление пользователями

```bash
# Получение информации о пользователе
GET /users/me
Authorization: Bearer <access_token>

# Обновление профиля
PUT /users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Новое Имя",
  "phone": "+79876543210"
}
```

### Записи на прием

```bash
# Получение всех записей
GET /appointments
Authorization: Bearer <access_token>

# Создание записи
POST /appointments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "doctor_id": 1,
  "appointment_date": "2024-01-15T10:00:00Z",
  "reason": "Консультация по головной боли"
}

# Обновление записи
PUT /appointments/{id}
Authorization: Bearer <access_token>

# Удаление записи
DELETE /appointments/{id}
Authorization: Bearer <access_token>
```

### Уведомления

```bash
# Получение уведомлений
GET /notifications
Authorization: Bearer <access_token>

# Создание уведомления
POST /notifications
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Напоминание о приеме",
  "message": "У вас запись к врачу через 1 час",
  "type": "appointment_reminder"
}
```

### Врачи

```bash
# Получение списка врачей
GET /doctors
Authorization: Bearer <access_token>

# Получение информации о враче
GET /doctors/{id}
Authorization: Bearer <access_token>
```

## Конфигурация

### Переменные окружения (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/medical_service
# или для SQLite
DATABASE_URL=sqlite:///./medical_service.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ML Service
ML_SERVICE_URL=http://localhost:5000

# Redis (опционально)
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```


---

### Реализовано:

- Система аутентификации с JWT токенами
- ML-классификация обращений с высокой точностью
- Современный веб-интерфейс с адаптивным дизайном
- Комплексное тестирование всех компонентов
- Контейнеризация для простого развертывания
- Документация API и инструкций
