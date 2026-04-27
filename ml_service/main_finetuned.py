"""
ML Classification Service with Fine-tuned RuBERT Model
"""

from fastapi import FastAPI
from pydantic import BaseModel
import os
import logging
import torch
import pickle
from transformers import AutoTokenizer
from .train_rubert import MultiTaskModel

app = FastAPI(title="ML Classification Service (Fine-tuned)")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    urgency: str
    request_type: str
    confidence: str

fine_tuned_model = None
tokenizer = None
device = None
urgency_encoder = None
request_type_encoder = None
num_request_types = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "medical_classifier_rubert")

@app.on_event("startup")
async def load_models():
    global fine_tuned_model, tokenizer, device, urgency_encoder, request_type_encoder, num_request_types
    
    try:
        logger.info(f"Loading fine-tuned RuBERT model from {MODEL_PATH}...")
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        fine_tuned_model = MultiTaskModel(MODEL_PATH, 3, 4)
        fine_tuned_model.load_state_dict(torch.load(os.path.join(MODEL_PATH, 'pytorch_model.bin')))
        fine_tuned_model.to(device)
        fine_tuned_model.eval()
        
        with open(f"{MODEL_PATH}/urgency_encoder.pkl", 'rb') as f:
            urgency_encoder = pickle.load(f)
        with open(f"{MODEL_PATH}/request_type_encoder.pkl", 'rb') as f:
            request_type_encoder = pickle.load(f)
        
        num_request_types = len(request_type_encoder.classes_)
        
        logger.info("OK - Fine-tuned RuBERT model loaded successfully")
        logger.info(f"Urgency classes: {urgency_encoder.classes_.tolist()}")
        logger.info(f"Request type classes: {request_type_encoder.classes_.tolist()}")
        
    except Exception as e:
        logger.error(f"Failed to load fine-tuned model - {e}")
        fine_tuned_model = None
        tokenizer = None
        urgency_encoder = None
        request_type_encoder = None



def classify_with_finetuned(text: str):
    if not fine_tuned_model:
        return {
            "urgency": "Неизвестно", 
            "request_type": "Неизвестно", 
            "confidence": "Низкая"
        }

    try:
        encoding = tokenizer(
            text,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)
        
        with torch.no_grad():
            outputs = fine_tuned_model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
        
        urgency_logits = outputs['urgency_logits']
        type_logits = outputs['type_logits']
        
        urgency_probabilities = torch.softmax(urgency_logits, dim=1)
        type_probabilities = torch.softmax(type_logits, dim=1)
        
        urgency_idx = torch.argmax(urgency_logits, dim=1).item()
        type_idx = torch.argmax(type_logits, dim=1).item()
        
        urgency_confidence = urgency_probabilities[0, urgency_idx].item()
        type_confidence = type_probabilities[0, type_idx].item()
        
        urgency = urgency_encoder.inverse_transform([urgency_idx])[0]
        request_type = request_type_encoder.inverse_transform([type_idx])[0]
        
        avg_confidence = (urgency_confidence + type_confidence) / 2
        if avg_confidence > 0.8:
            confidence = "Высокая"
        elif avg_confidence > 0.6:
            confidence = "Средняя"
        else:
            confidence = "Низкая"
        
        logger.info(f"Fine-tuned: urgency={urgency}, type={request_type}, confidence={avg_confidence:.2f}")
        
        return {
            "urgency": urgency,
            "request_type": request_type,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Classification error - {e}")
        return {
            "urgency": "Ошибка", 
            "request_type": "Ошибка", 
            "confidence": "Низкая"
        }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": fine_tuned_model is not None,
        "model_type": "fine-tuned RuBERT"
    }

@app.post("/classify", response_model=ClassificationResponse)
async def classify(request: ClassificationRequest):
    """Классификация медицинского запроса"""
    logger.info(f"Classification request: {request.text[:100]}")
    
    result = classify_with_finetuned(request.text)
    
    return ClassificationResponse(
        urgency=result["urgency"],
        request_type=result["request_type"],
        confidence=result["confidence"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
