"""
Redis cache client for short-term memory
Provides connection management and basic operations
"""

import redis
from redis.exceptions import RedisError, ConnectionError
from typing import Optional
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

settings = get_settings()

# Create Redis client with connection pooling
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    socket_keepalive=True,
    health_check_interval=30,
    retry_on_timeout=True,
    max_connections=50,
)


def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    return redis_client


def test_connection() -> bool:
    """Test Redis connection"""
    try:
        redis_client.ping()
        return True
    except (RedisError, ConnectionError) as e:
        print(f"Redis connection failed: {e}")
        return False


def get_info() -> Optional[dict]:
    """Get Redis server information"""
    try:
        return redis_client.info()
    except RedisError as e:
        print(f"Failed to get Redis info: {e}")
        return None


def flush_all_sessions() -> bool:
    """Flush all session data (use with caution!)"""
    try:
        # Only delete keys matching session pattern
        pattern = "session:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except RedisError as e:
        print(f"Failed to flush sessions: {e}")
        return False


if __name__ == "__main__":
    # Test connection when run directly
    if test_connection():
        print("✓ Redis connection successful")
        info = get_info()
        if info:
            print(f"  Redis version: {info.get('redis_version')}")
            print(f"  Connected clients: {info.get('connected_clients')}")
            print(f"  Used memory: {info.get('used_memory_human')}")
    else:
        print("✗ Redis connection failed")
