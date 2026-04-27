from fastapi import FastAPI
from pydantic import BaseModel
import os
import logging
import torch
import pickle
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

app = FastAPI(title="ML Classification Service")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    urgency: str
    request_type: str
    confidence: str

rubert_classifier = None
fasttext_urgency_model = None
fasttext_type_model = None

fine_tuned_model = None
tokenizer = None
device = None
urgency_encoder = None
request_type_encoder = None
num_request_types = None

MODEL_TYPE = os.getenv("MODEL_TYPE", "rubert")
FINE_TUNED_MODEL_PATH = "./medical_classifier_rubert"
logger.info(f"Using model type - {MODEL_TYPE}")



async def load_zero_shot_model():
    global rubert_classifier
    try:
        logger.info("Loading RuBERT zero-shot model...")
        rubert_classifier = pipeline(
            "zero-shot-classification", 
            model="DeepPavlov/rubert-base-cased"
        )
        logger.info("OK - RuBERT zero-shot model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load RuBERT zero-shot - {e}")
        rubert_classifier = None

@app.on_event("startup")
async def load_models():
    global rubert_classifier, fasttext_urgency_model, fasttext_type_model
    global fine_tuned_model, tokenizer, device, urgency_encoder, request_type_encoder, num_request_types
    
    if MODEL_TYPE == "rubert":
        if os.path.exists(FINE_TUNED_MODEL_PATH):
            try:
                logger.info(f"Loading fine-tuned RuBERT model from {FINE_TUNED_MODEL_PATH}...")
                
                device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                logger.info(f"Using device: {device}")
                
                tokenizer = AutoTokenizer.from_pretrained(FINE_TUNED_MODEL_PATH)
                from train_rubert import MultiTaskModel
                fine_tuned_model = MultiTaskModel(FINE_TUNED_MODEL_PATH, 3, 4)
                fine_tuned_model.load_state_dict(torch.load(os.path.join(FINE_TUNED_MODEL_PATH, 'pytorch_model.bin')))
                fine_tuned_model.to(device)
                fine_tuned_model.eval()
                
                with open(os.path.join(FINE_TUNED_MODEL_PATH, 'urgency_encoder.pkl'), 'rb') as f:
                    urgency_encoder = pickle.load(f)
                with open(os.path.join(FINE_TUNED_MODEL_PATH, 'request_type_encoder.pkl'), 'rb') as f:
                    request_type_encoder = pickle.load(f)
                
                num_request_types = len(request_type_encoder.classes_)
                
                logger.info("OK - Fine-tuned RuBERT model loaded successfully")
                logger.info(f"Urgency classes: {list(urgency_encoder.classes_)}")
                logger.info(f"Request type classes: {list(request_type_encoder.classes_)}")
                
            except Exception as e:
                logger.error(f"Failed to load fine-tuned RuBERT - {e}")
                fine_tuned_model = None
                await load_zero_shot_model()
        else:
            await load_zero_shot_model()
    
    elif MODEL_TYPE == "fasttext":
        try:
            logger.info("Loading FastText models...")
            try:
                import fasttext
                urgency_path = "models/urgency_model.bin"
                type_path = "models/type_model.bin"
                
                if os.path.exists(urgency_path) and os.path.exists(type_path):
                    fasttext_urgency_model = fasttext.load_model(urgency_path)
                    fasttext_type_model = fasttext.load_model(type_path)
                    logger.info("OK - FastText models loaded successfully")
                else:
                    logger.warning("FastText model files not found. Please run train_fasttext.py")
                    fasttext_urgency_model = None
                    fasttext_type_model = None
            except ImportError:
                logger.warning("FastText not installed. Install with - pip install fasttext")
                fasttext_urgency_model = None
                fasttext_type_model = None
        except Exception as e:
            logger.error(f"Failed to load FastText models - {e}")
            fasttext_urgency_model = None
            fasttext_type_model = None

