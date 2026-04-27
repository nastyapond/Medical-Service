import requests
import time

unique_id = int(time.time())
unique_email = f"test_{unique_id}@example.com"
unique_phone = f"+7123456{unique_id % 1000}"

ml_response = requests.post("http://localhost:5000/classify", json={"text": "У меня болит голова срочно"})
print("ML Service Response:", ml_response.json())

register_response = requests.post("http://localhost:8000/auth/register", json={
    "full_name": "Test User",
    "email": unique_email,
    "phone": unique_phone,
    "password": "Password123"
})
print("Register Response:", register_response.json())

login_response = requests.post("http://localhost:8000/auth/login", json={"email": unique_email, "password": "Password123"})
token = login_response.json()["access_token"]
print("Token received:", token[:50] + "...")

headers = {"Authorization": f"Bearer {token}"}
classify_response = requests.post("http://localhost:8001/classify", json={"text": "У меня болит голова срочно"}, headers=headers)
print("Backend Response Status:", classify_response.status_code)
print("Backend Response Text:", classify_response.text)
print("Backend Classification Response:", classify_response.json())