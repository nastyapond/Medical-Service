from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import auth, users, appointments, classify, notifications, doctors
from app.core.database import Base, engine, SessionLocal
from app.models.doctor import Doctor

Base.metadata.create_all(bind=engine)

def seed_default_doctors():
    db = SessionLocal()
    try:
        existing = db.query(Doctor).count()
        if existing == 0:
            doctors = [
                Doctor(full_name="Иванов Иван Иванович", specialization="Терапевт", schedule="Пн-Пт 09:00-18:00"),
                Doctor(full_name="Петрова Мария Сергеевна", specialization="Кардиолог", schedule="Пн, Ср, Пт 10:00-17:00"),
                Doctor(full_name="Сидоров Алексей Николаевич", specialization="Невролог", schedule="Вт-Чт 11:00-19:00"),
                Doctor(full_name="Кузнецова Ольга Владимировна", specialization="Дерматолог", schedule="Пн-Пт 09:00-16:00"),
                Doctor(full_name="Орлова Елена Юрьевна", specialization="Педиатр", schedule="Вт-Пт 08:30-15:30"),
            ]
            db.add_all(doctors)
            db.commit()
    finally:
        db.close()

seed_default_doctors()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Medical Request Service API",
    description="API для медицинского сервиса обработки запросов пациентов с ML классификацией",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter

def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return _rate_limit_exceeded_handler(request, exc)  # type: ignore[arg-type]

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def add_api_version(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "1.0.0"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(classify.router, prefix="/classify", tags=["Classification"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])


@app.get("/", summary="Root endpoint", description="Проверка работоспособности API")
def root():
    return {"message": "Medical Request Service API"}