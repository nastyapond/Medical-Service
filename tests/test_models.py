import pytest
from app.models.user import User, RefreshToken
from app.core.security import hash_password, verify_password

class TestUserModel:
    def test_user_creation(self, db_session, test_user_data):
        user = User(
            full_name=test_user_data["full_name"],
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            password_hash=hash_password(test_user_data["password"])
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.full_name == test_user_data["full_name"]
        assert user.email == test_user_data["email"]
        assert user.phone == test_user_data["phone"]
        assert user.password_hash != test_user_data["password"]  
    def test_user_unique_constraints(self, db_session, test_user_data):
        user1 = User(
            full_name="User 1",
            email=test_user_data["email"],
            phone="11111111111",
            password_hash=hash_password("pass1")
        )

        user2 = User(
            full_name="User 2",
            email="different@example.com",
            phone=test_user_data["phone"],
            password_hash=hash_password("pass2")
        )

        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        duplicate_email = User(
            full_name="User 3",
            email=test_user_data["email"],
            phone="22222222222",
            password_hash=hash_password("pass3")
        )

        with pytest.raises(Exception): 
            db_session.add(duplicate_email)
            db_session.commit()

class TestRefreshTokenModel:
    def test_refresh_token_creation(self, db_session, test_user_data):
        user = User(
            full_name=test_user_data["full_name"],
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            password_hash=hash_password(test_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()

        import secrets
        from datetime import datetime, timedelta

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)

        refresh_token = RefreshToken(
            token=token,
            user_id=user.id,
            expires_at=expires_at
        )

        db_session.add(refresh_token)
        db_session.commit()
        db_session.refresh(refresh_token)

        assert refresh_token.id is not None
        assert refresh_token.token == token
        assert refresh_token.user_id == user.id
        assert refresh_token.expires_at == expires_at

class TestPasswordSecurity:
    def test_password_hashing(self):
        password = "MySecurePassword123"

        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)