"""
Semantic memory store using FAISS
Manages vector embeddings for similarity search
"""

from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from datetime import datetime
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

settings = get_settings()


class SemanticStore:
    """
    Semantic memory backed by FAISS vector index
    Uses sentence-transformers for embedding generation
    """

    def __init__(self):
        # Load embedding model
        self.model = SentenceTransformer(settings.embedding_model)
        self.dimension = settings.vector_dimension

        # Initialize FAISS index (using IVF for large-scale search)
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self.user_indices = {}  # Map user_id -> list of indices

        # Paths for persistence
        self.index_path = os.path.join(settings.faiss_index_dir, "semantic.index")
        self.metadata_path = os.path.join(
            settings.faiss_index_dir, "semantic_metadata.pkl"
        )

        # Create directory if needed
        os.makedirs(settings.faiss_index_dir, exist_ok=True)

        # Load existing index if available
        self._load_index()

    def _load_index(self) -> bool:
        """Load FAISS index and metadata from disk"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                self.index = faiss.read_index(self.index_path)

                with open(self.metadata_path, "rb") as f:
                    data = pickle.load(f)
                    self.metadata = data.get("metadata", [])
                    self.user_indices = data.get("user_indices", {})

                print(f"Loaded FAISS index with {self.index.ntotal} vectors")
                return True
            else:
                # Create new index
                self._create_new_index()
                return False
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            self._create_new_index()
            return False

    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use L2 distance for now (can switch to IP for cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self.user_indices = {}
        print(f"Created new FAISS index with dimension {self.dimension}")

    def save_index(self) -> bool:
        """Persist FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, self.index_path)

            with open(self.metadata_path, "wb") as f:
                pickle.dump(
                    {"metadata": self.metadata, "user_indices": self.user_indices}, f
                )

            return True
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            return False

    def store(
        self,
        user_id: str,
        text: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Store text as vector embedding

        Args:
            user_id: User identifier
            text: Text to embed
            memory_type: Type of memory ('preference', 'behavior', 'conversation', 'knowledge')
            metadata: Optional additional metadata

        Returns:
            Vector index if successful, None otherwise
        """
        try:
            # Generate embedding
            embedding = self.model.encode([text], convert_to_numpy=True)[0]

            # Ensure correct dimension
            if embedding.shape[0] != self.dimension:
                print(
                    f"Embedding dimension mismatch: {embedding.shape[0]} != {self.dimension}"
                )
                return None

            # Add to FAISS index
            embedding = np.array([embedding], dtype="float32")
            self.index.add(embedding)

            # Store metadata
            vector_idx = self.index.ntotal - 1
            meta = {
                "user_id": user_id,
                "text": text,
                "memory_type": memory_type,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
            }
            self.metadata.append(meta)

            # Update user index mapping
            if user_id not in self.user_indices:
                self.user_indices[user_id] = []
            self.user_indices[user_id].append(vector_idx)

            # Persist to disk
            self.save_index()

            return vector_idx
        except Exception as e:
            print(f"Error storing semantic memory [{user_id}]: {e}")
            return None

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        top_k: int = 10,
        distance_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories

        Args:
            query: Query text
            user_id: Optional user filter
            memory_type: Optional memory type filter
            top_k: Number of results to return
            distance_threshold: Optional maximum distance for results

        Returns:
            List of matching memories with similarity scores
        """
        try:
            if self.index.ntotal == 0:
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
            query_embedding = np.array([query_embedding], dtype="float32")

            # Search FAISS index (get more than needed for filtering)
            search_k = min(top_k * 5, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, search_k)

            # Filter and format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # Skip invalid indices
                if idx < 0 or idx >= len(self.metadata):
                    continue

                meta = self.metadata[idx]

                # Apply filters
                if user_id and meta.get("user_id") != user_id:
                    continue

                if memory_type and meta.get("memory_type") != memory_type:
                    continue

                if distance_threshold and dist > distance_threshold:
                    continue

                # Calculate similarity score (convert L2 distance to similarity)
                similarity = 1 / (1 + dist)

                result = {
                    "index": int(idx),
                    "text": meta.get("text"),
                    "memory_type": meta.get("memory_type"),
                    "similarity": float(similarity),
                    "distance": float(dist),
                    "metadata": meta.get("metadata", {}),
                    "created_at": meta.get("created_at"),
                }

                results.append(result)

                # Stop when we have enough results
                if len(results) >= top_k:
                    break

            return results
        except Exception as e:
            print(f"Error searching semantic memory: {e}")
            return []

    def batch_store(
        self,
        user_id: str,
        texts: List[str],
        memory_type: str,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """
        Store multiple texts at once (more efficient)

        Args:
            user_id: User identifier
            texts: List of texts to embed
            memory_type: Type of memory
            metadata_list: Optional list of metadata dicts

        Returns:
            List of vector indices
        """
        try:
            if not texts:
                return []

            # Generate embeddings in batch
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False
            )
            embeddings = np.array(embeddings, dtype="float32")

            # Add to FAISS index
            start_idx = self.index.ntotal
            self.index.add(embeddings)

            # Store metadata
            indices = []
            metadata_list = metadata_list or [{}] * len(texts)

            for i, (text, meta_dict) in enumerate(zip(texts, metadata_list)):
                vector_idx = start_idx + i
                meta = {
                    "user_id": user_id,
                    "text": text,
                    "memory_type": memory_type,
                    "metadata": meta_dict or {},
                    "created_at": datetime.now().isoformat(),
                }
                self.metadata.append(meta)

                # Update user index mapping
                if user_id not in self.user_indices:
                    self.user_indices[user_id] = []
                self.user_indices[user_id].append(vector_idx)

                indices.append(vector_idx)

            # Persist to disk
            self.save_index()

            return indices
        except Exception as e:
            print(f"Error batch storing semantic memory [{user_id}]: {e}")
            return []

    def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a user

        Args:
            user_id: User identifier
            memory_type: Optional memory type filter
            limit: Optional limit on results

        Returns:
            List of memory dictionaries
        """
        try:
            if user_id not in self.user_indices:
                return []

            memories = []
            for idx in self.user_indices[user_id]:
                if idx >= len(self.metadata):
                    continue

                meta = self.metadata[idx]

                # Apply filter
                if memory_type and meta.get("memory_type") != memory_type:
                    continue

                memories.append(
                    {
                        "index": idx,
                        "text": meta.get("text"),
                        "memory_type": meta.get("memory_type"),
                        "metadata": meta.get("metadata", {}),
                        "created_at": meta.get("created_at"),
                    }
                )

                # Apply limit
                if limit and len(memories) >= limit:
                    break

            return memories
        except Exception as e:
            print(f"Error retrieving user memories [{user_id}]: {e}")
            return []

    def delete_user_memories(self, user_id: str) -> int:
        """
        Delete all memories for a user
        Note: FAISS doesn't support deletion, so we mark as deleted and rebuild if needed

        Args:
            user_id: User identifier

        Returns:
            Number of memories marked for deletion
        """
        try:
            if user_id not in self.user_indices:
                return 0

            count = 0
            for idx in self.user_indices[user_id]:
                if idx < len(self.metadata):
                    # Mark as deleted
                    self.metadata[idx]["deleted"] = True
                    count += 1

            # Remove from user index
            del self.user_indices[user_id]

            # Persist changes
            self.save_index()

            # Check if we should rebuild index (if too many deletions)
            deleted_count = sum(1 for m in self.metadata if m.get("deleted"))
            if deleted_count > 0.3 * len(self.metadata):  # If >30% deleted
                self._rebuild_index()

            return count
        except Exception as e:
            print(f"Error deleting user memories [{user_id}]: {e}")
            return 0

    def _rebuild_index(self):
        """Rebuild index without deleted entries"""
        try:
            print("Rebuilding FAISS index to remove deleted entries...")

            # Filter out deleted entries
            active_indices = [
                i for i, m in enumerate(self.metadata) if not m.get("deleted")
            ]

            if not active_indices:
                self._create_new_index()
                return

            # Generate embeddings for active entries
            texts = [self.metadata[i]["text"] for i in active_indices]
            embeddings = self.model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False
            )
            embeddings = np.array(embeddings, dtype="float32")

            # Create new index
            new_index = faiss.IndexFlatL2(self.dimension)
            new_index.add(embeddings)

            # Update metadata and mappings
            new_metadata = [self.metadata[i] for i in active_indices]
            new_user_indices = {}

            for new_idx, old_idx in enumerate(active_indices):
                user_id = self.metadata[old_idx]["user_id"]
                if user_id not in new_user_indices:
                    new_user_indices[user_id] = []
                new_user_indices[user_id].append(new_idx)

            # Replace with new structures
            self.index = new_index
            self.metadata = new_metadata
            self.user_indices = new_user_indices

            # Save
            self.save_index()

            print(f"Index rebuilt: {len(new_metadata)} active vectors")
        except Exception as e:
            print(f"Error rebuilding index: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the semantic store"""
        try:
            active_count = sum(1 for m in self.metadata if not m.get("deleted"))
            deleted_count = len(self.metadata) - active_count

            return {
                "total_vectors": self.index.ntotal,
                "active_vectors": active_count,
                "deleted_vectors": deleted_count,
                "unique_users": len(self.user_indices),
                "dimension": self.dimension,
                "model": settings.embedding_model,
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
