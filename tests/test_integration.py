import requests
import time

def test_integration():
    unique_id = int(time.time())
    unique_email = f"test_{unique_id}@example.com"
    unique_phone = f"+7{unique_id % 10000000000:010d}"

    ml_response = requests.post("http://localhost:5000/classify", json={"text": "У меня болит голова срочно"})
    assert ml_response.status_code == 200
    ml_data = ml_response.json()
    print("Ответ ML сервиса:", ml_data)
    assert "urgency" in ml_data
    assert "request_type" in ml_data or "type" in ml_data

    register_response = requests.post("http://localhost:8000/auth/register", json={
        "full_name": "Test User",
        "email": unique_email,
        "phone": unique_phone,
        "password": "Password123"
    })
    assert register_response.status_code == 200
    print("Ответ регистрации:", register_response.json())

    login_response = requests.post("http://localhost:8000/auth/login", json={"email": unique_email, "password": "Password123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    print("Токен доступа получен:", token[:50] + "...")
    assert token

    headers = {"Authorization": f"Bearer {token}"}
    classify_response = requests.post("http://localhost:8000/classify", json={"text": "У меня болит голова срочно"}, headers=headers)
    assert classify_response.status_code == 200
    backend_data = classify_response.json()
    print("Код ответа backend:", classify_response.status_code)
    print("Ответ классификации backend:", backend_data)
    assert "request_type" in backend_data or "type" in backend_data
    assert "urgency" in backend_data