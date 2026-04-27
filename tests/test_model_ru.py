# -*- coding: utf-8 -*-
import sys
import torch
import pickle
from pathlib import Path
from transformers import AutoTokenizer, BertModel

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

def main():
    print('Testing RuBERT Model')
    print('='*80)
    
    print('\nLoading model components...')
    try:
        with open(MODEL_DIR / 'urgency_encoder.pkl', 'rb') as f:
            urgency_encoder = pickle.load(f)
        print('Loaded urgency encoder')
        
        with open(MODEL_DIR / 'request_type_encoder.pkl', 'rb') as f:
            type_encoder = pickle.load(f)
        print('Loaded type encoder')
        
        model = SimpleMultiTaskModel(
            MODEL_NAME,
            len(urgency_encoder.classes_),
            len(type_encoder.classes_)
        )
        print('Created model')
        
        weights_path = MODEL_DIR / 'pytorch_model.bin'
        if weights_path.exists():
            state_dict = torch.load(weights_path, map_location='cpu')
            model.load_state_dict(state_dict)
            print(f'Loaded weights from {weights_path}')
        
        model.eval()
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print('Loaded tokenizer')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return
    
    print('\nRunning test cases...\n')
    
    test_texts = [
        'Bolyat' + chr(39) + ' v grudi, silnaya odyshka, poteniye',
        'U menya gripushka, kash',
        'Hochu zapist' + chr(39) + 'sya k vrachu',
    ]
    
    with torch.no_grad():
        for i, text in enumerate(test_texts, 1):
            try:
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
                
                urgency_idx = outputs['urgency_logits'].argmax(dim=-1).item()
                type_idx = outputs['type_logits'].argmax(dim=-1).item()
                
                pred_urgency = urgency_encoder.inverse_transform([urgency_idx])[0]
                pred_type = type_encoder.inverse_transform([type_idx])[0]
                
                print(f'Test {i}:')
                print(f'  Urgency: {pred_urgency}')
                print(f'  Type: {pred_type}')
                print()
                    
            except Exception as e:
                print(f'Test {i}: ERROR - {e}')
                import traceback
                traceback.print_exc()
    
    print('='*80)

if __name__ == '__main__':
    main()
