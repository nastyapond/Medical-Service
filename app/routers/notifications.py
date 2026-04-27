from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationCreate

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    return notifications


@router.post("/", response_model=NotificationResponse)
def create_notification(notification: NotificationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_notification = Notification(
        user_id=current_user.id,
        type=notification.type,
        text=notification.text
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification