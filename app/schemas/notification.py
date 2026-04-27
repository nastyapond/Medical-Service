from pydantic import BaseModel
from datetime import datetime


class NotificationCreate(BaseModel):
    type: str
    text: str


class NotificationResponse(BaseModel):
    id: int
    type: str
    text: str
    sent_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True