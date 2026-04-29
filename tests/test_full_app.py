import httpx
import asyncio
import time

async def test_application():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ ML СЕРВИСА (порт 5000)")
    print("=" * 50)
    
    ml_url = "http://localhost:5000/classify"
    test_requests = [
        "У меня сильная боль в голове, не могу работать",
        "Нужна консультация терапевта, хочу записаться",
        "Срочно нужна скорая помощь, не могу дышать",
        "Хочу пройти профилактический осмотр"
    ]
    
    async with httpx.AsyncClient() as client:
        for text in test_requests:
            try:
                response = await client.post(ml_url, json={"text": text})
                if response.status_code == 200:
                    result = response.json()
                    print(f"\nЗапрос: {text[:50]}...")
                    print(f"  Срочность: {result['urgency']}")
                    print(f"  Тип запроса: {result['request_type']}")
                    print(f"  Уверенность: {result['confidence']}")
                else:
                    print(f"Ошибка ML сервиса: {response.status_code}")
            except Exception as e:
                print(f"Ошибка при обращении к ML сервису: {e}")
    
    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ BACKEND (порт 8001)")
    print("=" * 50)
    
    backend_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{backend_url}/")
            print(f"\nRoot endpoint: {response.json()}")
        except Exception as e:
            print(f"Ошибка при обращении к root: {e}")
        
        try:
            timestamp = int(time.time())
            register_data = {
                "full_name": f"Test User {timestamp}",
                "email": f"test{timestamp}@example.com",
                "password": "TestPassword123",
                "phone": "+71234567890"
            }
            response = await client.post(f"{backend_url}/auth/register", json=register_data)
            if response.status_code in [200, 400]:
                print(f"\nРегистрация: OK")
                email = register_data["email"]
                password = register_data["password"]
            else:
                print(f"\nОшибка регистрации: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")
            return
        
        try:
            login_data = {
                "email": email,
                "password": password
            }
            response = await client.post(f"{backend_url}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                print(f"Логин: OK")
                print(f" Токен получен: {token_data.get('access_token', '')[:20]}...")
                
                headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
                
                classify_data = {"text": "У меня болит голова"}
                response = await client.post(
                    f"{backend_url}/classify",
                    json=classify_data,
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"\nКлассификация через backend: OK")
                    result = response.json()
                    print(f"  ├─ Срочность: {result.get('urgency', 'N/A')}")
                    print(f"  ├─ Тип: {result.get('request_type', 'N/A')}")
                    print(f"  └─ Уверенность: {result.get('confidence', 'N/A')}")
                else:
                    print(f"Ошибка классификации: {response.status_code} - {response.text}")
            else:
                print(f"Ошибка при логине: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Ошибка при логине/классификации: {e}")
    
    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_application())
