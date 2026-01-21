from TTS.api import TTS
import numpy as np
import io
import soundfile as sf
from typing import Iterator, List
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


class CoquiEngine:
    """Coqui TTS engine for text-to-speech synthesis"""

    def __init__(self):
        logger.info(f"Loading Coqui TTS model: {settings.coqui_model}")
        try:
            self.tts = TTS(
                model_name=settings.coqui_model,
                progress_bar=False,
                gpu=settings.use_gpu,
            )
            logger.info("Coqui TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise

    def synthesize(self, text: str, voice_id: str = None, speed: float = 1.0) -> bytes:
        """Convert text to speech audio bytes

        Args:
            text: Text to synthesize
            voice_id: Voice profile ID (optional)
            speed: Speech speed multiplier (0.5 - 2.0)

        Returns:
            Audio data as WAV bytes
        """
        try:
            logger.info(f"Synthesizing: '{text[:50]}...' (speed: {speed})")

            # Generate audio as numpy array
            wav = self.tts.tts(text)

            # Apply speed adjustment if needed
            if speed != 1.0:
                wav = self._adjust_speed(np.array(wav), speed)

            # Convert to bytes (WAV format)
            buffer = io.BytesIO()
            sf.write(buffer, np.array(wav), settings.sample_rate, format="WAV")
            buffer.seek(0)

            audio_bytes = buffer.read()
            logger.info(f"Synthesized {len(audio_bytes)} bytes")

            return audio_bytes

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise

    def synthesize_stream(
        self, text: str, voice_id: str = None, speed: float = 1.0
    ) -> Iterator[bytes]:
        """Stream audio in chunks (for long text)

        Args:
            text: Text to synthesize
            voice_id: Voice profile ID (optional)
            speed: Speech speed multiplier

        Yields:
            Audio chunks as bytes
        """
        # Split text into sentences
        sentences = self._split_sentences(text)
        logger.info(f"Streaming {len(sentences)} sentences")

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            logger.info(
                f"Synthesizing sentence {i + 1}/{len(sentences)}: '{sentence[:50]}...'"
            )

            # Generate audio for this sentence
            audio_bytes = self.synthesize(sentence, voice_id, speed)

            # Chunk the audio for streaming
            for chunk_start in range(0, len(audio_bytes), settings.chunk_size):
                chunk = audio_bytes[chunk_start : chunk_start + settings.chunk_size]
                yield chunk

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences for streaming

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        import re

        # Split on sentence boundaries
        sentences = re.split(r"([.!?]+\s+)", text)

        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (
                sentences[i + 1] if i + 1 < len(sentences) else ""
            )
            result.append(sentence.strip())

        # Add last sentence if odd number
        if len(sentences) % 2 == 1:
            result.append(sentences[-1].strip())

        return [s for s in result if s]

    def _adjust_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Adjust audio playback speed

        Args:
            audio: Audio samples
            speed: Speed multiplier

        Returns:
            Speed-adjusted audio
        """
        try:
            from scipy import signal

            # Resample to adjust speed
            new_length = int(len(audio) / speed)
            adjusted = signal.resample(audio, new_length)

            return adjusted.astype(np.float32)

        except ImportError:
            logger.warning("scipy not available, speed adjustment disabled")
            return audio
