import httpx
import asyncio

async def test_full_system():
    print("1. Тестирование ML сервиса напрямую...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5000/classify",
                json={"text": "У меня болит голова уже неделю"}
            )
            print(f"Ответ ML сервиса: {response.json()}")
    except Exception as e:
        print(f"Ошибка ML сервиса: {e}")
        return

    print("\n2. Тест backend пропущен (требуется аутентификация)")

    print("\nСистемный тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_full_system())