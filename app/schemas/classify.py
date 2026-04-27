from pydantic import BaseModel
from datetime import datetime


class ClassificationRequest(BaseModel):
    text: str


class ClassificationResponse(BaseModel):
    urgency: str
    request_type: str
    confidence: str
    created_at: datetime | None = None