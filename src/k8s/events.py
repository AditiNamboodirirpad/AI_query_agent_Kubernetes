# Functions to get recent events from the cluster
# Warnings are sorted to the top since they usually indicate problems
from kubernetes import client


def list_events(namespace="default", limit=20):
    api = client.CoreV1Api()
    events = api.list_namespaced_event(namespace=namespace)

    # Put warnings first, then sort by most recent
    def sort_key(e):
        ts = e.last_timestamp or e.event_time
        return (0 if e.type == "Warning" else 1, -(ts.timestamp() if ts else 0))

    recent = sorted(events.items, key=sort_key)[:limit]

    result = []
    for e in recent:
        result.append({
            "type": e.type,
            "reason": e.reason,
            "message": e.message,
            "object": (
                f"{e.involved_object.kind}/{e.involved_object.name}"
                if e.involved_object else "Unknown"
            ),
            "count": e.count or 1,
            "last_seen": str(e.last_timestamp) if e.last_timestamp else None,
        })

    return result
