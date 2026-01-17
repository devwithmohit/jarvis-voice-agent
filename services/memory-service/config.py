"""
Configuration management for Memory Service
Uses Pydantic Settings for environment-based configuration
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "voice_agent"
    db_user: str = "agent"
    db_password: str = "changeme"

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Memory Settings
    short_term_ttl: int = 86400  # 24 hours
    episodic_retention_days: int = 90
    max_episodic_events_per_query: int = 100

    # FAISS Vector Store
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384
    faiss_index_dir: str = "data/faiss_index"

    # gRPC Configuration
    grpc_port: int = 50051
    grpc_max_workers: int = 10

    # FastAPI Configuration
    api_port: int = 8001
    api_host: str = "0.0.0.0"

    # Service Configuration
    service_name: str = "memory-service"
    debug: bool = False
    log_level: str = "INFO"

    # Database Pool Settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
