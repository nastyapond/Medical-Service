from pydantic import BaseModel


class DoctorResponse(BaseModel):
    id: int
    full_name: str
    specialization: str
    schedule: str | None

    class Config:
        from_attributes = True
        orm_mode = True