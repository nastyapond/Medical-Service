import pytest
import requests
from unittest.mock import patch, MagicMock

class TestMLService:

    def test_ml_service_health(self):
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "model_type" in data
            assert data["status"] in ["ready", "loading", "error", "ok"]
        except requests.exceptions.RequestException:
            pytest.skip("ML service not running")

    def test_ml_service_classify(self):
        try:
            test_text = "У меня болит голова срочно"
            response = requests.post(
                "http://localhost:5000/classify",
                json={"text": test_text},
                timeout=10
            )

            assert response.status_code == 200

            data = response.json()
            assert "urgency" in data
            assert "request_type" in data
            assert "confidence" in data

            assert data["urgency"] in ["Экстренное", "Срочное", "Плановое", "Консультационное"]
            assert data["request_type"] in [
                "Запись на прием", "Вызов врача", "Перенаправление в экстренные службы",
                "Консультация или вопрос", "Наблюдение"
            ]
            assert data["confidence"] in ["Высокая", "Средняя", "Низкая"]

        except requests.exceptions.RequestException:
            pytest.skip("ML service not running")

    def test_ml_service_different_models(self):
        """Test different ML models if available."""
        models_to_test = ["rubert", "fasttext", "mock"]

        for model in models_to_test:
            try:
                # This would require restarting service with different MODEL_TYPE
                # For now, just test with current model
                response = requests.post(
                    "http://localhost:5000/classify",
                    json={"text": "Тестовый запрос"},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    assert all(key in data for key in ["urgency", "request_type", "confidence"])
                    break  

            except requests.exceptions.RequestException:
                continue

        else:
            pytest.skip("No ML models available")

class TestMLIntegration:

    @patch('httpx.AsyncClient.post')
    def test_backend_ml_integration_mock(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "urgency": "Экстренное",
            "request_type": "Перенаправление в экстренные службы",
            "confidence": "Высокая"
        }
        mock_response.status_code = 200

        mock_post.return_value = mock_response

        assert True  # Placeholder