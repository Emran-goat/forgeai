"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_models(client):
    """Test list models endpoint."""
    response = client.get("/api/models")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_hardware(client):
    """Test list hardware endpoint."""
    response = client.get("/api/hardware")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_list_candidates(client):
    """Test list candidates endpoint."""
    response = client.get("/api/candidates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
