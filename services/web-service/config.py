from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # gRPC
    grpc_port: int = 50056
    grpc_host: str = "0.0.0.0"

    # Browser
    headless: bool = True
    browser_timeout_ms: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Security
    max_redirects: int = 5
    max_page_size_mb: int = 50

    # Search
    default_search_engine: str = "google"
    max_search_results: int = 10

    # API Keys (optional)
    serpapi_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
