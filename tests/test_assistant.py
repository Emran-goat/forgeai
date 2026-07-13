"""Tests for AI assistant API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_gemma_service():
    """Mock gemma_service for all assistant endpoints."""
    with patch("backend.api.assistant.gemma_service") as mock:
        mock.chat_with_context = AsyncMock(return_value="Test AI response")
        mock.chat = AsyncMock(return_value=AsyncMock())
        yield mock


@pytest.fixture
def mock_parse_setup():
    """Mock parse_setup_request."""
    with patch("backend.api.assistant.parse_setup_request") as mock:
        from backend.models.assistant import OptimizationConfig, OptimizationConstraints

        mock.return_value = (
            OptimizationConfig(
                model_type="vision",
                target_hardware="MI300X",
                constraints=OptimizationConstraints(
                    max_latency_ms=20.0,
                    max_memory_gb=4.0,
                    min_accuracy_retention=0.97,
                ),
                recommended_phases=["pruning", "quantization"],
                parameters={"sparsity": 0.3, "quantization_format": "INT8"},
            ),
            "Test explanation",
            ["Prompt 1", "Prompt 2"],
        )
        yield mock


@pytest.fixture
def mock_generate_run_config():
    """Mock generate_run_config."""
    with patch("backend.api.assistant.generate_run_config") as mock:
        from backend.models.assistant import OptimizationConfig, OptimizationConstraints

        mock.return_value = (
            OptimizationConfig(
                model_type="vision",
                target_hardware="MI300X",
                constraints=OptimizationConstraints(),
                recommended_phases=["pruning"],
                parameters={},
            ),
            "Run config explanation",
        )
        yield mock


@pytest.fixture
def mock_generate_auto_chart():
    """Mock generate_auto_chart."""
    with patch("backend.api.assistant.generate_auto_chart") as mock:
        from backend.models.assistant import ChartData

        mock.return_value = ChartData(
            chart_type="scatter",
            data=[{"x": [1, 2], "y": [3, 4], "type": "scatter", "mode": "markers"}],
            layout={"title": {"text": "Test Chart"}},
        )
        yield mock


class TestSetupEndpoint:
    def test_setup_success(self, client, mock_parse_setup):
        response = client.post(
            "/api/v1/assistant/setup",
            json={"message": "Optimize my ResNet50 for MI300X with 20ms latency"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "explanation" in data
        assert "suggested_prompts" in data
        assert data["config"]["model_type"] == "vision"
        assert data["config"]["target_hardware"] == "MI300X"

    def test_setup_with_model_id(self, client, mock_parse_setup):
        response = client.post(
            "/api/v1/assistant/setup",
            json={
                "message": "Optimize my model",
                "model_id": "test-model-id",
            },
        )
        assert response.status_code == 200

    def test_setup_empty_message(self, client):
        response = client.post(
            "/api/v1/assistant/setup",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_setup_gemma_error(self, client):
        with patch("backend.api.assistant.parse_setup_request", new_callable=AsyncMock) as mock:
            from backend.services.gemma_service import GemmaServiceError

            mock.side_effect = GemmaServiceError("API unavailable")
            response = client.post(
                "/api/v1/assistant/setup",
                json={"message": "Test"},
            )
            assert response.status_code == 503


class TestChatEndpoint:
    def test_chat_success(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Explain these results", "history": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "suggested_followups" in data

    def test_chat_with_history(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={
                "message": "Tell me more",
                "history": [
                    {"role": "user", "content": "What is pruning?"},
                    {"role": "assistant", "content": "Pruning removes weights."},
                ],
            },
        )
        assert response.status_code == 200

    def test_chat_empty_message(self, client):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_chat_gemma_error(self, client):
        with patch("backend.api.assistant.gemma_service") as mock:
            from backend.services.gemma_service import GemmaServiceError

            mock.chat_with_context = AsyncMock(side_effect=GemmaServiceError("Unavailable"))
            response = client.post(
                "/api/v1/assistant/chat",
                json={"message": "Test"},
            )
            assert response.status_code == 503


class TestVisualizeEndpoint:
    def test_visualize_success(self, client, mock_generate_auto_chart, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/visualize",
            json={
                "chart_type": "auto",
                "data": {
                    "candidates": [
                        {"latency_ms": 10, "accuracy": 0.95, "memory_mb": 500, "name": "A"},
                        {"latency_ms": 20, "accuracy": 0.98, "memory_mb": 800, "name": "B"},
                    ]
                },
                "options": {},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "chart" in data
        assert "explanation" in data
        assert "suggested_next" in data

    def test_visualize_empty_data(self, client, mock_generate_auto_chart, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/visualize",
            json={"chart_type": "auto", "data": {}, "options": {}},
        )
        assert response.status_code == 200


class TestRunEndpoint:
    def test_run_success(self, client, mock_generate_run_config):
        response = client.post(
            "/api/v1/assistant/run",
            json={"message": "Optimize for lowest latency", "auto_config": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "optimization_id" in data
        assert "config_generated" in data
        assert "explanation" in data
        assert "websocket_url" in data

    def test_run_with_model_id(self, client, mock_generate_run_config):
        response = client.post(
            "/api/v1/assistant/run",
            json={
                "message": "Optimize my model",
                "model_id": "test-id",
                "auto_config": True,
            },
        )
        assert response.status_code == 200

    def test_run_gemma_error(self, client):
        with patch("backend.api.assistant.generate_run_config", new_callable=AsyncMock) as mock:
            from backend.services.gemma_service import GemmaServiceError

            mock.side_effect = GemmaServiceError("API error")
            response = client.post(
                "/api/v1/assistant/run",
                json={"message": "Test"},
            )
            assert response.status_code == 503


class TestExportEndpoint:
    def test_export_success(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/export",
            json={
                "message": "Export to ONNX",
                "format": "onnx",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["format"] == "onnx"
        assert "download_url" in data
        assert "guide" in data

    def test_export_default_format(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/export",
            json={"message": "Export my model"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "onnx"

    def test_export_torchscript(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/export",
            json={"message": "Export", "format": "torchscript"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "torchscript"

    def test_export_invalid_format(self, client):
        response = client.post(
            "/api/v1/assistant/export",
            json={"message": "Export", "format": "invalid"},
        )
        assert response.status_code == 422


class TestFollowupGeneration:
    def test_followups_for_pruning(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": "What about pruning and sparsity?"},
        )
        assert response.status_code == 200
        followups = response.json()["suggested_followups"]
        assert any("sparsity" in f.lower() for f in followups)

    def test_followups_for_quantization(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": "How does quantization work?"},
        )
        assert response.status_code == 200
        followups = response.json()["suggested_followups"]
        assert any("int" in f.lower() for f in followups)

    def test_followups_for_pareto(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Explain the Pareto tradeoff"},
        )
        assert response.status_code == 200
        followups = response.json()["suggested_followups"]
        assert any("knee" in f.lower() for f in followups)

    def test_followups_default(self, client, mock_gemma_service):
        response = client.post(
            "/api/v1/assistant/chat",
            json={"message": "Hello"},
        )
        assert response.status_code == 200
        followups = response.json()["suggested_followups"]
        assert len(followups) == 3
