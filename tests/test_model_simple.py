# -*- coding: utf-8 -*-
import sys
import torch
import pickle
from pathlib import Path
from transformers import AutoTokenizer, BertModel

# Model configuration
MODEL_DIR = Path(__file__).resolve().parent.parent / 'ml_service' / 'medical_classifier_rubert'
MODEL_NAME = 'DeepPavlov/rubert-base-cased'

class SimpleMultiTaskModel(torch.nn.Module):
    def __init__(self, model_name, num_urgency_labels, num_type_labels):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.urgency_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_urgency_labels)
        self.type_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_type_labels)

    def forward(self, input_ids, attention_mask=None, **kwargs):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        urgency_logits = self.urgency_classifier(pooled_output)
        type_logits = self.type_classifier(pooled_output)
        return {
            'urgency_logits': urgency_logits,
            'type_logits': type_logits
        }

# Test samples
TEST_CASES = [
    {
        'text': 'Боль в груди, потливость, одышка. Это экстренная ситуация.',
        'expected_urgency': 'Экстренное',
        'expected_type': 'Вызов врача',
    },
    {
        'text': 'У меня болит грудь при подъеме по лестнице. Боль проходит после отдыха.',
        'expected_urgency': 'Срочное',
        'expected_type': 'Консультация или вопрос',
    },
    {
        'text': 'Хочу записаться к врачу на прием.',
        'expected_urgency': 'Плановое',
        'expected_type': 'Запись на прием',
    },
]

def main():
    print('='*80)
    print('Testing RuBERT Model')
    print('='*80)
    
    # Load encoders
    print('\nLoading model components...')
    try:
        with open(MODEL_DIR / 'urgency_encoder.pkl', 'rb') as f:
            urgency_encoder = pickle.load(f)
        print('✓ Loaded urgency encoder')
        
        with open(MODEL_DIR / 'request_type_encoder.pkl', 'rb') as f:
            type_encoder = pickle.load(f)
        print('✓ Loaded type encoder')
        
        # Load model
        model = SimpleMultiTaskModel(
            MODEL_NAME,
            len(urgency_encoder.classes_),
            len(type_encoder.classes_)
        )
        print(f'✓ Loaded model')
        
        # Load weights
        weights_path = MODEL_DIR / 'pytorch_model.bin'
        if weights_path.exists():
            state_dict = torch.load(weights_path, map_location='cpu')
            model.load_state_dict(state_dict)
            print(f'✓ Loaded model weights from {weights_path}')
        else:
            print(f'⚠ Warning: weights file not found at {weights_path}')
        
        model.eval()
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print('✓ Loaded tokenizer')
        
    except Exception as e:
        print(f'✗ Error loading components: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # Run tests
    print(f'\n\nRunning {len(TEST_CASES)} test cases...\n')
    passed = 0
    total = len(TEST_CASES)
    
    with torch.no_grad():
        for i, test_case in enumerate(TEST_CASES, 1):
            text = test_case['text']
            expected_urgency = test_case.get('expected_urgency', '?')
            expected_type = test_case.get('expected_type', '?')
            
            try:
                # Tokenize
                encodings = tokenizer(
                    [text],
                    truncation=True,
                    padding='max_length',
                    max_length=128,
                    return_tensors='pt'
                )
                
                # Predict
                outputs = model(
                    input_ids=encodings['input_ids'],
                    attention_mask=encodings['attention_mask']
                )
                
                urgency_pred_idx = outputs['urgency_logits'].argmax(dim=-1).item()
                type_pred_idx = outputs['type_logits'].argmax(dim=-1).item()
                
                pred_urgency = urgency_encoder.inverse_transform([urgency_pred_idx])[0]
                pred_type = type_encoder.inverse_transform([type_pred_idx])[0]
                
                urgency_match = pred_urgency == expected_urgency
                type_match = pred_type == expected_type
                test_passed = urgency_match and type_match
                
                status = 'PASS' if test_passed else 'FAIL'
                print(f'Test {i}: {status}')
                print(f'  Text: "{text[:50]}..."')
                print(f'  Urgency: {pred_urgency} (expected: {expected_urgency}) {"✓" if urgency_match else "❌"}')
                print(f'  Type: {pred_type} (expected: {expected_type}) {"✓" if type_match else "❌"}')
                print()
                
                if test_passed:
                    passed += 1
                    
            except Exception as e:
                print(f'Test {i}: ERROR')
                print(f'  Text: "{text[:50]}..."')
                print(f'  Error: {e}\n')
                import traceback
                traceback.print_exc()
    
    # Summary
    print('='*80)
    print(f'Results: {passed}/{total} tests passed')
    accuracy = (passed / total) * 100 if total > 0 else 0
    print(f'Accuracy: {accuracy:.1f}%')
    print('='*80)

if __name__ == '__main__':
    main()