def classify_with_rubert(text: str):
    if fine_tuned_model and tokenizer and device and urgency_encoder and request_type_encoder:
        return classify_with_finetuned(text)
    
    if not rubert_classifier:
        return {"urgency": "Неизвестно", "request_type": "Неизвестно", "confidence": "Низкая"}

    try:
        urgency_labels = ["высокая", "средняя", "низкая"]
        type_labels = ["экстренная помощь", "лечение", "диагностика", "консультация"]

        urgency_result = rubert_classifier(text, urgency_labels, multi_class=False)
        urgency = urgency_result['labels'][0]
        urgency_score = urgency_result['scores'][0]

        type_result = rubert_classifier(text, type_labels, multi_class=False)
        request_type = type_result['labels'][0]
        type_score = type_result['scores'][0]

        avg_score = (urgency_score + type_score) / 2
        if avg_score > 0.8:
            confidence = "Высокая"
        elif avg_score > 0.6:
            confidence = "Средняя"
        else:
            confidence = "Низкая"

        logger.info(f"RuBERT zero-shot: urgency={urgency} ({urgency_score:.2f}), type={request_type} ({type_score:.2f})")
        
        return {
            "urgency": urgency,
            "request_type": request_type,
            "confidence": confidence
        }
    except Exception as e:
        logger.error(f"RuBERT classification error: {e}")
        return {"urgency": "Неизвестно", "request_type": "Неизвестно", "confidence": "Низкая"}

def classify_with_finetuned(text: str):
    try:
        logger.info(f"Fine-tuned: {text[:50]}...")
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = fine_tuned_model(**inputs)
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
        logger.error(f"Fine-tuned classification error: {e}")
        return {"urgency": "Неизвестно", "request_type": "Неизвестно", "confidence": "Низкая"}

def classify_with_fasttext(text: str):
    """Classify using trained FastText models."""
    if not fasttext_urgency_model or not fasttext_type_model:
        logger.warning("FastText models not loaded, using mock classification")
        return classify_text_mock(text)

    try:
        urgency_pred = fasttext_urgency_model.predict(text, k=1)
        urgency = urgency_pred[0][0].replace("__label__", "")
        urgency_score = urgency_pred[1][0]

        type_pred = fasttext_type_model.predict(text, k=1)
        request_type = type_pred[0][0].replace("__label__", "").replace("_", " ")
        type_score = type_pred[1][0]

        avg_score = (urgency_score + type_score) / 2
        if avg_score > 0.7:
            confidence = "Высокая"
        elif avg_score > 0.5:
            confidence = "Средняя"
        else:
            confidence = "Низкая"

        logger.info(f"FastText: urgency={urgency} ({urgency_score:.2f}), type={request_type} ({type_score:.2f})")
        
        return {
            "urgency": urgency,
            "request_type": request_type,
            "confidence": confidence
        }
    except Exception as e:
        logger.error(f"FastText classification error: {e}")
        return classify_text_mock(text)

def classify_text_mock(text: str):
    """Keyword-based mock classification (fallback)."""
    text_lower = text.lower()

    urgency_classes = {
        'Консультационное': ['вопрос', 'справка', 'повторный', 'консультация'],
        'Плановое': ['завтра', 'скоро', 'планово', 'ближайшие'],
        'Срочное': ['сегодня', 'быстро', 'важно'],
        'Экстренное': ['срочно', 'немедленно', 'боль', 'критично', 'скорая']
    }

    urgency = 'Срочное'
    for cls, keywords in urgency_classes.items():
        if any(word in text_lower for word in keywords):
            urgency = cls
            break

    type_classes = {
        'Запись на прием': ['записать', 'прием', 'врач', 'талон'],
        'Вызов врача': ['вызвать', 'домой', 'на дом'],
        'Перенаправление в экстренные службы': ['скорая', 'экстренная', 'помощь'],
        'Консультация или вопрос': ['вопрос', 'узнать', 'как', 'что'],
        'Наблюдение': ['наблюдение', 'диспансеризация', 'осмотр']
    }

    request_type = 'Запись на прием'
    for cls, keywords in type_classes.items():
        if any(word in text_lower for word in keywords):
            request_type = cls
            break

    logger.info(f"Mock: urgency={urgency}, type={request_type}")
    
    return {
        "urgency": urgency,
        "request_type": request_type,
        "confidence": "Средняя"
    }

@app.get("/")
async def root():
    return {"message": "ML Classification Service"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_type": MODEL_TYPE,
        "models_loaded": {
            "rubert": rubert_classifier is not None,
            "fasttext_urgency": fasttext_urgency_model is not None,
            "fasttext_type": fasttext_type_model is not None
        }
    }

@app.post("/classify", response_model=ClassificationResponse)
async def classify_request(request: ClassificationRequest):
    """Classify medical request."""
    logger.info(f"Classifying: {request.text[:50]}...")
    
    if MODEL_TYPE == "rubert":
        result = classify_with_rubert(request.text)
    elif MODEL_TYPE == "fasttext":
        result = classify_with_fasttext(request.text)
    else: 
        result = classify_text_mock(request.text)

    return ClassificationResponse(**result)
