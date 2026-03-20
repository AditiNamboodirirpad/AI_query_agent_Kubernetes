"""Integration tests for the FastAPI layer."""
from unittest.mock import MagicMock, patch


class TestHealthEndpoint:
    def test_returns_ok_when_k8s_connected(self, test_client):
        with patch("src.api.routes.health.client") as mock_k8s:
            mock_k8s.CoreV1Api.return_value.list_namespace.return_value = MagicMock()
            response = test_client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["kubernetes"] == "connected"
        assert "version" in body

    def test_returns_disconnected_when_k8s_unreachable(self, test_client):
        with patch("src.api.routes.health.client") as mock_k8s:
            mock_k8s.CoreV1Api.return_value.list_namespace.side_effect = Exception(
                "unreachable"
            )
            response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["kubernetes"] == "disconnected"


class TestQueryEndpoint:
    def test_basic_query_returns_answer(self, test_client):
        response = test_client.post(
            "/query",
            json={"query": "How many pods are running?", "session_id": "test-session"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "How many pods are running?"
        assert body["answer"] == "Mocked AI answer."
        assert body["session_id"] == "test-session"

    def test_empty_query_rejected(self, test_client):
        response = test_client.post("/query", json={"query": ""})
        assert response.status_code == 422

    def test_clear_session_endpoint(self, test_client):
        response = test_client.delete("/sessions/test-session")
        assert response.status_code == 200
        body = response.json()
        assert body["session_id"] == "test-session"
        assert "cleared" in body["message"]
