from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class RequestHistory(Base):
    __tablename__ = "request_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    urgency_class: Mapped[str] = mapped_column(String, nullable=False)
    request_type_class: Mapped[str] = mapped_column(String, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)