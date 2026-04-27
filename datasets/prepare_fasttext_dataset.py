import csv
import re
from pathlib import Path
from collections import Counter

DATA_PATH = Path(__file__).parent / 'medical-symptom-triage' / 'processed_ru.csv'
OUTPUT_DIR = Path(__file__).parent.parent / 'ml_service' / 'data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VALID_URGENCIES = {'Экстренное', 'Срочное', 'Плановое', 'Консультационное'}
VALID_TYPES = {'Запись на прием', 'Вызов врача', 'Консультация или вопрос', 'Наблюдение', 'Перенаправление в экстренные службы'}

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip('"').strip()
    return text.strip()

def tokenize_text(text):
    text = re.sub(r'[.,!?;:\(\)\[\]{}«»„"—–]', ' ', text)
    tokens = text.split()
    return ' '.join(tokens)

def filter_by_frequency(texts, min_freq=2, max_freq_ratio=0.5):
    all_tokens = []
    for text in texts:
        all_tokens.extend(text.split())
    
    token_counts = Counter(all_tokens)
    total_docs = len(texts)
    max_freq_threshold = int(total_docs * max_freq_ratio)
    
    filtered_texts = []
    for text in texts:
        tokens = text.split()
        filtered_tokens = [
            t for t in tokens 
            if min_freq <= token_counts[t] <= max_freq_threshold
        ]
        filtered_texts.append(' '.join(filtered_tokens))
    
    return filtered_texts

def load_and_prepare_data():
    urgency_texts = []
    urgency_labels = []
    type_texts = []
    type_labels = []
    
    with DATA_PATH.open('r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            
            text = clean_text(row[0])
            urgency = row[1].strip()
            request_type = row[2].strip()
            
            if urgency not in VALID_URGENCIES or request_type not in VALID_TYPES:
                continue
            
            if not text:
                continue
            
            # Токенизировать
            processed_text = tokenize_text(text)
            if processed_text:
                urgency_texts.append(processed_text)
                urgency_labels.append(urgency)
                type_texts.append(processed_text)
                type_labels.append(request_type)
    
    print(f"Загружено {len(urgency_texts)} строк из датасета")
    
    urgency_dist = Counter(urgency_labels)
    print("\nРаспределение классов срочности:")
    for label, count in urgency_dist.most_common():
        print(f"  {label}: {count}")
    
    type_dist = Counter(type_labels)
    print("\nРаспределение классов типа запроса:")
    for label, count in type_dist.most_common():
        print(f"  {label}: {count}")
    
    return urgency_texts, urgency_labels, type_texts, type_labels

def save_fasttext_format(texts, labels, output_file, class_prefix=''):
    """Сохранить в формат FastText с префиксом класса"""
    with output_file.open('w', encoding='utf-8') as f:
        for text, label in zip(texts, labels):
            fasttext_label = label.replace(' ', '_')
            f.write(f"__label__{class_prefix}{fasttext_label} {text}\n")

def main():
    print("=" * 60)
    print("Подготовка датасета для FastText")
    print("=" * 60)
    
    urgency_texts, urgency_labels, type_texts, type_labels = load_and_prepare_data()
    
    urgency_file = OUTPUT_DIR / 'fasttext_urgency_train.txt'
    type_file = OUTPUT_DIR / 'fasttext_type_train.txt'
    
    save_fasttext_format(urgency_texts, urgency_labels, urgency_file, class_prefix='urgency_')
    save_fasttext_format(type_texts, type_labels, type_file, class_prefix='type_')
    
    print(f"\n✓ Файл срочности сохранён: {urgency_file}")
    print(f"✓ Файл типа запроса сохранён: {type_file}")
    print(f"\nОбщее количество примеров: {len(urgency_texts)}")

if __name__ == '__main__':
    main()
