# Functions to get node info from the cluster
from kubernetes import client


def list_nodes():
    api = client.CoreV1Api()
    nodes = api.list_node()
    result = []

    for node in nodes.items:
        addresses = {a.type: a.address for a in (node.status.addresses or [])}
        allocatable = _get_allocatable(node)

        result.append({
            "name": node.metadata.name,
            "internal_ip": addresses.get("InternalIP", "Unknown"),
            "hostname": addresses.get("Hostname", "Unknown"),
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason}
                for c in (node.status.conditions or [])
            ],
            "allocatable": allocatable,
            # Unschedulable means the node is cordoned
            "unschedulable": bool(node.spec.unschedulable),
            # Skip default kubernetes.io labels to keep it readable
            "labels": {
                k: v for k, v in (node.metadata.labels or {}).items()
                if not k.startswith("kubernetes.io/")
            },
        })

    return result


def _get_allocatable(node):
    # How much CPU, memory, and pods this node can still handle
    if not node.status.allocatable:
        return {}
    return {
        "cpu": node.status.allocatable.get("cpu"),
        "memory": node.status.allocatable.get("memory"),
        "pods": node.status.allocatable.get("pods"),
    }
