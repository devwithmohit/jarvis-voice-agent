"""
Episodic memory store using PostgreSQL
Manages event history and weekly summaries
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import text
from datetime import datetime, timedelta
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db import get_db
from config import get_settings

settings = get_settings()


class EpisodicStore:
    """
    Episodic memory backed by PostgreSQL
    Stores event history with automatic summarization and retention
    """

    def store_event(
        self,
        user_id: str,
        event_type: str,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None,
    ) -> Optional[int]:
        """
        Store an episodic event

        Args:
            user_id: User identifier
            event_type: Type of event ('command', 'task', 'conversation', 'correction')
            summary: Brief summary of the event
            details: Optional detailed information dictionary
            occurred_at: When the event occurred (default: now)

        Returns:
            Event ID if successful, None otherwise
        """
        with get_db() as db:
            try:
                query = text("""
                    INSERT INTO episodic_events
                    (user_id, event_type, summary, details, occurred_at)
                    VALUES (:user_id, :event_type, :summary, :details::jsonb, :occurred_at)
                    RETURNING id
                """)

                result = db.execute(
                    query,
                    {
                        "user_id": user_id,
                        "event_type": event_type,
                        "summary": summary,
                        "details": json.dumps(details or {}),
                        "occurred_at": occurred_at or datetime.now(),
                    },
                )

                event_id = result.fetchone()[0]
                return event_id
            except Exception as e:
                print(f"Error storing episodic event [{user_id}/{event_type}]: {e}")
                return None

    def get_events(
        self,
        user_id: str,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve episodic events with optional filters

        Args:
            user_id: User identifier
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        with get_db() as db:
            try:
                # Build query dynamically based on filters
                query_parts = [
                    """
                    SELECT id, event_type, summary, details, occurred_at, created_at
                    FROM episodic_events
                    WHERE user_id = :user_id
                """
                ]

                params = {"user_id": user_id}

                if event_type:
                    query_parts.append("AND event_type = :event_type")
                    params["event_type"] = event_type

                if start_time:
                    query_parts.append("AND occurred_at >= :start_time")
                    params["start_time"] = start_time

                if end_time:
                    query_parts.append("AND occurred_at <= :end_time")
                    params["end_time"] = end_time

                query_parts.append("ORDER BY occurred_at DESC LIMIT :limit")
                params["limit"] = min(limit, settings.max_episodic_events_per_query)

                query = text(" ".join(query_parts))
                result = db.execute(query, params)

                events = []
                for row in result:
                    event = dict(row._mapping)
                    # Parse JSONB details
                    if event.get("details"):
                        try:
                            event["details"] = (
                                json.loads(event["details"])
                                if isinstance(event["details"], str)
                                else event["details"]
                            )
                        except json.JSONDecodeError:
                            event["details"] = {}
                    events.append(event)

                return events
            except Exception as e:
                print(f"Error retrieving events [{user_id}]: {e}")
                return []

    def get_recent_events(
        self, user_id: str, days: int = 7, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events from the last N days

        Args:
            user_id: User identifier
            days: Number of days to look back
            event_type: Optional event type filter

        Returns:
            List of recent events
        """
        start_time = datetime.now() - timedelta(days=days)
        return self.get_events(
            user_id=user_id, event_type=event_type, start_time=start_time
        )

    def generate_weekly_summary(
        self, user_id: str, week_start: Optional[datetime] = None
    ) -> Optional[int]:
        """
        Generate a weekly summary from events
        Uses PostgreSQL function for consistency

        Args:
            user_id: User identifier
            week_start: Start of the week (default: last Monday)

        Returns:
            Summary ID if successful, None otherwise
        """
        with get_db() as db:
            try:
                # Default to last Monday if not specified
                if week_start is None:
                    today = datetime.now().date()
                    days_since_monday = today.weekday()
                    week_start = today - timedelta(days=days_since_monday)
                elif isinstance(week_start, datetime):
                    week_start = week_start.date()

                # Call PostgreSQL function
                query = text("""
                    SELECT generate_weekly_summary(:user_id, :week_start::date)
                """)

                db.execute(query, {"user_id": user_id, "week_start": week_start})

                # Get the summary that was just created/updated
                summary_query = text("""
                    SELECT id FROM episodic_summaries
                    WHERE user_id = :user_id AND week_start = :week_start
                """)

                result = db.execute(
                    summary_query, {"user_id": user_id, "week_start": week_start}
                ).fetchone()

                return result[0] if result else None
            except Exception as e:
                print(f"Error generating weekly summary [{user_id}]: {e}")
                return None

    def get_summary(
        self, user_id: str, week_start: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific weekly summary

        Args:
            user_id: User identifier
            week_start: Start date of the week

        Returns:
            Summary dictionary or None
        """
        with get_db() as db:
            try:
                query = text("""
                    SELECT id, week_start, summary, event_count, metadata, created_at
                    FROM episodic_summaries
                    WHERE user_id = :user_id AND week_start = :week_start
                """)

                result = db.execute(
                    query,
                    {
                        "user_id": user_id,
                        "week_start": week_start.date()
                        if isinstance(week_start, datetime)
                        else week_start,
                    },
                ).fetchone()

                if result:
                    summary = dict(result._mapping)
                    # Parse metadata if exists
                    if summary.get("metadata"):
                        try:
                            summary["metadata"] = (
                                json.loads(summary["metadata"])
                                if isinstance(summary["metadata"], str)
                                else summary["metadata"]
                            )
                        except json.JSONDecodeError:
                            summary["metadata"] = {}
                    return summary
                return None
            except Exception as e:
                print(f"Error retrieving summary [{user_id}/{week_start}]: {e}")
                return None

    def get_all_summaries(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all weekly summaries for a user

        Args:
            user_id: User identifier

        Returns:
            List of summary dictionaries ordered by week
        """
        with get_db() as db:
            try:
                query = text("""
                    SELECT id, week_start, summary, event_count, metadata, created_at
                    FROM episodic_summaries
                    WHERE user_id = :user_id
                    ORDER BY week_start DESC
                """)

                result = db.execute(query, {"user_id": user_id})

                summaries = []
                for row in result:
                    summary = dict(row._mapping)
                    if summary.get("metadata"):
                        try:
                            summary["metadata"] = (
                                json.loads(summary["metadata"])
                                if isinstance(summary["metadata"], str)
                                else summary["metadata"]
                            )
                        except json.JSONDecodeError:
                            summary["metadata"] = {}
                    summaries.append(summary)

                return summaries
            except Exception as e:
                print(f"Error retrieving summaries [{user_id}]: {e}")
                return []

    def delete_old_events(self, user_id: str, days: Optional[int] = None) -> int:
        """
        Delete events older than specified days (default from config)

        Args:
            user_id: User identifier
            days: Days to retain (default from settings)

        Returns:
            Number of events deleted
        """
        with get_db() as db:
            try:
                days = days or settings.episodic_retention_days
                cutoff_date = datetime.now() - timedelta(days=days)

                query = text("""
                    DELETE FROM episodic_events
                    WHERE user_id = :user_id AND occurred_at < :cutoff_date
                """)

                result = db.execute(
                    query, {"user_id": user_id, "cutoff_date": cutoff_date}
                )

                return result.rowcount
            except Exception as e:
                print(f"Error deleting old events [{user_id}]: {e}")
                return 0

    def clear_all_events(self, user_id: str) -> int:
        """Clear all episodic events for a user"""
        with get_db() as db:
            try:
                query = text("DELETE FROM episodic_events WHERE user_id = :user_id")
                result = db.execute(query, {"user_id": user_id})
                return result.rowcount
            except Exception as e:
                print(f"Error clearing events [{user_id}]: {e}")
                return 0

    def clear_all_summaries(self, user_id: str) -> int:
        """Clear all episodic summaries for a user"""
        with get_db() as db:
            try:
                query = text("DELETE FROM episodic_summaries WHERE user_id = :user_id")
                result = db.execute(query, {"user_id": user_id})
                return result.rowcount
            except Exception as e:
                print(f"Error clearing summaries [{user_id}]: {e}")
                return 0

    def get_event_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's episodic memory

        Returns:
            Dictionary with event counts by type and time ranges
        """
        with get_db() as db:
            try:
                query = text("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT event_type) as event_types,
                        MIN(occurred_at) as first_event,
                        MAX(occurred_at) as last_event,
                        COUNT(CASE WHEN occurred_at >= NOW() - INTERVAL '7 days' THEN 1 END) as last_week,
                        COUNT(CASE WHEN occurred_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_month
                    FROM episodic_events
                    WHERE user_id = :user_id
                """)

                result = db.execute(query, {"user_id": user_id}).fetchone()

                if result:
                    return dict(result._mapping)
                return {}
            except Exception as e:
                print(f"Error retrieving event stats [{user_id}]: {e}")
                return {}
