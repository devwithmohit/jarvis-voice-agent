from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # TTS Engine
    tts_engine: str = "coqui"  # "coqui" or "elevenlabs"

    # Coqui settings
    coqui_model: str = "tts_models/en/ljspeech/tacotron2-DDC"
    use_gpu: bool = False

    # ElevenLabs (optional)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice

    # Audio settings
    sample_rate: int = 22050
    audio_format: str = "wav"

    # Cache
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2  # Different DB than rate limiting

    # gRPC
    grpc_port: int = 50053
    grpc_host: str = "0.0.0.0"

    # Model cache
    model_cache_dir: str = "./models"

    # Streaming
    chunk_size: int = 4096  # Bytes per audio chunk

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
