# Functions to get deployment info from the cluster
from kubernetes import client


def list_deployments(namespace="default"):
    api = client.AppsV1Api()
    deployments = api.list_namespaced_deployment(namespace=namespace)
    result = []

    for d in deployments.items:
        result.append({
            "name": d.metadata.name,
            "namespace": d.metadata.namespace,
            "desired_replicas": d.spec.replicas,
            "ready_replicas": d.status.ready_replicas or 0,
            "available_replicas": d.status.available_replicas or 0,
            "updated_replicas": d.status.updated_replicas or 0,
            "strategy": d.spec.strategy.type if d.spec.strategy else "Unknown",
            "images": [c.image for c in (d.spec.template.spec.containers or [])],
            "conditions": [
                {"type": c.type, "status": c.status, "reason": c.reason, "message": c.message}
                for c in (d.status.conditions or [])
            ],
        })

    return result
