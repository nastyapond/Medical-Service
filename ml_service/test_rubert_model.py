# -*- coding: utf-8 -*-
import torch
import pickle
from pathlib import Path
from transformers import AutoTokenizer
from ml_service.train_rubert import MultiTaskModel

# Paths
MODEL_DIR = Path(__file__).resolve().parent / 'medical_classifier_rubert'
MODEL_NAME = 'DeepPavlov/rubert-base-cased'

# Test samples
TEST_CASES = [
    {
        'text': 'Последний час меня мучила невыносимая боль в центре груди. Боль распространяется в левую руку. Я очень потею и мне нехватает дыхания.',
        'expected_urgency': 'Экстренное',
        'expected_type': 'Вызов врача',
        'description': 'Emergency: chest pain with arm radiation'
    },
    {
        'text': 'У меня сжимающая боль в груди, которая возникает при подъеме по лестнице. Боль проходит после отдыха.',
        'expected_urgency': 'Срочное',
        'expected_type': 'Консультация или вопрос',
        'description': 'Urgent: exercise-induced chest pain'
    },
    {
        'text': 'Я хотел бы записаться на прием к кардиологу для профилактического осмотра.',
        'expected_urgency': 'Плановое',
        'expected_type': 'Запись на прием',
        'description': 'Planned: appointment request'
    },
    {
        'text': 'У меня периодические учащения сердцебиения, это нормально?',
        'expected_urgency': 'Консультационное',
        'expected_type': 'Консультация или вопрос',
        'description': 'Consultation: advice on symptoms'
    },
]

def load_model():
    """Load the trained model and encoders."""
    try:
        # Load encoders
        with open(MODEL_DIR / 'urgency_encoder.pkl', 'rb') as f:
            urgency_encoder = pickle.load(f)
        with open(MODEL_DIR / 'request_type_encoder.pkl', 'rb') as f:
            type_encoder = pickle.load(f)
        
        # Load model
        model = MultiTaskModel(
            MODEL_NAME,
            len(urgency_encoder.classes_),
            len(type_encoder.classes_)
        )
        
        # Try to load weights if they exist (from fine-tuned version)
        weights_path = MODEL_DIR / 'pytorch_model.bin'
        if weights_path.exists():
            model.load_state_dict(torch.load(weights_path, map_location='cpu'))
            print(f'✓ Loaded fine-tuned weights from {weights_path}')
        
        model.eval()
        return model, urgency_encoder, type_encoder
    except Exception as e:
        print(f'✗ Error loading model: {e}')
        raise

def predict(model, tokenizer, text, urgency_encoder, type_encoder):
    """Make predictions on a single text."""
    with torch.no_grad():
        encodings = tokenizer(
            [text],
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        outputs = model(
            input_ids=encodings['input_ids'],
            attention_mask=encodings['attention_mask']
        )
        
        urgency_pred = outputs['urgency_logits'].argmax(dim=-1).item()
        type_pred = outputs['type_logits'].argmax(dim=-1).item()
        
        urgency_label = urgency_encoder.inverse_transform([urgency_pred])[0]
        type_label = type_encoder.inverse_transform([type_pred])[0]
        
        return urgency_label, type_label

def main():
    print('=' * 80)
    print('Testing RuBERT Urgency/Type Classification Model')
    print('=' * 80)
    
    # Load model
    print('\nLoading model...')
    try:
        model, urgency_encoder, type_encoder = load_model()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print('✓ Model loaded successfully')
    except Exception as e:
        print(f'✗ Failed to load model: {e}')
        return
    
    # Run tests
    print(f'\nRunning {len(TEST_CASES)} test cases...\n')
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        text = test_case['text']
        expected_urgency = test_case['expected_urgency']
        expected_type = test_case['expected_type']
        description = test_case['description']
        
        try:
            pred_urgency, pred_type = predict(model, tokenizer, text, urgency_encoder, type_encoder)
            
            urgency_match = pred_urgency == expected_urgency
            type_match = pred_type == expected_type
            test_passed = urgency_match and type_match
            
            status = '✓ PASS' if test_passed else '✗ FAIL'
            print(f'Test {i}: {status} ({description})')
            print(f'  Text: "{text[:60]}..."')
            print(f'  Urgency: {pred_urgency} (expected: {expected_urgency}) {["❌", "✓"][urgency_match]}')
            print(f'  Type: {pred_type} (expected: {expected_type}) {["❌", "✓"][type_match]}')
            print()
            
            if test_passed:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f'Test {i}: ✗ ERROR ({description})')
            print(f'  Error: {e}\n')
            failed += 1
    
    # Summary
    print('=' * 80)
    print(f'Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests')
    accuracy = (passed / len(TEST_CASES)) * 100 if TEST_CASES else 0
    print(f'Accuracy: {accuracy:.1f}%')
    print('=' * 80)

if __name__ == '__main__':
    main()
