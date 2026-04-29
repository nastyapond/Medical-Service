#!/usr/bin/env python3

import requests
import sys
import time

def check_service(name, url, timeout=10):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = time.time() - start_time

        if response.status_code == 200:
            print(f"УСПЕШНО {name}: ответ получен ({response_time:.2f}с)")
            return True, response.json()
        else:
            print(f"ОШИБКА {name}: HTTP {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"ОШИБКА {name}: не удалось подключиться - {e}")
        return False, None

def check_ml_service():
    try:
        response = requests.post("http://localhost:5000/classify",
                               json={"text": "У меня болит голова срочно"},
                               timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"УСПЕШНО классификация ML: {data}")
            return True
        else:
            print(f"ОШИБКА классификации ML: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"ОШИБКА классификации ML: {e}")
        return False

def check_backend_auth():
    try:
        unique_id = int(time.time())
        register_data = {
            "full_name": "Health Check User",
            "email": f"healthcheck_{unique_id}@example.com",
            "phone": f"+1234567{unique_id % 1000:03d}",
            "password": "Password123"
        }

        response = requests.post("http://localhost:8001/auth/register",
                               json=register_data,
                               timeout=10)

        if response.status_code == 200:
            print("УСПЕШНО регистрация в backend")

            login_response = requests.post("http://localhost:8001/auth/login",
                                         json={"email": register_data["email"], "password": "Password123"},
                                         timeout=10)

            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                if token:
                    print("УСПЕШНО вход в backend")

                    headers = {"Authorization": f"Bearer {token}"}
                    classify_response = requests.post("http://localhost:8001/classify",
                                                    json={"text": "У меня болит голова срочно"},
                                                    headers=headers,
                                                    timeout=30)

                    if classify_response.status_code == 200:
                        print("УСПЕШНО классификация через backend")
                        return True
                    else:
                        print(f"ОШИБКА классификации backend: HTTP {classify_response.status_code}")
                        return False
                else:
                    print("ОШИБКА входа в backend: токен не получен")
                    return False
            else:
                print(f"ОШИБКА входа в backend: HTTP {login_response.status_code}")
                return False
        else:
            print(f"ОШИБКА регистрации backend: HTTP {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"FAIL Backend Auth: {e}")
        return False

def main():
    print("Проверка работоспособности медицинского приложения\n")

    backend_ok, _ = check_service("Backend API", "http://localhost:8001/")
    ml_ok, _ = check_service("ML Service", "http://localhost:5000/")

    if ml_ok:
        ml_classify_ok = check_ml_service()
    else:
        ml_classify_ok = False

    if backend_ok:
        backend_auth_ok = check_backend_auth()
    else:
        backend_auth_ok = False

    print("\n" + "="*50)
    print("ИТОГ:")
    print(f"Backend API: {'УСПЕШНО' if backend_ok else 'ОШИБКА'}")
    print(f"ML Service: {'УСПЕШНО' if ml_ok else 'ОШИБКА'}")
    print(f"ML Classification: {'УСПЕШНО' if ml_classify_ok else 'ОШИБКА'}")
    print(f"Backend Auth & Classification: {'УСПЕШНО' if backend_auth_ok else 'ОШИБКА'}")

    all_ok = backend_ok and ml_ok and ml_classify_ok and backend_auth_ok
    if all_ok:
        print("\nВсе сервисы работают корректно!")
        sys.exit(0)
    else:
        print("\nНекоторые сервисы работают с ошибками. Проверьте вывод выше.")
        sys.exit(1)

if __name__ == "__main__":
    main()