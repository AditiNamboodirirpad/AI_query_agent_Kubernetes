# Functions to get service info from the cluster
from kubernetes import client


def list_services(namespace="default"):
    api = client.CoreV1Api()
    services = api.list_namespaced_service(namespace=namespace)
    result = []

    for svc in services.items:
        ports = [
            {
                "port": p.port,
                "target_port": str(p.target_port),
                "protocol": p.protocol,
                "node_port": p.node_port,
            }
            for p in (svc.spec.ports or [])
        ]

        result.append({
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type,
            "cluster_ip": svc.spec.cluster_ip,
            "external_ips": svc.spec.external_i_ps or [],
            "ports": ports,
            "selector": svc.spec.selector or {},
        })

    return result
