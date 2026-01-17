"""
Rate Limiter - Token bucket rate limiting using Redis
Tracks per-user, per-tool rate limits
"""

import redis
from typing import Optional
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from config import get_settings

settings = get_settings()


class RateLimiter:
    """
    Token bucket rate limiter using Redis
    Supports per-user, per-tool rate limiting
    """

    def __init__(self):
        """Initialize rate limiter with Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
            )
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}")
            self.redis_client = None

    def check_rate_limit(
        self, user_id: str, tool_name: str, limit: int, period: str
    ) -> bool:
        """
        Check if request is within rate limit

        Args:
            user_id: User identifier
            tool_name: Tool name
            limit: Maximum requests allowed
            period: Time period (e.g., 'minute', 'hour')

        Returns:
            True if allowed, False if rate limit exceeded
        """
        if not self.redis_client:
            # If Redis unavailable, allow (fail open)
            return True

        # Convert period to seconds
        period_seconds = self._period_to_seconds(period)
        if period_seconds == 0:
            return True

        # Generate Redis key
        key = f"rate_limit:{user_id}:{tool_name}"

        try:
            # Get current count
            current = self.redis_client.get(key)

            if current is None:
                # First request in period
                self.redis_client.setex(key, period_seconds, 1)
                return True

            current_count = int(current)

            if current_count >= limit:
                # Rate limit exceeded
                return False

            # Increment count
            self.redis_client.incr(key)
            return True

        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True  # Fail open

    def get_remaining(
        self, user_id: str, tool_name: str, limit: int, period: str
    ) -> Optional[int]:
        """
        Get remaining requests in current period

        Args:
            user_id: User identifier
            tool_name: Tool name
            limit: Maximum requests allowed
            period: Time period

        Returns:
            Remaining requests or None if unavailable
        """
        if not self.redis_client:
            return None

        key = f"rate_limit:{user_id}:{tool_name}"

        try:
            current = self.redis_client.get(key)
            if current is None:
                return limit

            current_count = int(current)
            return max(0, limit - current_count)
        except Exception:
            return None

    def reset(self, user_id: str, tool_name: str) -> None:
        """
        Reset rate limit for user and tool

        Args:
            user_id: User identifier
            tool_name: Tool name
        """
        if not self.redis_client:
            return

        key = f"rate_limit:{user_id}:{tool_name}"

        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Rate limit reset error: {e}")

    def _period_to_seconds(self, period: str) -> int:
        """
        Convert period string to seconds

        Args:
            period: Period string (e.g., 'second', 'minute', 'hour', 'day')

        Returns:
            Number of seconds
        """
        period = period.lower().strip()

        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }

        return period_map.get(period, 0)
