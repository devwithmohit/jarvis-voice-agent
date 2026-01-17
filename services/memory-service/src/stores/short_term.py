"""
Short-term memory store using Redis
Manages session context with TTL (time-to-live)
"""

import json
from typing import Optional, Dict, Any, List
from redis import Redis
from redis.exceptions import RedisError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

settings = get_settings()


class ShortTermStore:
    """
    Short-term memory backed by Redis
    Stores session context with 24-hour default TTL
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = settings.short_term_ttl

    def store(
        self, session_id: str, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Store session context in Redis with TTL

        Args:
            session_id: Unique session identifier
            key: Context key (e.g., 'conversation_history', 'user_location')
            value: Value to store (will be JSON-serialized)
            ttl: Time-to-live in seconds (default: 24 hours)

        Returns:
            bool: Success status
        """
        redis_key = f"session:{session_id}:{key}"
        ttl = ttl or self.default_ttl

        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list, str, int, float, bool)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)

            # Store with TTL
            self.redis.setex(redis_key, ttl, serialized)
            return True
        except (RedisError, TypeError, ValueError) as e:
            print(f"Error storing short-term memory [{redis_key}]: {e}")
            return False

    def retrieve(self, session_id: str, key: str) -> Optional[Any]:
        """
        Retrieve session context from Redis

        Args:
            session_id: Session identifier
            key: Context key

        Returns:
            Stored value or None if not found
        """
        redis_key = f"session:{session_id}:{key}"

        try:
            data = self.redis.get(redis_key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            print(f"Error retrieving short-term memory [{redis_key}]: {e}")
            return None

    def get_all_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get all context for a session

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of all context key-value pairs
        """
        pattern = f"session:{session_id}:*"

        try:
            keys = self.redis.keys(pattern)
            context = {}

            for redis_key in keys:
                # Extract the context key from redis key
                # Format: session:uuid:context_key -> context_key
                context_key = redis_key.split(":", 2)[-1]
                value = self.redis.get(redis_key)

                if value:
                    try:
                        context[context_key] = json.loads(value)
                    except json.JSONDecodeError:
                        context[context_key] = value

            return context
        except RedisError as e:
            print(f"Error retrieving session context [{session_id}]: {e}")
            return {}

    def delete(self, session_id: str, key: str) -> bool:
        """
        Delete specific context key

        Args:
            session_id: Session identifier
            key: Context key to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        redis_key = f"session:{session_id}:{key}"

        try:
            return bool(self.redis.delete(redis_key))
        except RedisError as e:
            print(f"Error deleting short-term memory [{redis_key}]: {e}")
            return False

    def clear_session(self, session_id: str) -> int:
        """
        Clear all context for a session

        Args:
            session_id: Session identifier

        Returns:
            int: Number of keys deleted
        """
        pattern = f"session:{session_id}:*"

        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except RedisError as e:
            print(f"Error clearing session [{session_id}]: {e}")
            return 0

    def get_ttl(self, session_id: str, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key

        Args:
            session_id: Session identifier
            key: Context key

        Returns:
            Remaining TTL in seconds or None if key doesn't exist
        """
        redis_key = f"session:{session_id}:{key}"

        try:
            ttl = self.redis.ttl(redis_key)
            return ttl if ttl >= 0 else None
        except RedisError as e:
            print(f"Error getting TTL [{redis_key}]: {e}")
            return None

    def extend_ttl(self, session_id: str, key: str, additional_seconds: int) -> bool:
        """
        Extend the TTL of a key

        Args:
            session_id: Session identifier
            key: Context key
            additional_seconds: Seconds to add to current TTL

        Returns:
            bool: Success status
        """
        redis_key = f"session:{session_id}:{key}"

        try:
            current_ttl = self.redis.ttl(redis_key)
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                return bool(self.redis.expire(redis_key, new_ttl))
            return False
        except RedisError as e:
            print(f"Error extending TTL [{redis_key}]: {e}")
            return False

    def list_active_sessions(self) -> List[str]:
        """
        List all active session IDs

        Returns:
            List of unique session IDs
        """
        pattern = "session:*"

        try:
            keys = self.redis.keys(pattern)
            # Extract unique session IDs
            sessions = set()
            for key in keys:
                # Format: session:uuid:context_key -> uuid
                parts = key.split(":")
                if len(parts) >= 2:
                    sessions.add(parts[1])

            return list(sessions)
        except RedisError as e:
            print(f"Error listing sessions: {e}")
            return []
