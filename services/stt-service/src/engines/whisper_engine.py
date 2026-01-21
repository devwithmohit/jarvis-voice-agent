from faster_whisper import WhisperModel
from typing import Iterator, Tuple, Optional
import numpy as np
from config import Settings
import logging

logger = logging.getLogger(__name__)
settings = Settings()


class WhisperEngine:
    """Whisper-based speech recognition engine with streaming support"""

    def __init__(self):
        logger.info(f"Loading Whisper model: {settings.whisper_model}")
        self.model = WhisperModel(
            settings.whisper_model,
            device=settings.device,
            compute_type=settings.compute_type,
            download_root=settings.model_cache_dir,
        )
        self.sample_rate = settings.sample_rate
        logger.info("Whisper model loaded successfully")

    def transcribe_audio(
        self, audio_data: np.ndarray, language: str = "en"
    ) -> Tuple[str, float]:
        """Transcribe complete audio buffer

        Args:
            audio_data: Audio samples as numpy array (float32, normalized to [-1, 1])
            language: Language code (default: "en")

        Returns:
            Tuple of (transcribed_text, average_confidence)
        """
        try:
            segments, info = self.model.transcribe(
                audio_data,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500, threshold=0.5),
            )

            # Concatenate all segments and calculate average confidence
            texts = []
            confidences = []

            for segment in segments:
                texts.append(segment.text)
                # Faster-whisper doesn't provide confidence, use info.language_probability
                confidences.append(
                    info.language_probability
                    if hasattr(info, "language_probability")
                    else 0.9
                )

            text = " ".join(texts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"Transcribed: '{text}' (confidence: {avg_confidence:.2f})")
            return text, avg_confidence

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "", 0.0

    def transcribe_stream(
        self, audio_chunks: Iterator[bytes]
    ) -> Iterator[Tuple[str, bool, float]]:
        """Stream transcription with partial results

        Args:
            audio_chunks: Iterator of audio byte chunks (int16 PCM)

        Yields:
            Tuple of (text, is_final, confidence)
        """
        buffer = bytearray()
        silence_count = 0
        max_silence = settings.silence_timeout_ms // settings.chunk_duration_ms

        logger.info("Starting streaming transcription")

        for chunk in audio_chunks:
            buffer.extend(chunk)

            # Check if we have enough audio (minimum 1 second)
            if len(buffer) < settings.min_audio_length * 2:  # 2 bytes per int16 sample
                continue

            # Convert to numpy array (int16 -> float32 normalized)
            audio_array = np.frombuffer(bytes(buffer), dtype=np.int16)
            audio_array = audio_array.astype(np.float32) / 32768.0

            # Transcribe current buffer
            text, confidence = self.transcribe_audio(audio_array)

            if text:
                yield (text, False, confidence)  # Partial result
                silence_count = 0
            else:
                silence_count += 1

            # If silence exceeded, finalize
            if silence_count >= max_silence and text:
                logger.info(f"Silence detected, finalizing: '{text}'")
                yield (text, True, confidence)  # Final result
                buffer.clear()
                silence_count = 0
