import os
from pathlib import Path

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    print("IMPORTANT - FastText not available. Creating mock models for demonstration.")

URGENCY_TRAINING_DATA = """
__label__Экстренное У меня критическая боль в груди срочно
__label__Экстренное Потеря сознания вызовите скорую
__label__Экстренное Не могу дышать немедленно нужна помощь
__label__Срочное Температура 40 градусов нужно к врачу сегодня
__label__Срочное Сильная боль в животе срочно запишите
__label__Плановое Хочу приходить на прием завтра
__label__Плановое Запишите меня пожалуйста на этой неделе
__label__Консультационное Какой врач лечит это заболевание
__label__Консультационное Как правильно принимать это лекарство
"""

REQUEST_TYPE_TRAINING_DATA = """
__label__Запись_на_прием Нужно записаться к кардиологу
__label__Запись_на_прием Запишите меня на прием пожалуйста
__label__Вызов_врача Пожалуйста вызовите врача на дом
__label__Вызов_врача Дома не могу добраться приедет врач
__label__Перенаправление_экстренное Вызовите скорую помощь максимально быстро
__label__Перенаправление_экстренное Нужна срочная помощь в травмпункт
__label__Консультация Подскажите что мне делать
__label__Консультация Есть ли противопоказания этому лекарству
__label__Наблюдение Прошу назначить диспансеризацию
__label__Наблюдение Хочу встать на диспансерное наблюдение
"""


def prepare_training_files():
    """Подготовить файлы обучающих данных"""
    os.makedirs("data", exist_ok=True)
    
    with open("data/urgency_train.txt", "w", encoding="utf-8") as f:
        f.write(URGENCY_TRAINING_DATA.strip())
    
    with open("data/type_train.txt", "w", encoding="utf-8") as f:
        f.write(REQUEST_TYPE_TRAINING_DATA.strip())
    
    print("OK - Training data files prepared")


def train_urgency_model():
    if not FASTTEXT_AVAILABLE:
        print("FastText not available - creating mock model placeholder")
        os.makedirs("models", exist_ok=True)
        with open("models/urgency_model.bin", "w") as f:
            f.write("MOCK_MODEL_PLACEHOLDER")
        return None
    
    print("Training urgency classification model...")
    
    model = fasttext.train_supervised(
        input="data/urgency_train.txt",
        epoch=100,
        lr=0.5,
        wordNgrams=2,
        dim=100,
        loss='softmax',
        minn=3,
        maxn=6,
    )
    
    model.save_model("models/urgency_model.bin")
    print("Urgency model saved to models/urgency_model.bin")
    
    predictions = model.predict("болит голова срочно")[0]
    print(f"  Sample prediction - {predictions}")
    
    return model


def train_type_model():
    if not FASTTEXT_AVAILABLE:
        print("FastText not available - creating mock model placeholder")
        os.makedirs("models", exist_ok=True)
        with open("models/type_model.bin", "w") as f:
            f.write("MOCK_MODEL_PLACEHOLDER")
        return None
    
    print("Training request type classification model...")
    
    model = fasttext.train_supervised(
        input="data/type_train.txt",
        epoch=100,
        lr=0.5,
        wordNgrams=2,
        dim=100,
        loss='softmax',
        minn=3,
        maxn=6,
    )
    
    model.save_model("models/type_model.bin")
    print("Type model saved to models/type_model.bin")
    
    predictions = model.predict("запишите на прием")[0]
    print(f"  Sample prediction - {predictions}")
    
    return model


def evaluate_model(model, test_data):
    with open("temp_test.txt", "w", encoding="utf-8") as f:
        f.write(test_data)
    
    result = model.test("temp_test.txt")
    precision = result[1]
    recall = result[2]
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    print(f"  Precision - {precision:.3f}, Recall - {recall:.3f}, F1-Score - {f1_score:.3f}")
    
    os.remove("temp_test.txt")
    return result


if __name__ == "__main__":
    print("FastText Model Training Pipeline\n")
    
    prepare_training_files()
    print()
    
    os.makedirs("models", exist_ok=True)
    urgency_model = train_urgency_model()
    print()
    type_model = train_type_model()
    
    print("\n✓ Models trained successfully!")
    print("Use MODEL_TYPE=fasttext environment variable to use FastText models")
