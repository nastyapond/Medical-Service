from pydantic import BaseModel
from datetime import datetime


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: datetime


class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    doctor_id: int
    appointment_date: datetime
    status: str

    class Config:
        from_attributes = True
        orm_mode = True