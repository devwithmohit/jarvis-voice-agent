"""
Memory REST API Routes
Provides HTTP endpoints for memory operations
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    StoreShortTermRequest,
    RetrieveContextRequest,
    ContextResponse,
    StorePreferenceRequest,
    GetPreferencesRequest,
    RecordBehaviorRequest,
    GetBehaviorsRequest,
    StoreEventRequest,
    GetEventsRequest,
    GenerateSummaryRequest,
    AddSemanticRequest,
    SearchSemanticRequest,
    SearchSemanticResponse,
    SuccessResponse,
    PreferenceResponse,
    BehaviorResponse,
    EventResponse,
    SummaryResponse,
)
from stores.short_term import ShortTermStore
from stores.long_term import LongTermStore
from stores.episodic import EpisodicStore
from stores.semantic import SemanticStore
from utils.cache import redis_client

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

# Initialize stores
short_term_store = ShortTermStore(redis_client)
long_term_store = LongTermStore()
episodic_store = EpisodicStore()
semantic_store = SemanticStore()


# Short-term Memory Endpoints


@router.post("/short-term/store", response_model=SuccessResponse)
async def store_short_term(request: StoreShortTermRequest):
    """Store session context in Redis with TTL"""
    success = short_term_store.store(
        session_id=request.session_id,
        key=request.key,
        value=request.value,
        ttl=request.ttl_seconds,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store short-term memory",
        )

    return SuccessResponse(success=True, message="Context stored successfully")


@router.post("/short-term/retrieve", response_model=ContextResponse)
async def retrieve_context(request: RetrieveContextRequest):
    """Retrieve session context from Redis"""
    if request.key:
        value = short_term_store.retrieve(request.session_id, request.key)
        context = {request.key: value} if value is not None else {}
    else:
        context = short_term_store.get_all_context(request.session_id)

    return ContextResponse(session_id=request.session_id, context=context)


@router.delete("/short-term/session/{session_id}", response_model=SuccessResponse)
async def clear_session(session_id: str):
    """Clear all context for a session"""
    deleted_count = short_term_store.clear_session(session_id)
    return SuccessResponse(success=True, message=f"Cleared {deleted_count} items")


# Long-term Memory Endpoints


@router.post("/long-term/preference", response_model=SuccessResponse)
async def store_preference(request: StorePreferenceRequest):
    """Store or update user preference"""
    success = long_term_store.store_preference(
        user_id=request.user_id,
        category=request.category,
        key=request.key,
        value=request.value,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store preference",
        )

    return SuccessResponse(success=True, message="Preference stored successfully")


@router.post("/long-term/preferences", response_model=list[PreferenceResponse])
async def get_preferences(request: GetPreferencesRequest):
    """Retrieve user preferences"""
    preferences = long_term_store.get_preferences(
        user_id=request.user_id, category=request.category
    )
    return preferences


@router.post("/long-term/behavior", response_model=SuccessResponse)
async def record_behavior(request: RecordBehaviorRequest):
    """Record learned behavior pattern"""
    success = long_term_store.record_behavior(
        user_id=request.user_id,
        behavior_type=request.behavior_type,
        pattern=request.pattern,
        metadata=request.metadata,
        confidence=request.confidence,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record behavior",
        )

    return SuccessResponse(success=True, message="Behavior recorded successfully")


@router.post("/long-term/behaviors", response_model=list[BehaviorResponse])
async def get_behaviors(request: GetBehaviorsRequest):
    """Retrieve learned behaviors"""
    behaviors = long_term_store.get_behaviors(
        user_id=request.user_id,
        behavior_type=request.behavior_type,
        min_confidence=request.min_confidence,
    )
    return behaviors


# Episodic Memory Endpoints


@router.post("/episodic/event", response_model=SuccessResponse)
async def store_event(request: StoreEventRequest):
    """Store episodic event"""
    event_id = episodic_store.store_event(
        user_id=request.user_id,
        event_type=request.event_type,
        summary=request.summary,
        details=request.details,
        occurred_at=request.occurred_at,
    )

    if event_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store event",
        )

    return SuccessResponse(success=True, message=f"Event stored with ID {event_id}")


@router.post("/episodic/events", response_model=list[EventResponse])
async def get_events(request: GetEventsRequest):
    """Retrieve episodic events"""
    events = episodic_store.get_events(
        user_id=request.user_id,
        event_type=request.event_type,
        start_time=request.start_time,
        end_time=request.end_time,
        limit=request.limit,
    )
    return events


@router.get("/episodic/recent/{user_id}", response_model=list[EventResponse])
async def get_recent_events(user_id: str, days: int = 7, event_type: str = None):
    """Get recent events for a user"""
    events = episodic_store.get_recent_events(
        user_id=user_id, days=days, event_type=event_type
    )
    return events


@router.post("/episodic/summary", response_model=SuccessResponse)
async def generate_summary(request: GenerateSummaryRequest):
    """Generate weekly summary from events"""
    summary_id = episodic_store.generate_weekly_summary(
        user_id=request.user_id, week_start=request.week_start
    )

    if summary_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary",
        )

    return SuccessResponse(
        success=True, message=f"Summary generated with ID {summary_id}"
    )


@router.get("/episodic/summaries/{user_id}", response_model=list[SummaryResponse])
async def get_summaries(user_id: str):
    """Get all weekly summaries for a user"""
    summaries = episodic_store.get_all_summaries(user_id)
    return summaries


# Semantic Memory Endpoints


@router.post("/semantic/add", response_model=SuccessResponse)
async def add_semantic(request: AddSemanticRequest):
    """Add text to semantic memory with embeddings"""
    vector_idx = semantic_store.store(
        user_id=request.user_id,
        text=request.text,
        memory_type=request.memory_type,
        metadata=request.metadata,
    )

    if vector_idx is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add semantic memory",
        )

    return SuccessResponse(
        success=True, message=f"Added to semantic memory at index {vector_idx}"
    )


@router.post("/semantic/search", response_model=SearchSemanticResponse)
async def search_semantic(request: SearchSemanticRequest):
    """Search semantic memory using vector similarity"""
    results = semantic_store.search(
        query=request.query,
        user_id=request.user_id,
        memory_type=request.memory_type,
        top_k=request.top_k,
        distance_threshold=request.distance_threshold,
    )

    return SearchSemanticResponse(results=results)


@router.get("/semantic/user/{user_id}", response_model=SearchSemanticResponse)
async def get_user_semantic_memories(
    user_id: str, memory_type: str = None, limit: int = 100
):
    """Get all semantic memories for a user"""
    memories = semantic_store.get_user_memories(
        user_id=user_id, memory_type=memory_type, limit=limit
    )
    return SearchSemanticResponse(results=memories)


# Statistics Endpoints


@router.get("/stats/episodic/{user_id}")
async def get_episodic_stats(user_id: str):
    """Get episodic memory statistics"""
    stats = episodic_store.get_event_stats(user_id)
    return stats


@router.get("/stats/semantic")
async def get_semantic_stats():
    """Get semantic store statistics"""
    stats = semantic_store.get_stats()
    return stats
