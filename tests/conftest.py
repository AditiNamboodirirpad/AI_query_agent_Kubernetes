"""Shared pytest fixtures."""
import os
from unittest.mock import MagicMock, patch

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

# Provide a dummy API key so Settings() doesn't fail during tests
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")


@pytest.fixture
def mock_k8s_pods():
    """A minimal mock pod object."""
    pod = MagicMock()
    pod.metadata.name = "nginx-abc123"
    pod.metadata.namespace = "default"
    pod.status.phase = "Running"
    pod.spec.node_name = "minikube"
    pod.status.container_statuses = []
    pod.status.conditions = []
    return pod


@pytest.fixture
def mock_k8s_deployment():
    """A minimal mock deployment object."""
    dep = MagicMock()
    dep.metadata.name = "nginx"
    dep.metadata.namespace = "default"
    dep.spec.replicas = 2
    dep.status.ready_replicas = 2
    dep.status.available_replicas = 2
    dep.status.updated_replicas = 2
    dep.spec.strategy.type = "RollingUpdate"
    dep.spec.template.spec.containers = []
    dep.status.conditions = []
    return dep


@pytest.fixture
def mock_k8s_node():
    """A minimal mock node object."""
    node = MagicMock()
    node.metadata.name = "minikube"
    node.metadata.labels = {}
    node.spec.unschedulable = False
    ready = MagicMock()
    ready.type = "Ready"
    ready.status = "True"
    ready.reason = "KubeletReady"
    node.status.conditions = [ready]
    node.status.addresses = []
    node.status.allocatable = {}
    return node


@pytest.fixture
def test_client():
    """FastAPI TestClient with K8s init and graph build mocked out."""
    with patch("src.k8s.client.init_k8s"), patch(
        "src.agent.graph.build_agent_graph"
    ) as mock_graph:
        mock_result = {"messages": [MagicMock(content="Mocked AI answer.")]}
        mock_graph.return_value.ainvoke = AsyncMock(return_value=mock_result)

        from src.api.app import create_app

        app = create_app()
        yield TestClient(app, raise_server_exceptions=True)
