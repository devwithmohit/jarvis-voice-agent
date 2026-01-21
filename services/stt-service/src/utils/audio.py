import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def bytes_to_audio_array(audio_bytes: bytes, dtype: str = "int16") -> np.ndarray:
    """Convert audio bytes to numpy array

    Args:
        audio_bytes: Raw audio bytes
        dtype: Data type ('int16' or 'float32')

    Returns:
        Numpy array normalized to [-1, 1] for float32
    """
    if dtype == "int16":
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        # Normalize to float32 [-1, 1]
        return audio_array.astype(np.float32) / 32768.0
    elif dtype == "float32":
        return np.frombuffer(audio_bytes, dtype=np.float32)
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")


def validate_audio_format(
    audio_data: np.ndarray, expected_sample_rate: int = 16000
) -> bool:
    """Validate audio data format

    Args:
        audio_data: Audio samples as numpy array
        expected_sample_rate: Expected sample rate

    Returns:
        True if valid, False otherwise
    """
    # Check if audio is not empty
    if len(audio_data) == 0:
        logger.warning("Audio data is empty")
        return False

    # Check if audio length is reasonable (at least 0.1 seconds)
    min_samples = expected_sample_rate * 0.1
    if len(audio_data) < min_samples:
        logger.warning(f"Audio too short: {len(audio_data)} samples")
        return False

    # Check if values are normalized
    if audio_data.dtype == np.float32:
        if np.abs(audio_data).max() > 1.0:
            logger.warning("Audio values exceed [-1, 1] range")
            return False

    return True


def resample_audio(
    audio_data: np.ndarray, original_rate: int, target_rate: int
) -> np.ndarray:
    """Resample audio to target sample rate

    Args:
        audio_data: Audio samples
        original_rate: Original sample rate
        target_rate: Target sample rate

    Returns:
        Resampled audio
    """
    if original_rate == target_rate:
        return audio_data

    try:
        from scipy import signal

        # Calculate resampling ratio
        ratio = target_rate / original_rate
        num_samples = int(len(audio_data) * ratio)

        # Resample using scipy
        resampled = signal.resample(audio_data, num_samples)
        return resampled.astype(np.float32)

    except ImportError:
        logger.error("scipy not installed, cannot resample")
        return audio_data
