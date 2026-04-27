from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.appointment import AppointmentCreate, AppointmentResponse

router = APIRouter()


@router.post("/", response_model=AppointmentResponse)
def create_appointment(appointment: AppointmentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_appointment = Appointment(
        user_id=current_user.id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # Create reminder notification for 1 day before
    reminder_date = appointment.appointment_date - timedelta(days=1)
    notification = Notification(
        user_id=current_user.id,
        type="appointment_reminder",
        text=f"Напоминание: у вас запись к врачу {appointment.appointment_date.strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(notification)
    db.commit()

    return db_appointment


@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.user_id == current_user.id).all()
    return appointments


@router.get("/all", response_model=List[AppointmentResponse])
def get_all_appointments(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    sort_by: str = Query("appointment_date", enum=["appointment_date", "user_id", "doctor_id"]),
    sort_order: str = Query("asc", enum=["asc", "desc"])
):
    query = db.query(Appointment)
    
    if patient_id:
        query = query.filter(Appointment.user_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    
    if sort_order == "desc":
        query = query.order_by(getattr(Appointment, sort_by).desc())
    else:
        query = query.order_by(getattr(Appointment, sort_by).asc())
    
    appointments = query.all()
    return appointments


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check if user owns the appointment or is admin
    if db_appointment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")
    
    db_appointment.doctor_id = appointment.doctor_id
    db_appointment.appointment_date = appointment.appointment_date
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check if user owns the appointment or is admin
    if db_appointment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")
    
    db.delete(db_appointment)
    db.commit()
    return {"message": "Appointment deleted"}