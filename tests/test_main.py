from fastapi.testclient import TestClient
from app.main import app
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import hash_password

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Medical Request Service API"}

def test_register_user():
    response = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "123456789",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

def test_register_duplicate_user():
    client.post("/auth/register", json={
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "phone": "123456789",
        "password": "password123"
    })
    response = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "phone": "123456789",
        "password": "password123"
    })
    assert response.status_code == 400
    assert "User already exists" in response.json()["detail"]

def test_login_success():
    client.post("/auth/register", json={
        "full_name": "Login Test",
        "email": "login@example.com",
        "phone": "123456789",
        "password": "password123"
    })
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]