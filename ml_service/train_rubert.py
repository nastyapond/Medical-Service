import argparse
import csv
import os
import sys
import traceback
from pathlib import Path
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import torch

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR.parent / 'datasets' / 'medical-symptom-triage' / 'processed_ru.csv'
OUTPUT_DIR = BASE_DIR / 'medical_classifier_rubert'
MODEL_NAME = 'DeepPavlov/rubert-base-cased'
VALID_URGENCIES = {'Экстренное', 'Срочное', 'Плановое', 'Консультационное'}
VALID_TYPES = {'Запись на прием', 'Вызов врача', 'Консультация или вопрос', 'Наблюдение'}


class UrgencyTypeDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, urgency_labels, type_labels):
        self.encodings = encodings
        self.urgency_labels = urgency_labels
        self.type_labels = type_labels

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item['urgency_labels'] = torch.tensor(self.urgency_labels[idx], dtype=torch.long)
        item['type_labels'] = torch.tensor(self.type_labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        return len(self.urgency_labels)


def load_data(path):
    rows = []
    with path.open('r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            text, urgency, request_type = row[0].strip(), row[1].strip(), row[2].strip()
            if urgency.lower() == 'urgency' or request_type.lower() == 'request_type':
                continue
            if urgency in VALID_URGENCIES and request_type in VALID_TYPES and text:
                rows.append((text, urgency, request_type))
    return rows


def get_data_path():
    parser = argparse.ArgumentParser(description='Train RuBERT urgency/type classifier')
    parser.add_argument('--data-path', type=str, default=os.getenv('DATA_PATH', str(DEFAULT_DATA_PATH)))
    args = parser.parse_args()
    return Path(args.data_path)


def build_labels(rows):
    urgency_encoder = LabelEncoder()
    type_encoder = LabelEncoder()
    urgency_encoder.fit(sorted(VALID_URGENCIES))
    type_encoder.fit(sorted(VALID_TYPES))

    urgency_labels = []
    type_labels = []
    for _, urgency, request_type in rows:
        urgency_labels.append(int(urgency_encoder.transform([urgency])[0]))
        type_labels.append(int(type_encoder.transform([request_type])[0]))

    return urgency_labels, type_labels, urgency_encoder, type_encoder


class MultiTaskTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        outputs = model(**inputs)
        loss = outputs['loss']
        return (loss, outputs) if return_outputs else loss

    def prediction_step(self, model, inputs, prediction_loss_only, ignore_keys=None):
        inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask', 'urgency_labels', 'type_labels']}
        outputs = model(**inputs)
        loss = outputs['loss'].detach()
        logits = (outputs['urgency_logits'].detach(), outputs['type_logits'].detach())
        labels = (inputs['urgency_labels'], inputs['type_labels'])
        return (loss, logits, labels)

class MultiTaskModel(torch.nn.Module):
    def __init__(self, model_name, num_urgency_labels, num_type_labels):
        super().__init__()
        self.bert = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_urgency_labels).bert
        self.urgency_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_urgency_labels)
        self.type_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_type_labels)

    def forward(self, input_ids, attention_mask=None, urgency_labels=None, type_labels=None, **kwargs):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        urgency_logits = self.urgency_classifier(pooled_output)
        type_logits = self.type_classifier(pooled_output)

        loss = None
        if urgency_labels is not None and type_labels is not None:
            urgency_loss = torch.nn.functional.cross_entropy(urgency_logits, urgency_labels)
            type_loss = torch.nn.functional.cross_entropy(type_logits, type_labels)
            loss = urgency_loss + type_loss

        return {'loss': loss, 'urgency_logits': urgency_logits, 'type_logits': type_logits}

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    urgency_logits, type_logits = logits
    urgency_predictions = urgency_logits.argmax(axis=-1)
    type_predictions = type_logits.argmax(axis=-1)
    urgency_labels, type_labels = labels

    urgency_accuracy = accuracy_score(urgency_labels, urgency_predictions)
    type_accuracy = accuracy_score(type_labels, type_predictions)
    urgency_f1 = f1_score(urgency_labels, urgency_predictions, average='weighted')
    type_f1 = f1_score(type_labels, type_predictions, average='weighted')

    return {
        'urgency_accuracy': urgency_accuracy,
        'type_accuracy': type_accuracy,
        'urgency_f1': urgency_f1,
        'type_f1': type_f1,
        'avg_accuracy': (urgency_accuracy + type_accuracy) / 2,
        'avg_f1': (urgency_f1 + type_f1) / 2
    }


def main():
    data_path = get_data_path()
    print(f'Using dataset: {data_path.resolve()}')
    if not data_path.exists():
        raise FileNotFoundError(f'Dataset file not found: {data_path}')

    rows = load_data(data_path)
    print(f'Loaded {len(rows)} valid rows from the dataset')

    if len(rows) < 100:
        raise RuntimeError('Not enough training data after filtering valid labels')

    texts = [text for text, _, _ in rows]
    urgency_labels, type_labels, urgency_encoder, type_encoder = build_labels(rows)

    train_texts, val_texts, train_urgency_labels, val_urgency_labels, train_type_labels, val_type_labels = train_test_split(
        texts,
        urgency_labels,
        type_labels,
        test_size=0.12,
        random_state=42,
        stratify=urgency_labels,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_encodings = tokenizer(
        train_texts,
        truncation=True,
        padding='max_length',
        max_length=128,
    )
    val_encodings = tokenizer(
        val_texts,
        truncation=True,
        padding='max_length',
        max_length=128,
    )

    train_dataset = UrgencyTypeDataset(train_encodings, train_urgency_labels, train_type_labels)
    val_dataset = UrgencyTypeDataset(val_encodings, val_urgency_labels, val_type_labels)

    model = MultiTaskModel(MODEL_NAME, len(urgency_encoder.classes_), len(type_encoder.classes_))

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        evaluation_strategy='epoch',
        save_strategy='epoch',
        logging_strategy='epoch',
        learning_rate=2e-5,
        load_best_model_at_end=True,
        metric_for_best_model='avg_f1',
        seed=42,
        save_total_limit=2,
    )

    trainer = MultiTaskTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print('Starting training...')
    trainer.train()
    print('Saving model to', OUTPUT_DIR)
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    with open(OUTPUT_DIR / 'urgency_encoder.pkl', 'wb') as f:
        import pickle
        pickle.dump(urgency_encoder, f)

    with open(OUTPUT_DIR / 'request_type_encoder.pkl', 'wb') as f:
        import pickle
        pickle.dump(type_encoder, f)

    label_stats = Counter(urgency_labels + type_labels)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR: Training failed with exception:', file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
