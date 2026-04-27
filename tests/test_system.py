import httpx
import asyncio

async def test_full_system():
    # Тест ML сервиса напрямую
    print("1. Testing ML service directly...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:5000/classify",
                json={"text": "У меня болит голова уже неделю"}
            )
            print(f"ML Service Response: {response.json()}")
    except Exception as e:
        print(f"ML Service Error: {e}")
        return

    # Тест backend (нужен токен, так что пропустим пока)
    print("\n2. Backend test skipped (requires authentication)")

    print("\nSystem test completed!")

if __name__ == "__main__":
    asyncio.run(test_full_system())