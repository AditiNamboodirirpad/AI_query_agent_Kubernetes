"""Unit tests for the Kubernetes data layer."""
from unittest.mock import MagicMock, patch

class TestListPods:
    def test_returns_formatted_pod_data(self, mock_k8s_pods):
        with patch("src.k8s.pods.client") as mock_client:
            mock_client.CoreV1Api.return_value.list_namespaced_pod.return_value.items = [
                mock_k8s_pods
            ]
            from src.k8s.pods import list_pods

            result = list_pods("default")

        assert len(result) == 1
        pod = result[0]
        assert pod["name"] == "nginx-abc123"
        assert pod["phase"] == "Running"
        assert pod["node"] == "minikube"

    def test_empty_namespace_returns_empty_list(self):
        with patch("src.k8s.pods.client") as mock_client:
            mock_client.CoreV1Api.return_value.list_namespaced_pod.return_value.items = []
            from src.k8s.pods import list_pods

            result = list_pods("empty-ns")

        assert result == []

    def test_container_restart_count_captured(self):
        pod = MagicMock()
        pod.metadata.name = "crash-pod"
        pod.metadata.namespace = "default"
        pod.status.phase = "Running"
        pod.spec.node_name = "minikube"
        pod.status.conditions = []

        cs = MagicMock()
        cs.name = "app"
        cs.image = "myapp:latest"
        cs.ready = False
        cs.restart_count = 12
        cs.state.running = None
        cs.state.waiting.reason = "CrashLoopBackOff"
        cs.state.terminated = None
        pod.status.container_statuses = [cs]

        with patch("src.k8s.pods.client") as mock_client:
            mock_client.CoreV1Api.return_value.list_namespaced_pod.return_value.items = [
                pod
            ]
            from src.k8s.pods import list_pods

            result = list_pods()

        assert result[0]["containers"][0]["restart_count"] == 12


class TestClusterHealth:
    def _make_healthy_data(self):
        pods = [{"name": "p1", "phase": "Running", "containers": [], "conditions": []}]
        deps = [
            {
                "name": "d1",
                "desired_replicas": 1,
                "ready_replicas": 1,
                "available_replicas": 1,
                "conditions": [],
            }
        ]
        nodes_data = [
            {
                "name": "n1",
                "unschedulable": False,
                "conditions": [{"type": "Ready", "status": "True"}],
            }
        ]
        return pods, deps, nodes_data

    def test_healthy_cluster_scores_100(self):
        pods, deps, nodes_data = self._make_healthy_data()
        with (
            patch("src.k8s.health.list_pods", return_value=pods),
            patch("src.k8s.health.list_deployments", return_value=deps),
            patch("src.k8s.health.list_nodes", return_value=nodes_data),
        ):
            from src.k8s.health import compute_cluster_health

            result = compute_cluster_health()

        assert result["score"] == 100
        assert result["status"] == "healthy"
        assert result["issues"] == []

    def test_failed_pod_reduces_score(self):
        pods = [{"name": "bad-pod", "phase": "Failed", "containers": [], "conditions": []}]
        _, deps, nodes_data = self._make_healthy_data()
        with (
            patch("src.k8s.health.list_pods", return_value=pods),
            patch("src.k8s.health.list_deployments", return_value=deps),
            patch("src.k8s.health.list_nodes", return_value=nodes_data),
        ):
            from src.k8s.health import compute_cluster_health

            result = compute_cluster_health()

        assert result["score"] < 100
        assert any("Failed" in i["issue"] for i in result["issues"])

    def test_degraded_deployment_reduces_score(self):
        pods, _, nodes_data = self._make_healthy_data()
        deps = [
            {
                "name": "half-dep",
                "desired_replicas": 3,
                "ready_replicas": 1,
                "available_replicas": 1,
                "conditions": [],
            }
        ]
        with (
            patch("src.k8s.health.list_pods", return_value=pods),
            patch("src.k8s.health.list_deployments", return_value=deps),
            patch("src.k8s.health.list_nodes", return_value=nodes_data),
        ):
            from src.k8s.health import compute_cluster_health

            result = compute_cluster_health()

        assert result["score"] < 100
        assert any("replica" in i["issue"] for i in result["issues"])

    def test_score_never_negative(self):
        many_failed_pods = [
            {"name": f"bad-{i}", "phase": "Failed", "containers": [], "conditions": []}
            for i in range(20)
        ]
        with (
            patch("src.k8s.health.list_pods", return_value=many_failed_pods),
            patch("src.k8s.health.list_deployments", return_value=[]),
            patch("src.k8s.health.list_nodes", return_value=[]),
        ):
            from src.k8s.health import compute_cluster_health

            result = compute_cluster_health()

        assert result["score"] >= 0
        assert result["status"] == "critical"
