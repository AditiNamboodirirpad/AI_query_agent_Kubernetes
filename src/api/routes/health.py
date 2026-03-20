# Simple health check endpoint — useful for liveness probes in Kubernetes
from fastapi import APIRouter
from kubernetes import client

from src.api.models import HealthResponse
from src.config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    # Try listing namespaces as a quick way to ping the cluster
    try:
        client.CoreV1Api().list_namespace(_request_timeout=2)
        k8s_status = "connected"
    except Exception:
        k8s_status = "disconnected"

    settings = get_settings()
    return HealthResponse(status="ok", kubernetes=k8s_status, version=settings.app_version)
