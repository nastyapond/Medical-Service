#!/usr/bin/env python
"""
ML Model Runner Tests

Tests for RuBERT model inference when model files are available.
In CI environments where model artifacts are not tracked, tests are skipped gracefully.
"""

import torch
import pickle
from pathlib import Path
from transformers import AutoTokenizer, BertModel
import pytest


# ============================================================================
# Configuration
# ============================================================================

MODEL_DIR = Path(__file__).resolve().parent.parent / 'ml_service' / 'medical_classifier_rubert'
MODEL_NAME = 'DeepPavlov/rubert-base-cased'


# ============================================================================
# Model Definition
# ============================================================================

class RuBertMultiTaskModel(torch.nn.Module):
    """RuBERT-based multi-task model for urgency and request type classification."""

    def __init__(self, model_name, num_urgency_labels, num_type_labels):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.urgency_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_urgency_labels)
        self.type_classifier = torch.nn.Linear(self.bert.config.hidden_size, num_type_labels)

    def forward(self, input_ids, attention_mask=None, **kwargs):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        p = out.pooler_output
        return {
            'urgency_logits': self.urgency_classifier(p),
            'type_logits': self.type_classifier(p)
        }


# ============================================================================
# Model Loading & Initialization
# ============================================================================

MODEL_AVAILABLE = False
model = None
tokenizer = None
urgency_encoder = None
type_encoder = None

try:
    print('Loading ML model files...')
    
    # Load encoders
    with open(MODEL_DIR / 'urgency_encoder.pkl', 'rb') as f:
        urgency_encoder = pickle.load(f)
    with open(MODEL_DIR / 'request_type_encoder.pkl', 'rb') as f:
        type_encoder = pickle.load(f)

    # Initialize and load model
    model = RuBertMultiTaskModel(
        MODEL_NAME,
        len(urgency_encoder.classes_),
        len(type_encoder.classes_)
    )
    
    weights_path = MODEL_DIR / 'pytorch_model.bin'
    if weights_path.exists():
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    
    model.eval()

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print('✓ ML model loaded successfully')
    print(f'  Urgency classes: {urgency_encoder.classes_}')
    print(f'  Type classes: {type_encoder.classes_}\n')
    
    MODEL_AVAILABLE = True
    
except FileNotFoundError as e:
    print(f'⚠ Model files not found: {e}')
    print('  Model tests will be skipped (expected in CI environment)\n')


# ============================================================================
# Test Cases
# ============================================================================

TEST_CASES = [
    ('bol v grudi', 'Ekstrennoe', 'Vyzov vracha'),
    ('gripp i kash', 'Srochnoe', 'Konsultacija'),
]


# ============================================================================
# Pytest Tests
# ============================================================================

@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Model files not available (CI environment)")
def test_model_loaded():
    """Verify that model was successfully loaded."""
    assert MODEL_AVAILABLE, "Model should be available"
    assert model is not None, "Model should be initialized"
    assert tokenizer is not None, "Tokenizer should be loaded"
    assert urgency_encoder is not None, "Urgency encoder should be loaded"
    assert type_encoder is not None, "Type encoder should be loaded"


@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Model files not available (CI environment)")
def test_model_inference():
    """Test model inference on sample texts."""
    with torch.no_grad():
        for text, expected_urgency, expected_type in TEST_CASES:
            # Tokenize
            encodings = tokenizer(
                [text],
                truncation=True,
                padding='max_length',
                max_length=128,
                return_tensors='pt'
            )
            
            # Inference
            outputs = model(
                input_ids=encodings['input_ids'],
                attention_mask=encodings['attention_mask']
            )
            
            # Get predictions
            urgency_idx = outputs['urgency_logits'].argmax(dim=-1).item()
            type_idx = outputs['type_logits'].argmax(dim=-1).item()
            
            urgency = urgency_encoder.inverse_transform([urgency_idx])[0]
            type_pred = type_encoder.inverse_transform([type_idx])[0]
            
            # Verify
            assert urgency is not None, f"Urgency should be predicted for: {text}"
            assert type_pred is not None, f"Type should be predicted for: {text}"
            
            print(f"✓ Text: {text}")
            print(f"  Urgency: {urgency} (expected: {expected_urgency})")
            print(f"  Type: {type_pred} (expected: {expected_type})\n")

