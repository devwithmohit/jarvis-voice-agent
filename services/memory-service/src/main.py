"""
Main FastAPI application for Memory Service
Combines REST API and gRPC server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.memory_routes import router as memory_router
from api.admin_routes import router as admin_router
from config import get_settings
from models import HealthResponse
from datetime import datetime

settings = get_settings()


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    Start gRPC server on startup, cleanup on shutdown
    """
    # Startup
    print("=" * 60)
    print(f"Starting {settings.service_name}")
    print("=" * 60)

    # Start gRPC server in background thread
    if settings.grpc_port:
        from grpc_server import serve

        grpc_thread = threading.Thread(target=serve, daemon=True)
        grpc_thread.start()
        print(f"✓ gRPC server starting on port {settings.grpc_port}")

    # Test connections
    try:
        from utils.cache import redis_client

        redis_client.ping()
        print("✓ Redis connection: OK")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")

    try:
        from utils.db import test_connection

        test_connection()
        print("✓ PostgreSQL connection: OK")
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")

    print("=" * 60)
    print(f"✓ REST API running on http://{settings.api_host}:{settings.api_port}")
    print(
        f"✓ Documentation available at http://{settings.api_host}:{settings.api_port}/docs"
    )
    print("=" * 60)

    yield

    # Shutdown
    print("\nShutting down Memory Service...")


# Create FastAPI app
app = FastAPI(
    title="Memory Service API",
    description="Voice AI Agent Memory Service - Manages short-term, long-term, episodic, and semantic memory",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memory_router)
app.include_router(admin_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "memory_api": "/api/v1/memory",
            "admin_api": "/api/v1/admin",
        },
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check for all components
    """
    components = {}
    overall_status = "healthy"

    # Check Redis
    try:
        from utils.cache import redis_client

        redis_client.ping()
        components["redis"] = "healthy"
    except Exception as e:
        components["redis"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"

    # Check PostgreSQL
    try:
        from utils.db import test_connection

        test_connection()
        components["postgresql"] = "healthy"
    except Exception as e:
        components["postgresql"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"

    # Check FAISS
    try:
        from stores.semantic import SemanticStore

        store = SemanticStore()
        stats = store.get_stats()
        components["faiss"] = f"healthy ({stats.get('total_vectors', 0)} vectors)"
    except Exception as e:
        components["faiss"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version="1.0.0",
        timestamp=datetime.now(),
        components=components,
    )


# Metrics endpoint (placeholder for Prometheus integration)
@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring
    Can be extended with Prometheus metrics
    """
    from stores.semantic import SemanticStore
    from stores.episodic import EpisodicStore

    try:
        semantic_store = SemanticStore()
        semantic_stats = semantic_store.get_stats()

        # Get sample user stats (if available)
        # episodic_stats = episodic_store.get_event_stats("sample_user")

        return {
            "service": settings.service_name,
            "semantic_store": semantic_stats,
            "timestamp": datetime.now(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now()}


def main():
    """
    Run the FastAPI application
    """
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
