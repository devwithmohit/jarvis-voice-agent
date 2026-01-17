"""
Configuration management for Agent Core
Uses Pydantic Settings for environment-based configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service Configuration
    service_name: str = "agent-core"
    debug: bool = False
    log_level: str = "INFO"

    # LLM Configuration
    llm_provider: str = "openrouter"  # openrouter, openai, local
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "meta-llama/llama-3.1-8b-instruct"
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.7
    llm_timeout: int = 30

    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = None
    openrouter_site_url: Optional[str] = None
    openrouter_app_name: Optional[str] = "Voice AI Agent"

    # Redis Configuration (for rate limiting)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1  # Different from memory service
    redis_password: Optional[str] = None

    # Memory Service gRPC
    memory_service_host: str = "localhost"
    memory_service_port: int = 50051

    # Tool Executor gRPC
    tool_executor_host: str = "localhost"
    tool_executor_port: int = 50055

    # Web Service gRPC
    web_service_host: str = "localhost"
    web_service_port: int = 50056

    # gRPC Configuration
    grpc_port: int = 50052
    grpc_max_workers: int = 10

    # FastAPI Configuration
    api_port: int = 8002
    api_host: str = "0.0.0.0"

    # Security Configuration
    enable_rate_limiting: bool = True
    default_rate_limit: int = 20  # requests per minute
    max_plan_actions: int = 5  # Max actions in single plan
    require_confirmation_for_destructive: bool = True

    # Intent Classification
    intent_confidence_threshold: float = 0.7
    use_llm_fallback: bool = True

    # Conversation Management
    conversation_history_limit: int = 10
    session_timeout_seconds: int = 3600  # 1 hour

    # Tool Configuration
    tools_config_path: str = "config/tools.yaml"
    intents_config_path: str = "config/intents.yaml"

    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Settings = None


def get_settings() -> Settings:
    """Get cached settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
