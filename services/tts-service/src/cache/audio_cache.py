import hashlib
import redis
from typing import Optional
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import Settings

logger = logging.getLogger(__name__)
settings = Settings()


class AudioCache:
    """Redis-based cache for TTS audio"""

    def __init__(self):
        if settings.enable_cache:
            try:
                self.redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=False,  # Binary data
                )
                # Test connection
                self.redis.ping()
                logger.info(
                    f"Audio cache connected to Redis: {settings.redis_host}:{settings.redis_port}"
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                logger.warning("Audio caching disabled")
                self.redis = None
        else:
            self.redis = None
            logger.info("Audio caching disabled")

        self.enabled = settings.enable_cache and self.redis is not None
        self.ttl = settings.cache_ttl

    def get(self, text: str, voice_id: str = "", speed: float = 1.0) -> Optional[bytes]:
        """Get cached audio for text

        Args:
            text: Text to synthesize
            voice_id: Voice profile ID
            speed: Speech speed

        Returns:
            Cached audio bytes or None
        """
        if not self.enabled:
            return None

        try:
            key = self._generate_key(text, voice_id, speed)
            cached = self.redis.get(key)

            if cached:
                logger.info(f"Cache HIT: {key[:16]}...")
                return cached
            else:
                logger.debug(f"Cache MISS: {key[:16]}...")
                return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self, text: str, audio_bytes: bytes, voice_id: str = "", speed: float = 1.0
    ):
        """Cache audio for text

        Args:
            text: Text that was synthesized
            audio_bytes: Generated audio data
            voice_id: Voice profile ID
            speed: Speech speed
        """
        if not self.enabled:
            return

        try:
            key = self._generate_key(text, voice_id, speed)
            self.redis.setex(key, self.ttl, audio_bytes)
            logger.info(f"Cached {len(audio_bytes)} bytes for '{text[:30]}...'")

        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def _generate_key(self, text: str, voice_id: str, speed: float) -> str:
        """Generate cache key from text and parameters

        Args:
            text: Text content
            voice_id: Voice profile ID
            speed: Speech speed

        Returns:
            Cache key string
        """
        # Create unique key from all parameters
        key_data = f"{text}|{voice_id}|{speed:.2f}|{settings.coqui_model}"
        text_hash = hashlib.md5(key_data.encode()).hexdigest()

        return f"tts:cache:{text_hash}"

    def clear(self):
        """Clear all TTS cache entries"""
        if not self.enabled:
            return

        try:
            # Delete all keys matching pattern
            keys = self.redis.keys("tts:cache:*")
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            else:
                logger.info("No cache entries to clear")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    def stats(self) -> dict:
        """Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            keys = self.redis.keys("tts:cache:*")

            total_size = 0
            for key in keys:
                value = self.redis.get(key)
                if value:
                    total_size += len(value)

            return {
                "enabled": True,
                "entries": len(keys),
                "total_size_mb": total_size / (1024 * 1024),
                "ttl_seconds": self.ttl,
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}
