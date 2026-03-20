# Creates the FastAPI app and registers all routes
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import query, health, cluster
from src.config import get_settings
from src.k8s.client import init_k8s


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts
    os.makedirs("logs", exist_ok=True)
    init_k8s()
    yield


def create_app():
    settings = get_settings()

    app = FastAPI(
        lifespan=lifespan,
        title="K8sGPT",
        description="Ask your Kubernetes cluster questions in plain English.",
        version=settings.app_version,
    )

    # Allow all origins so the Swagger UI works without issues
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(query.router)
    app.include_router(health.router)
    app.include_router(cluster.router)

    return app
