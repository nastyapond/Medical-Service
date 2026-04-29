import requests
import json

BASE_URL = "http://localhost:8001"

def test_refresh_tokens():
    print("Тестирование JWT refresh tokens...")

    register_data = {
        "full_name": "Refresh Test User",
        "email": "refresh@example.com",
        "phone": "12345678901",
        "password": "Password123"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"Регистрация: {response.status_code}")
        if response.status_code != 200:
            print(f"Ошибка регистрации: {response.text}")
            return

        login_data = {
            "email": "refresh@example.com",
            "password": "Password123"
        }

        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Вход: {response.status_code}")

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            print("Получены tokens:")
            print(f"  Access token: {access_token[:50]}...")
            print(f"  Refresh token: {refresh_token[:50]}...")

            refresh_data = {"refresh_token": refresh_token}
            response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
            print(f"Refresh: {response.status_code}")

            if response.status_code == 200:
                new_tokens = response.json()
                print("Новые tokens получены:")
                print(f"  New access: {new_tokens.get('access_token')[:50]}...")
                print(f"  New refresh: {new_tokens.get('refresh_token')[:50]}...")
                print("OK - Refresh tokens работают!")
            else:
                print(f"Ошибка refresh: {response.text}")
        else:
            print(f"Ошибка входа: {response.text}")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_refresh_tokens()