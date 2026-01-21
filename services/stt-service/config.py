from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Whisper model
    whisper_model: str = "base.en"  # tiny.en, base.en, small.en, medium.en
    device: str = "cpu"  # or "cuda"
    compute_type: str = "int8"  # int8, float16, float32

    # Audio settings
    sample_rate: int = 16000
    chunk_duration_ms: int = 30  # VAD chunk size

    # gRPC
    grpc_port: int = 50052
    grpc_host: str = "0.0.0.0"

    # Streaming
    silence_timeout_ms: int = 1500  # Stop transcription after silence
    min_audio_length: int = 16000  # 1 second minimum (sample_rate * 1)

    # Model download
    model_cache_dir: str = "./models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
