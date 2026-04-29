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

            print("Получены токены:")
            print(f"  Токен доступа: {access_token[:50]}...")
            print(f"  Токен обновления: {refresh_token[:50]}...")

            refresh_data = {"refresh_token": refresh_token}
            response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
            print(f"Обновление токена: {response.status_code}")

            if response.status_code == 200:
                new_tokens = response.json()
                print("Новые токены получены:")
                print(f"  Новый токен доступа: {new_tokens.get('access_token')[:50]}...")
                print(f"  Новый токен обновления: {new_tokens.get('refresh_token')[:50]}...")
                print("Токены обновления работают!")
            else:
                print(f"Ошибка обновления: {response.text}")
        else:
            print(f"Ошибка входа: {response.text}")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_refresh_tokens()