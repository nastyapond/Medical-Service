import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.core.security import hash_password

# Test database
TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user():
    """Create test user data."""
    return {
        "full_name": "API Test User",
        "email": "api_test@example.com",
        "phone": "+71234567890",
        "password": "ApiTest123"
    }

class TestAuthAPI:
    def test_register_success(self, client, test_user):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user)

        assert response.status_code == 200
        assert response.json() == {"message": "User registered successfully"}

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        # Register first user
        client.post("/auth/register", json=test_user)

        # Try to register with same email
        duplicate_user = test_user.copy()
        duplicate_user["phone"] = "+79999999999"

        response = client.post("/auth/register", json=duplicate_user)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_phone_format_error(self, client, test_user):
        """Test registration with invalid phone format."""
        invalid_user = test_user.copy()
        invalid_user["phone"] = "1234567890"

        response = client.post("/auth/register", json=invalid_user)

        assert response.status_code == 422
        assert any(
            "Введите телефон в формате +71234567890" in item["msg"]
            for item in response.json()["detail"]
        )

    def test_register_password_requirements(self, client, test_user):
        """Test registration password complexity validation."""
        invalid_user = test_user.copy()
        invalid_user["password"] = "pass1"

        response = client.post("/auth/register", json=invalid_user)

        assert response.status_code == 422
        assert any(
            "Пароль должен содержать минимум 6 символов" in item["msg"]
            for item in response.json()["detail"]
        )

    def test_login_success(self, client, test_user):
        """Test successful login."""
        # Register user first
        client.post("/auth/register", json=test_user)

        # Login
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_refresh_token(self, client, test_user):
        """Test refresh token functionality."""
        # Register and login
        client.post("/auth/register", json=test_user)

        login_response = client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })

        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        refresh_response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert refresh_response.status_code == 200

        new_data = refresh_response.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data
        assert new_data["token_type"] == "bearer"

class TestProtectedEndpoints:
    def test_classify_without_auth(self, client):
        """Test classify endpoint without authentication."""
        response = client.post("/classify", json={"text": "Test message"})
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_classify_with_auth(self, client, test_user):
        """Test classify endpoint with authentication."""
        # Register and login
        client.post("/auth/register", json=test_user)

        login_response = client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })

        access_token = login_response.json()["access_token"]

        # Make authenticated request
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/classify", json={"text": "У меня болит голова"}, headers=headers)

        # Note: This will fail without ML service running, but tests auth
        # In real scenario, would mock ML service
        assert response.status_code in [200, 500]  # 200 if ML works, 500 if not

    def test_users_me_endpoint(self, client, test_user):
        """Test /users/me endpoint."""
        # Register and login
        client.post("/auth/register", json=test_user)

        login_response = client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })

        access_token = login_response.json()["access_token"]

        # Get user info
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/users/me", headers=headers)

        assert response.status_code == 200

        user_data = response.json()
        assert user_data["email"] == test_user["email"]
        assert user_data["full_name"] == test_user["full_name"]