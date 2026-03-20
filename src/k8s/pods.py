# Functions to get pod info and logs from the cluster
from kubernetes import client


def list_pods(namespace="default"):
    api = client.CoreV1Api()
    pods = api.list_namespaced_pod(namespace=namespace)
    result = []

    for pod in pods.items:
        containers = _get_container_info(pod)
        result.append({
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node": pod.spec.node_name,
            "containers": containers,
            "conditions": [
                {"type": c.type, "status": c.status}
                for c in (pod.status.conditions or [])
            ],
        })

    return result


def _get_container_info(pod):
    # Pull out restart count and current state for each container
    containers = []
    for cs in pod.status.container_statuses or []:
        state = "unknown"
        if cs.state.running:
            state = "running"
        elif cs.state.waiting:
            state = f"waiting:{cs.state.waiting.reason}"
        elif cs.state.terminated:
            state = f"terminated:{cs.state.terminated.reason}"

        containers.append({
            "name": cs.name,
            "image": cs.image,
            "ready": cs.ready,
            "restart_count": cs.restart_count,
            "state": state,
        })
    return containers


def get_pod_logs(pod_name, namespace="default", tail_lines=100):
    api = client.CoreV1Api()
    try:
        return api.read_namespaced_pod_log(
            name=pod_name, namespace=namespace, tail_lines=tail_lines
        )
    except Exception as e:
        print(f"Could not fetch logs for {pod_name}: {e}")
        return f"Error fetching logs: {e}"
