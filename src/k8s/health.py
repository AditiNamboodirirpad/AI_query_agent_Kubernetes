# Calculates a health score (0-100) for the cluster
# Points are deducted for failed pods, degraded deployments, and unhealthy nodes
from src.k8s.pods import list_pods
from src.k8s.deployments import list_deployments
from src.k8s.nodes import list_nodes

# How many points each problem type costs
PENALTIES = {
    "pod_not_running": 8,
    "pod_failed": 15,
    "high_restarts": 5,
    "deployment_degraded": 15,
    "node_not_ready": 25,
    "node_cordoned": 10,
}


def compute_cluster_health(namespace="default"):
    pods = list_pods(namespace)
    deployments = list_deployments(namespace)
    nodes = list_nodes()

    issues = []
    score = 100

    score, issues = _check_pods(pods, score, issues)
    score, issues = _check_deployments(deployments, score, issues)
    score, issues = _check_nodes(nodes, score, issues)

    score = max(0, score)
    status = _score_to_status(score)

    return {
        "score": score,
        "status": status,
        "summary": _build_summary(pods, deployments, nodes),
        "issues": sorted(issues, key=lambda i: i["severity"] != "high"),
    }


def _check_pods(pods, score, issues):
    for pod in pods:
        phase = pod.get("phase", "Unknown")

        if phase == "Failed":
            issues.append({
                "severity": "high",
                "resource": f"Pod/{pod['name']}",
                "issue": "Pod is in Failed state",
                "remediation": "Run `kubectl describe pod <name>` and check events.",
            })
            score -= PENALTIES["pod_failed"]
        elif phase not in ("Running", "Succeeded"):
            issues.append({
                "severity": "medium",
                "resource": f"Pod/{pod['name']}",
                "issue": f"Pod is in {phase} state",
                "remediation": "Check pod events and container image availability.",
            })
            score -= PENALTIES["pod_not_running"]

        for container in pod.get("containers", []):
            if container.get("restart_count", 0) > 5:
                issues.append({
                    "severity": "medium",
                    "resource": f"Pod/{pod['name']} → {container['name']}",
                    "issue": f"Container restarted {container['restart_count']} times",
                    "remediation": "Run `kubectl logs <pod> --previous` to see last crash.",
                })
                score -= PENALTIES["high_restarts"]

    return score, issues


def _check_deployments(deployments, score, issues):
    for dep in deployments:
        desired = dep.get("desired_replicas") or 0
        ready = dep.get("ready_replicas") or 0
        if desired > 0 and ready < desired:
            issues.append({
                "severity": "high",
                "resource": f"Deployment/{dep['name']}",
                "issue": f"Only {ready}/{desired} replicas ready",
                "remediation": "Run `kubectl rollout status deployment/<name>`.",
            })
            score -= PENALTIES["deployment_degraded"]

    return score, issues


def _check_nodes(nodes, score, issues):
    for node in nodes:
        if node.get("unschedulable"):
            issues.append({
                "severity": "medium",
                "resource": f"Node/{node['name']}",
                "issue": "Node is cordoned (unschedulable)",
                "remediation": "Run `kubectl uncordon <node>` when ready.",
            })
            score -= PENALTIES["node_cordoned"]

        for condition in node.get("conditions", []):
            if condition["type"] == "Ready" and condition["status"] != "True":
                issues.append({
                    "severity": "high",
                    "resource": f"Node/{node['name']}",
                    "issue": "Node is not Ready",
                    "remediation": "Run `kubectl describe node <name>` to investigate.",
                })
                score -= PENALTIES["node_not_ready"]

    return score, issues


def _score_to_status(score):
    if score >= 80:
        return "healthy"
    elif score >= 50:
        return "degraded"
    return "critical"


def _build_summary(pods, deployments, nodes):
    return {
        "total_pods": len(pods),
        "running_pods": sum(1 for p in pods if p.get("phase") == "Running"),
        "total_deployments": len(deployments),
        "healthy_deployments": sum(
            1 for d in deployments
            if (d.get("ready_replicas") or 0) >= (d.get("desired_replicas") or 0)
        ),
        "total_nodes": len(nodes),
        "ready_nodes": sum(
            1 for n in nodes
            if any(
                c["type"] == "Ready" and c["status"] == "True"
                for c in n.get("conditions", [])
            )
        ),
    }
