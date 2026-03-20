# Wraps each Kubernetes function as a LangGraph tool
# The @tool decorator lets the agent decide when to call each one
import json
from langchain_core.tools import tool
from src.k8s import pods, deployments, nodes, services, events, health


@tool
def list_pods_tool(namespace: str = "default") -> str:
    """List all pods in a Kubernetes namespace.

    Returns each pod's name, phase, node assignment, container states,
    and restart counts. Use this for questions about pod status, counts,
    or which pods are running/failing.
    """
    return json.dumps(pods.list_pods(namespace), indent=2)


@tool
def get_pod_logs_tool(pod_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
    """Fetch recent logs from a specific pod.

    Use for questions like 'show me the logs for pod X' or 'what errors
    is pod Y producing?'. Returns the last tail_lines lines of stdout/stderr.
    """
    return pods.get_pod_logs(pod_name, namespace, tail_lines)


@tool
def list_deployments_tool(namespace: str = "default") -> str:
    """List all Kubernetes Deployments with replica counts and health conditions.

    Use for questions about deployment status, replica availability,
    rollout state, or which images are running.
    """
    return json.dumps(deployments.list_deployments(namespace), indent=2)


@tool
def list_nodes_tool() -> str:
    """List all cluster nodes with their readiness, capacity, and IP addresses.

    Use for questions about node count, node health, resource capacity,
    or whether any nodes are cordoned/unschedulable.
    """
    return json.dumps(nodes.list_nodes(), indent=2)


@tool
def list_services_tool(namespace: str = "default") -> str:
    """List all Kubernetes Services with type, ports, and selectors.

    Use for questions about how workloads are exposed, what ports are open,
    or which services exist in a namespace.
    """
    return json.dumps(services.list_services(namespace), indent=2)


@tool
def list_events_tool(namespace: str = "default") -> str:
    """List recent Kubernetes events, with Warnings surfaced first.

    Essential for diagnosing scheduling failures, image pull errors,
    OOMKills, and other operational issues. Always check events when
    a resource is unhealthy.
    """
    return json.dumps(events.list_events(namespace), indent=2)


@tool
def get_cluster_health_tool(namespace: str = "default") -> str:
    """Compute a health score (0-100) for the cluster with issue breakdown.

    Returns overall status (healthy / degraded / critical), a pod/node/
    deployment summary, and a prioritised list of issues with remediation
    suggestions. Use proactively for any 'how is my cluster doing?' questions.
    """
    return json.dumps(health.compute_cluster_health(namespace), indent=2)


ALL_TOOLS = [
    list_pods_tool,
    get_pod_logs_tool,
    list_deployments_tool,
    list_nodes_tool,
    list_services_tool,
    list_events_tool,
    get_cluster_health_tool,
]
