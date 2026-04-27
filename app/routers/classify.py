from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import json
import logging
from app.core.config import settings
from app.core.security import get_current_user
from app.core.cache import get_cached_result, set_cached_result
from app.models.user import User
from app.models.request_history import RequestHistory
from app.core.database import get_db
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class ClassificationRequest(BaseModel):
    text: str


class ClassificationResponse(BaseModel):
    urgency: str
    request_type: str
    confidence: str


@router.post("/", response_model=ClassificationResponse)
async def classify_request(data: ClassificationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        cache_key = f"classify:{data.text}"
        cached = get_cached_result(cache_key)
        if cached:
            logger.info(f"Cache hit for - {data.text[:50]}")
            result = json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache read failed - {e}")
        cached = None
    
    if not cached:
        try:
            logger.info(f"Calling ML service at {settings.ML_SERVICE_URL}/classify with text - {data.text[:50]}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ML_SERVICE_URL}/classify", 
                    json={"text": data.text}
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"ML service response - {result}")
            
            try:
                set_cached_result(cache_key, json.dumps(result))
            except Exception as e:
                logger.warning(f"Cache write failed - {e}")
                
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"ML service unavailable, falling back to empty classification - {e}")
            result = {
                "urgency": "Не определено",
                "request_type": "Не определено",
                "confidence": "Не определено"
            }
        except Exception as e:
            logger.error(f"Unexpected error calling ML service - {e}")
            result = {
                "urgency": "Не определено",
                "request_type": "Не определено",
                "confidence": "Не определено"
            }

    try:
        history = RequestHistory(
            user_id=current_user.id,
            request_text=data.text,
            urgency_class=result["urgency"],
            request_type_class=result["request_type"],
            confidence_level=result["confidence"]
        )
        db.add(history)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save to history - {e}")
        db.rollback()

    return ClassificationResponse(**result)