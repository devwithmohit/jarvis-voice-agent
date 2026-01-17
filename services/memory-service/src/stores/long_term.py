"""
Long-term memory store using PostgreSQL
Manages user preferences and learned behaviors
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import text
from datetime import datetime
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_db


class LongTermStore:
    """
    Long-term memory backed by PostgreSQL
    Stores user preferences and learned behavioral patterns
    """

    def store_preference(
        self, user_id: str, category: str, key: str, value: Any
    ) -> bool:
        """
        Store or update user preference

        Args:
            user_id: User identifier
            category: Preference category ('voice', 'privacy', 'behavior', 'ui')
            key: Preference key
            value: Preference value (will be JSON-serialized)

        Returns:
            bool: Success status
        """
        with get_db() as db:
            try:
                # Serialize value to JSONB
                if not isinstance(value, str):
                    json_value = json.dumps(value)
                else:
                    json_value = value

                query = text("""
                    INSERT INTO user_preferences (user_id, category, key, value, updated_at)
                    VALUES (:user_id, :category, :key, :value::jsonb, NOW())
                    ON CONFLICT (user_id, category, key)
                    DO UPDATE SET value = :value::jsonb, updated_at = NOW()
                """)

                db.execute(
                    query,
                    {
                        "user_id": user_id,
                        "category": category,
                        "key": key,
                        "value": json_value,
                    },
                )
                return True
            except Exception as e:
                print(f"Error storing preference [{user_id}/{category}/{key}]: {e}")
                return False

    def get_preferences(
        self, user_id: str, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user preferences

        Args:
            user_id: User identifier
            category: Optional category filter

        Returns:
            List of preference dictionaries
        """
        with get_db() as db:
            try:
                if category:
                    query = text("""
                        SELECT id, category, key, value, updated_at, created_at
                        FROM user_preferences
                        WHERE user_id = :user_id AND category = :category
                        ORDER BY category, key
                    """)
                    params = {"user_id": user_id, "category": category}
                else:
                    query = text("""
                        SELECT id, category, key, value, updated_at, created_at
                        FROM user_preferences
                        WHERE user_id = :user_id
                        ORDER BY category, key
                    """)
                    params = {"user_id": user_id}

                result = db.execute(query, params)

                preferences = []
                for row in result:
                    pref = dict(row._mapping)
                    # Parse JSONB value
                    if pref.get("value"):
                        try:
                            pref["value"] = (
                                json.loads(pref["value"])
                                if isinstance(pref["value"], str)
                                else pref["value"]
                            )
                        except json.JSONDecodeError:
                            pass
                    preferences.append(pref)

                return preferences
            except Exception as e:
                print(f"Error retrieving preferences [{user_id}]: {e}")
                return []

    def get_preference(self, user_id: str, category: str, key: str) -> Optional[Any]:
        """
        Get a single preference value

        Args:
            user_id: User identifier
            category: Preference category
            key: Preference key

        Returns:
            Preference value or None
        """
        with get_db() as db:
            try:
                query = text("""
                    SELECT value
                    FROM user_preferences
                    WHERE user_id = :user_id
                    AND category = :category
                    AND key = :key
                """)

                result = db.execute(
                    query, {"user_id": user_id, "category": category, "key": key}
                ).fetchone()

                if result:
                    value = result.value
                    try:
                        return json.loads(value) if isinstance(value, str) else value
                    except json.JSONDecodeError:
                        return value
                return None
            except Exception as e:
                print(f"Error retrieving preference [{user_id}/{category}/{key}]: {e}")
                return None

    def delete_preference(self, user_id: str, category: str, key: str) -> bool:
        """
        Delete a specific preference

        Args:
            user_id: User identifier
            category: Preference category
            key: Preference key

        Returns:
            bool: Success status
        """
        with get_db() as db:
            try:
                query = text("""
                    DELETE FROM user_preferences
                    WHERE user_id = :user_id
                    AND category = :category
                    AND key = :key
                """)

                result = db.execute(
                    query, {"user_id": user_id, "category": category, "key": key}
                )
                return result.rowcount > 0
            except Exception as e:
                print(f"Error deleting preference [{user_id}/{category}/{key}]: {e}")
                return False

    def record_behavior(
        self,
        user_id: str,
        behavior_type: str,
        pattern: str,
        metadata: Optional[Dict] = None,
        confidence: float = 0.5,
    ) -> bool:
        """
        Record or update learned behavior pattern
        Increases confidence with repeated occurrences

        Args:
            user_id: User identifier
            behavior_type: Type of behavior ('command_shortcut', 'tool_preference', 'speech_pattern')
            pattern: The behavior pattern
            metadata: Optional metadata dictionary
            confidence: Initial confidence (0.0-1.0)

        Returns:
            bool: Success status
        """
        with get_db() as db:
            try:
                # Check if pattern exists
                check_query = text("""
                    SELECT id, occurrence_count, confidence
                    FROM learned_behaviors
                    WHERE user_id = :user_id
                    AND behavior_type = :behavior_type
                    AND pattern = :pattern
                """)

                existing = db.execute(
                    check_query,
                    {
                        "user_id": user_id,
                        "behavior_type": behavior_type,
                        "pattern": pattern,
                    },
                ).fetchone()

                if existing:
                    # Update existing behavior
                    new_count = existing.occurrence_count + 1
                    # Increase confidence with more occurrences (max 0.95)
                    new_confidence = min(0.95, existing.confidence + 0.05)

                    update_query = text("""
                        UPDATE learned_behaviors
                        SET occurrence_count = :count,
                            confidence = :confidence,
                            last_seen = NOW(),
                            metadata = :metadata::jsonb
                        WHERE id = :id
                    """)

                    db.execute(
                        update_query,
                        {
                            "id": existing.id,
                            "count": new_count,
                            "confidence": new_confidence,
                            "metadata": json.dumps(metadata or {}),
                        },
                    )
                else:
                    # Insert new behavior
                    insert_query = text("""
                        INSERT INTO learned_behaviors
                        (user_id, behavior_type, pattern, metadata, confidence, occurrence_count)
                        VALUES (:user_id, :behavior_type, :pattern, :metadata::jsonb, :confidence, 1)
                    """)

                    db.execute(
                        insert_query,
                        {
                            "user_id": user_id,
                            "behavior_type": behavior_type,
                            "pattern": pattern,
                            "metadata": json.dumps(metadata or {}),
                            "confidence": max(0.0, min(1.0, confidence)),
                        },
                    )

                return True
            except Exception as e:
                print(f"Error recording behavior [{user_id}/{behavior_type}]: {e}")
                return False

    def get_behaviors(
        self,
        user_id: str,
        behavior_type: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve learned behaviors above confidence threshold

        Args:
            user_id: User identifier
            behavior_type: Optional behavior type filter
            min_confidence: Minimum confidence threshold

        Returns:
            List of behavior dictionaries sorted by confidence
        """
        with get_db() as db:
            try:
                if behavior_type:
                    query = text("""
                        SELECT id, behavior_type, pattern, metadata,
                               confidence, occurrence_count, last_seen, created_at
                        FROM learned_behaviors
                        WHERE user_id = :user_id
                        AND behavior_type = :behavior_type
                        AND confidence >= :min_confidence
                        ORDER BY confidence DESC, occurrence_count DESC
                    """)
                    params = {
                        "user_id": user_id,
                        "behavior_type": behavior_type,
                        "min_confidence": min_confidence,
                    }
                else:
                    query = text("""
                        SELECT id, behavior_type, pattern, metadata,
                               confidence, occurrence_count, last_seen, created_at
                        FROM learned_behaviors
                        WHERE user_id = :user_id
                        AND confidence >= :min_confidence
                        ORDER BY confidence DESC, occurrence_count DESC
                    """)
                    params = {"user_id": user_id, "min_confidence": min_confidence}

                result = db.execute(query, params)

                behaviors = []
                for row in result:
                    behavior = dict(row._mapping)
                    # Parse JSONB metadata
                    if behavior.get("metadata"):
                        try:
                            behavior["metadata"] = (
                                json.loads(behavior["metadata"])
                                if isinstance(behavior["metadata"], str)
                                else behavior["metadata"]
                            )
                        except json.JSONDecodeError:
                            behavior["metadata"] = {}
                    behaviors.append(behavior)

                return behaviors
            except Exception as e:
                print(f"Error retrieving behaviors [{user_id}]: {e}")
                return []

    def delete_behavior(self, user_id: str, behavior_id: int) -> bool:
        """Delete a specific learned behavior"""
        with get_db() as db:
            try:
                query = text("""
                    DELETE FROM learned_behaviors
                    WHERE user_id = :user_id AND id = :behavior_id
                """)
                result = db.execute(
                    query, {"user_id": user_id, "behavior_id": behavior_id}
                )
                return result.rowcount > 0
            except Exception as e:
                print(f"Error deleting behavior [{behavior_id}]: {e}")
                return False

    def clear_all_preferences(self, user_id: str) -> int:
        """Clear all preferences for a user"""
        with get_db() as db:
            try:
                query = text("DELETE FROM user_preferences WHERE user_id = :user_id")
                result = db.execute(query, {"user_id": user_id})
                return result.rowcount
            except Exception as e:
                print(f"Error clearing preferences [{user_id}]: {e}")
                return 0

    def clear_all_behaviors(self, user_id: str) -> int:
        """Clear all learned behaviors for a user"""
        with get_db() as db:
            try:
                query = text("DELETE FROM learned_behaviors WHERE user_id = :user_id")
                result = db.execute(query, {"user_id": user_id})
                return result.rowcount
            except Exception as e:
                print(f"Error clearing behaviors [{user_id}]: {e}")
                return 0
