"""
Unit tests for Short-term Memory Store (Redis)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from stores.short_term import ShortTermStore
from unittest.mock import Mock, MagicMock
import json


@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    redis_mock = Mock()
    redis_mock.setex = Mock(return_value=True)
    redis_mock.get = Mock(return_value=None)
    redis_mock.keys = Mock(return_value=[])
    redis_mock.delete = Mock(return_value=1)
    redis_mock.ttl = Mock(return_value=3600)
    redis_mock.expire = Mock(return_value=True)
    return redis_mock


@pytest.fixture
def store(mock_redis):
    """Create ShortTermStore instance with mock Redis"""
    return ShortTermStore(mock_redis)


def test_store_success(store, mock_redis):
    """Test successful storage of session context"""
    session_id = "test_session"
    key = "user_name"
    value = "John Doe"

    result = store.store(session_id, key, value)

    assert result is True
    mock_redis.setex.assert_called_once()

    # Check the key format
    call_args = mock_redis.setex.call_args[0]
    assert call_args[0] == f"session:{session_id}:{key}"
    assert call_args[1] == store.default_ttl
    assert json.loads(call_args[2]) == value


def test_store_with_custom_ttl(store, mock_redis):
    """Test storage with custom TTL"""
    session_id = "test_session"
    key = "temp_data"
    value = {"data": "temporary"}
    custom_ttl = 300

    result = store.store(session_id, key, value, ttl=custom_ttl)

    assert result is True
    call_args = mock_redis.setex.call_args[0]
    assert call_args[1] == custom_ttl


def test_retrieve_existing_key(store, mock_redis):
    """Test retrieval of existing key"""
    session_id = "test_session"
    key = "user_name"
    expected_value = "John Doe"

    mock_redis.get.return_value = json.dumps(expected_value)

    result = store.retrieve(session_id, key)

    assert result == expected_value
    mock_redis.get.assert_called_once_with(f"session:{session_id}:{key}")


def test_retrieve_non_existing_key(store, mock_redis):
    """Test retrieval of non-existing key"""
    session_id = "test_session"
    key = "non_existing"

    mock_redis.get.return_value = None

    result = store.retrieve(session_id, key)

    assert result is None


def test_get_all_context(store, mock_redis):
    """Test retrieval of all session context"""
    session_id = "test_session"

    # Mock keys and values
    mock_keys = [
        f"session:{session_id}:name",
        f"session:{session_id}:age",
        f"session:{session_id}:city",
    ]
    mock_redis.keys.return_value = mock_keys

    # Mock get to return values
    def mock_get(key):
        if "name" in key:
            return json.dumps("John")
        elif "age" in key:
            return json.dumps(30)
        elif "city" in key:
            return json.dumps("New York")
        return None

    mock_redis.get.side_effect = mock_get

    result = store.get_all_context(session_id)

    assert result == {"name": "John", "age": 30, "city": "New York"}


def test_delete_key(store, mock_redis):
    """Test deletion of specific key"""
    session_id = "test_session"
    key = "temp_data"

    mock_redis.delete.return_value = 1

    result = store.delete(session_id, key)

    assert result is True
    mock_redis.delete.assert_called_once_with(f"session:{session_id}:{key}")


def test_clear_session(store, mock_redis):
    """Test clearing all session data"""
    session_id = "test_session"

    mock_keys = [
        f"session:{session_id}:key1",
        f"session:{session_id}:key2",
        f"session:{session_id}:key3",
    ]
    mock_redis.keys.return_value = mock_keys
    mock_redis.delete.return_value = 3

    result = store.clear_session(session_id)

    assert result == 3
    mock_redis.delete.assert_called_once()


def test_get_ttl(store, mock_redis):
    """Test getting TTL for a key"""
    session_id = "test_session"
    key = "user_data"

    mock_redis.ttl.return_value = 3600

    result = store.get_ttl(session_id, key)

    assert result == 3600
    mock_redis.ttl.assert_called_once_with(f"session:{session_id}:{key}")


def test_extend_ttl(store, mock_redis):
    """Test extending TTL for a key"""
    session_id = "test_session"
    key = "user_data"
    seconds = 7200

    mock_redis.expire.return_value = True

    result = store.extend_ttl(session_id, key, seconds)

    assert result is True
    mock_redis.expire.assert_called_once()


def test_list_active_sessions(store, mock_redis):
    """Test listing active sessions"""
    mock_keys = [
        "session:user1:data",
        "session:user1:name",
        "session:user2:data",
        "session:user3:name",
    ]
    mock_redis.keys.return_value = mock_keys

    result = store.list_active_sessions()

    assert set(result) == {"user1", "user2", "user3"}


def test_store_complex_object(store, mock_redis):
    """Test storing complex nested objects"""
    session_id = "test_session"
    key = "complex_data"
    value = {
        "user": {"name": "John", "preferences": ["dark_mode", "notifications"]},
        "metadata": {"version": "1.0", "timestamp": "2026-01-17"},
    }

    result = store.store(session_id, key, value)

    assert result is True
    call_args = mock_redis.setex.call_args[0]
    assert json.loads(call_args[2]) == value


def test_store_error_handling(store, mock_redis):
    """Test error handling during storage"""
    session_id = "test_session"
    key = "data"
    value = "test"

    # Simulate Redis error
    mock_redis.setex.side_effect = Exception("Redis connection error")

    result = store.store(session_id, key, value)

    assert result is False


def test_retrieve_error_handling(store, mock_redis):
    """Test error handling during retrieval"""
    session_id = "test_session"
    key = "data"

    # Simulate Redis error
    mock_redis.get.side_effect = Exception("Redis connection error")

    result = store.retrieve(session_id, key)

    assert result is None
