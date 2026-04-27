import pytest
from datetime import datetime, timedelta
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_password,
    verify_password
)
from app.core.config import settings

class TestSecurityFunctions:
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "1", "user": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        from jose import jwt
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == "1"
        assert payload["user"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_password_hashing(self):
        password = "TestPassword123"

        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_refresh_token_operations(self, db_session, test_user_data):
        from app.models.user import User
        user = User(
            full_name=test_user_data["full_name"],
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            password_hash=hash_password(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        refresh_token = create_refresh_token(user.id, db_session)
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0

        user_id = verify_refresh_token(refresh_token, db_session)
        assert user_id == user.id

        invalid_user_id = verify_refresh_token("invalid_token", db_session)
        assert invalid_user_id is None

        from app.models.user import RefreshToken
        expired_token = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).first()
        expired_token.expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        expired_user_id = verify_refresh_token(refresh_token, db_session)
        assert expired_user_id is None