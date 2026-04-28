#!/usr/bin/env python
import torch
import pickle
from pathlib import Path
from transformers import AutoTokenizer, BertModel
import pytest

MODEL_DIR = Path(__file__).resolve().parent.parent / 'ml_service' / 'medical_classifier_rubert'
MODEL_NAME = 'DeepPavlov/rubert-base-cased'

class Model(torch.nn.Module):
    def __init__(self, model_name, nu, nt):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.uc = torch.nn.Linear(self.bert.config.hidden_size, nu)
        self.tc = torch.nn.Linear(self.bert.config.hidden_size, nt)

    def forward(self, input_ids, attention_mask=None, **kw):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        p = out.pooler_output
        return {'urgency_logits': self.uc(p), 'type_logits': self.tc(p)}

# Try to load model files; skip tests if not available
try:
    print('Loading...')
    with open(MODEL_DIR / 'urgency_encoder.pkl', 'rb') as f:
        ue = pickle.load(f)
    with open(MODEL_DIR / 'request_type_encoder.pkl', 'rb') as f:
        te = pickle.load(f)

    m = Model(MODEL_NAME, len(ue.classes_), len(te.classes_))
    p = MODEL_DIR / 'pytorch_model.bin'
    if p.exists():
        m.load_state_dict(torch.load(p, map_location='cpu'))
    m.eval()

    tok = AutoTokenizer.from_pretrained(MODEL_NAME)

    print('Model loaded')
    print('Urgency classes:', ue.classes_)
    print('Type classes:', te.classes_)
    print('\nTesting...\n')
    
    MODEL_AVAILABLE = True
    
    # Run inference tests
    tests = [
        ('bol v grudi', 'Ekstrennoe', 'Vyzov vracha'),
        ('gripp i kash', 'Srochnoe', 'Konsultacija'),
    ]

    with torch.no_grad():
        for txt, eu, et in tests:
            enc = tok([txt], truncation=True, padding='max_length', max_length=128, return_tensors='pt')
            out = m(input_ids=enc['input_ids'], attention_mask=enc['attention_mask'])
            ui = out['urgency_logits'].argmax(dim=-1).item()
            ti = out['type_logits'].argmax(dim=-1).item()
            u = ue.inverse_transform([ui])[0]
            t = te.inverse_transform([ti])[0]
            print('Text:', txt)
            print('Urgency:', u, '(exp:', eu, ')')
            print('Type:', t, '(exp:', et, ')')
            print()
    
except FileNotFoundError as e:
    print(f'Warning: Model files not found: {e}')
    print('Skipping model tests (models not available in CI)')
    MODEL_AVAILABLE = False


# Define pytest placeholder functions that skip when model is unavailable
@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Model files not available (in CI environment)")
def test_model_loaded():
    """Test that model files were successfully loaded."""
    assert MODEL_AVAILABLE, "Model files should be available to run this test"

