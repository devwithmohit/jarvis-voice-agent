import numpy as np
import webrtcvad
from typing import Iterator, Optional
import logging

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Process audio streams with Voice Activity Detection"""

    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30):
        """
        Args:
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000)
            frame_duration_ms: Frame duration (10, 20, or 30 ms)
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3

        # Calculate frame size in bytes
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.frame_bytes = self.frame_size * 2  # 2 bytes per int16 sample

        logger.info(
            f"StreamProcessor initialized: {sample_rate}Hz, {frame_duration_ms}ms frames"
        )

    def is_speech(self, audio_frame: bytes) -> bool:
        """Check if audio frame contains speech

        Args:
            audio_frame: Raw audio bytes (int16 PCM)

        Returns:
            True if speech detected, False otherwise
        """
        try:
            return self.vad.is_speech(audio_frame, self.sample_rate)
        except Exception as e:
            logger.warning(f"VAD error: {e}")
            return False

    def process_stream(
        self,
        audio_chunks: Iterator[bytes],
        padding_duration_ms: int = 300,
        min_speech_duration_ms: int = 500,
    ) -> Iterator[bytes]:
        """Process audio stream and yield speech segments

        Args:
            audio_chunks: Iterator of audio byte chunks
            padding_duration_ms: Padding before/after speech (milliseconds)
            min_speech_duration_ms: Minimum speech duration to yield

        Yields:
            Audio segments containing speech
        """
        buffer = bytearray()
        num_padding_frames = padding_duration_ms // self.frame_duration_ms
        num_min_speech_frames = min_speech_duration_ms // self.frame_duration_ms

        ring_buffer = [None] * num_padding_frames
        ring_buffer_index = 0

        triggered = False
        voiced_frames = []

        for chunk in audio_chunks:
            buffer.extend(chunk)

            # Process complete frames
            while len(buffer) >= self.frame_bytes:
                frame = bytes(buffer[: self.frame_bytes])
                buffer = buffer[self.frame_bytes :]

                is_speech = self.is_speech(frame)

                if not triggered:
                    # Not in speech segment
                    ring_buffer[ring_buffer_index] = (frame, is_speech)
                    ring_buffer_index = (ring_buffer_index + 1) % num_padding_frames

                    num_voiced = sum(
                        1 for f, speech in ring_buffer if f is not None and speech
                    )

                    if num_voiced > 0.5 * num_padding_frames:
                        triggered = True
                        # Yield buffered frames
                        for f, _ in ring_buffer:
                            if f is not None:
                                voiced_frames.append(f)
                        ring_buffer = [None] * num_padding_frames
                        ring_buffer_index = 0
                else:
                    # In speech segment
                    voiced_frames.append(frame)
                    ring_buffer[ring_buffer_index] = (frame, is_speech)
                    ring_buffer_index = (ring_buffer_index + 1) % num_padding_frames

                    num_unvoiced = sum(
                        1 for f, speech in ring_buffer if f is not None and not speech
                    )

                    if num_unvoiced > 0.9 * num_padding_frames:
                        # End of speech segment
                        triggered = False

                        if len(voiced_frames) >= num_min_speech_frames:
                            # Yield speech segment
                            segment = b"".join(voiced_frames)
                            logger.info(f"Speech segment: {len(segment)} bytes")
                            yield segment

                        voiced_frames = []
                        ring_buffer = [None] * num_padding_frames
                        ring_buffer_index = 0

        # Yield remaining frames if any
        if voiced_frames and len(voiced_frames) >= num_min_speech_frames:
            segment = b"".join(voiced_frames)
            logger.info(f"Final speech segment: {len(segment)} bytes")
            yield segment
