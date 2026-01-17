"""
Admin and User Control REST API Routes
Provides endpoints for user data transparency and control
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ExportUserDataRequest,
    ExportUserDataResponse,
    DeleteUserDataRequest,
    DeleteUserDataResponse,
    SuccessResponse,
)
from stores.short_term import ShortTermStore
from stores.long_term import LongTermStore
from stores.episodic import EpisodicStore
from stores.semantic import SemanticStore
from utils.cache import redis_client

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Initialize stores
short_term_store = ShortTermStore(redis_client)
long_term_store = LongTermStore()
episodic_store = EpisodicStore()
semantic_store = SemanticStore()


@router.post("/export", response_model=ExportUserDataResponse)
async def export_user_data(request: ExportUserDataRequest):
    """
    Export all user data across all memory stores
    Provides full transparency of what the system knows about the user
    """
    try:
        # Gather data from all stores
        preferences = long_term_store.get_preferences(request.user_id)
        behaviors = long_term_store.get_behaviors(request.user_id, min_confidence=0.0)
        recent_events = episodic_store.get_recent_events(request.user_id, days=90)
        summaries = episodic_store.get_all_summaries(request.user_id)
        semantic_memories = semantic_store.get_user_memories(request.user_id)

        return ExportUserDataResponse(
            user_id=request.user_id,
            preferences=preferences,
            behaviors=behaviors,
            recent_events=recent_events,
            summaries=summaries,
            semantic_memories=semantic_memories,
            export_time=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user data: {str(e)}",
        )


@router.post("/delete", response_model=DeleteUserDataResponse)
async def delete_user_data(request: DeleteUserDataRequest):
    """
    Delete all user data across all memory stores
    Provides user control over their data (GDPR compliance)
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion must be confirmed with confirm=true",
        )

    try:
        # Delete from all stores
        items_deleted = {
            "preferences": long_term_store.clear_all_preferences(request.user_id),
            "behaviors": long_term_store.clear_all_behaviors(request.user_id),
            "events": episodic_store.clear_all_events(request.user_id),
            "summaries": episodic_store.clear_all_summaries(request.user_id),
            "semantic_memories": semantic_store.delete_user_memories(request.user_id),
        }

        return DeleteUserDataResponse(
            user_id=request.user_id, deleted=True, items_deleted=items_deleted
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user data: {str(e)}",
        )


@router.get("/summary/{user_id}")
async def get_user_summary(user_id: str):
    """
    Get a summary of what the system knows about a user
    Quick overview without full data export
    """
    try:
        episodic_stats = episodic_store.get_event_stats(user_id)
        semantic_stats = semantic_store.get_stats()

        preferences_count = len(long_term_store.get_preferences(user_id))
        behaviors_count = len(
            long_term_store.get_behaviors(user_id, min_confidence=0.0)
        )

        return {
            "user_id": user_id,
            "preferences_count": preferences_count,
            "behaviors_count": behaviors_count,
            "episodic_stats": episodic_stats,
            "semantic_store_stats": semantic_stats,
            "generated_at": datetime.now(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate user summary: {str(e)}",
        )


@router.post("/cleanup/episodic/{user_id}", response_model=SuccessResponse)
async def cleanup_old_events(user_id: str, days: int = None):
    """
    Clean up old episodic events beyond retention period
    Optional: specify custom retention period
    """
    try:
        deleted_count = episodic_store.delete_old_events(user_id, days)
        return SuccessResponse(
            success=True, message=f"Deleted {deleted_count} old events"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup events: {str(e)}",
        )


@router.get("/active-sessions")
async def get_active_sessions():
    """
    Get list of active sessions in short-term memory
    Useful for monitoring and debugging
    """
    try:
        sessions = short_term_store.list_active_sessions()
        return {
            "active_sessions": sessions,
            "count": len(sessions),
            "timestamp": datetime.now(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active sessions: {str(e)}",
        )


@router.get("/health-check")
async def health_check():
    """
    Check health of all memory stores
    """
    health = {"status": "healthy", "timestamp": datetime.now(), "components": {}}

    try:
        # Test Redis connection
        redis_client.ping()
        health["components"]["redis"] = "healthy"
    except Exception as e:
        health["components"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    try:
        # Test database connection
        from utils.db import test_connection

        test_connection()
        health["components"]["postgresql"] = "healthy"
    except Exception as e:
        health["components"]["postgresql"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    try:
        # Test FAISS index
        stats = semantic_store.get_stats()
        health["components"]["faiss"] = (
            f"healthy ({stats.get('total_vectors', 0)} vectors)"
        )
    except Exception as e:
        health["components"]["faiss"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    return health
