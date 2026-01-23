# services/tts-service/src/engines/elevenlabs_engine.py
from elevenlabs import generate, set_api_key, Voice
from config import Settings
import io

settings = Settings()
set_api_key(settings.elevenlabs_api_key)


class ElevenLabsEngine:
    def __init__(self):
        self.voice_id = settings.elevenlabs_voice_id
        self.model = settings.elevenlabs_model

    def synthesize(self, text: str) -> bytes:
        """Convert text to speech using ElevenLabs API"""
        audio = generate(
            text=text, voice=Voice(voice_id=self.voice_id), model=self.model
        )

        # ElevenLabs returns bytes directly
        return audio

    def synthesize_stream(self, text: str):
        """Stream audio for long text"""
        # Split into sentences
        sentences = self._split_sentences(text)

        for sentence in sentences:
            audio_bytes = self.synthesize(sentence)

            # Chunk for streaming
            chunk_size = 4096
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i : i + chunk_size]

    def _split_sentences(self, text: str) -> list[str]:
        import re

        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]
