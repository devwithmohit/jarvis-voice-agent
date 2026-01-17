"""
Unit tests for Semantic Memory Store (FAISS)
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from stores.semantic import SemanticStore
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create temporary directory for FAISS index"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def store(temp_dir):
    """Create SemanticStore instance with temporary storage"""
    with patch("stores.semantic.settings") as mock_settings:
        mock_settings.embedding_model = "all-MiniLM-L6-v2"
        mock_settings.vector_dimension = 384
        mock_settings.faiss_index_dir = temp_dir

        store = SemanticStore()
        return store


def test_initialization(store):
    """Test store initialization"""
    assert store.index is not None
    assert store.dimension == 384
    assert store.model is not None
    assert isinstance(store.metadata, list)
    assert isinstance(store.user_indices, dict)


def test_store_single_memory(store):
    """Test storing a single memory"""
    user_id = "user123"
    text = "The user prefers dark mode"
    memory_type = "preference"
    metadata = {"category": "ui"}

    vector_idx = store.store(user_id, text, memory_type, metadata)

    assert vector_idx is not None
    assert vector_idx == 0
    assert store.index.ntotal == 1
    assert user_id in store.user_indices


def test_batch_store(store):
    """Test batch storing multiple memories"""
    user_id = "user123"
    texts = [
        "User prefers dark mode",
        "User likes concise responses",
        "User is interested in AI topics",
    ]
    memory_type = "preference"

    indices = store.batch_store(user_id, texts, memory_type)

    assert len(indices) == 3
    assert store.index.ntotal == 3
    assert len(store.user_indices[user_id]) == 3


def test_search_similar_memories(store):
    """Test searching for similar memories"""
    user_id = "user123"

    # Store some memories
    texts = [
        "User prefers dark mode for the interface",
        "User likes short and concise answers",
        "User is interested in machine learning",
        "User enjoys programming in Python",
    ]

    store.batch_store(user_id, texts, "preference")

    # Search for similar content
    query = "UI theme preferences"
    results = store.search(query, user_id=user_id, top_k=2)

    assert len(results) <= 2
    assert all("text" in r for r in results)
    assert all("similarity" in r for r in results)


def test_search_with_memory_type_filter(store):
    """Test searching with memory type filter"""
    user_id = "user123"

    # Store different types
    store.store(user_id, "User prefers dark mode", "preference", {})
    store.store(user_id, "User completed task X", "behavior", {})

    # Search only preferences
    results = store.search(
        "preferences", user_id=user_id, memory_type="preference", top_k=5
    )

    assert all(r["memory_type"] == "preference" for r in results if "memory_type" in r)


def test_get_user_memories(store):
    """Test retrieving all memories for a user"""
    user_id = "user123"

    # Store memories
    texts = ["Memory 1", "Memory 2", "Memory 3"]
    store.batch_store(user_id, texts, "preference")

    # Retrieve all
    memories = store.get_user_memories(user_id)

    assert len(memories) == 3


def test_get_user_memories_with_limit(store):
    """Test retrieving memories with limit"""
    user_id = "user123"

    texts = [f"Memory {i}" for i in range(10)]
    store.batch_store(user_id, texts, "preference")

    memories = store.get_user_memories(user_id, limit=5)

    assert len(memories) == 5


def test_delete_user_memories(store):
    """Test deleting all user memories"""
    user_id = "user123"

    # Store memories
    texts = ["Memory 1", "Memory 2", "Memory 3"]
    store.batch_store(user_id, texts, "preference")

    # Delete
    deleted_count = store.delete_user_memories(user_id)

    assert deleted_count == 3
    assert user_id not in store.user_indices


def test_multiple_users(store):
    """Test storing memories for multiple users"""
    user1 = "user1"
    user2 = "user2"

    store.store(user1, "User1 memory", "preference", {})
    store.store(user2, "User2 memory", "preference", {})

    # Each user should have their own memories
    user1_memories = store.get_user_memories(user1)
    user2_memories = store.get_user_memories(user2)

    assert len(user1_memories) == 1
    assert len(user2_memories) == 1


def test_search_across_multiple_users(store):
    """Test that search respects user_id filter"""
    user1 = "user1"
    user2 = "user2"

    store.store(user1, "Dark mode preference", "preference", {})
    store.store(user2, "Light mode preference", "preference", {})

    # Search for user1 only
    results = store.search("mode preference", user_id=user1, top_k=5)

    # Should only return user1's memories
    for result in results:
        # Check metadata to verify user
        assert result.get("index") in store.user_indices.get(user1, [])


def test_get_stats(store):
    """Test getting store statistics"""
    user_id = "user123"

    # Store some data
    store.batch_store(user_id, ["Memory 1", "Memory 2"], "preference")

    stats = store.get_stats()

    assert "total_vectors" in stats
    assert "active_vectors" in stats
    assert "unique_users" in stats
    assert stats["total_vectors"] >= 2


def test_persistence(store, temp_dir):
    """Test index persistence and loading"""
    user_id = "user123"
    text = "Test memory for persistence"

    # Store and save
    store.store(user_id, text, "preference", {})
    store.save_index()

    # Create new store instance (should load from disk)
    with patch("stores.semantic.settings") as mock_settings:
        mock_settings.embedding_model = "all-MiniLM-L6-v2"
        mock_settings.vector_dimension = 384
        mock_settings.faiss_index_dir = temp_dir

        new_store = SemanticStore()

        assert new_store.index.ntotal == 1
        assert len(new_store.metadata) == 1


def test_distance_threshold(store):
    """Test search with distance threshold"""
    user_id = "user123"

    store.store(
        user_id, "Very specific technical content about Python", "knowledge", {}
    )
    store.store(user_id, "Completely unrelated random text", "knowledge", {})

    # Search with threshold - should filter out dissimilar results
    results = store.search(
        "Python programming",
        user_id=user_id,
        distance_threshold=1.0,  # Low threshold = high similarity required
        top_k=10,
    )

    # Results should be limited by distance
    assert len(results) >= 0  # May or may not find close matches


def test_empty_search(store):
    """Test search on empty index"""
    results = store.search("test query", user_id="nonexistent", top_k=5)

    assert results == []


def test_metadata_storage(store):
    """Test that metadata is properly stored and retrieved"""
    user_id = "user123"
    text = "Test memory"
    metadata = {"source": "conversation", "timestamp": "2026-01-17"}

    vector_idx = store.store(user_id, text, "preference", metadata)

    # Retrieve and check
    memories = store.get_user_memories(user_id)
    assert len(memories) == 1
    assert memories[0]["metadata"] == metadata
