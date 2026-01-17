"""
Pydantic models for Memory Service API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


# Short-term Memory Models
class StoreShortTermRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    key: str = Field(..., description="Context key")
    value: Any = Field(..., description="Context value")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")


class RetrieveContextRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    key: Optional[str] = Field(None, description="Specific key to retrieve")


class ContextResponse(BaseModel):
    session_id: str
    context: Dict[str, Any]


# Long-term Memory Models
class StorePreferenceRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    category: str = Field(..., description="Preference category")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")


class GetPreferencesRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    category: Optional[str] = Field(None, description="Optional category filter")


class PreferenceResponse(BaseModel):
    category: str
    key: str
    value: Any
    updated_at: datetime


class RecordBehaviorRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    behavior_type: str = Field(..., description="Type of behavior")
    pattern: str = Field(..., description="Behavior pattern")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    confidence: float = Field(0.5, description="Initial confidence score")


class GetBehaviorsRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    behavior_type: Optional[str] = Field(
        None, description="Optional behavior type filter"
    )
    min_confidence: float = Field(0.5, description="Minimum confidence threshold")


class BehaviorResponse(BaseModel):
    behavior_type: str
    pattern: str
    metadata: Dict[str, Any]
    confidence: float
    occurrence_count: int


# Episodic Memory Models
class StoreEventRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    event_type: str = Field(..., description="Event type")
    summary: str = Field(..., description="Event summary")
    details: Optional[Dict[str, Any]] = Field(None, description="Event details")
    occurred_at: Optional[datetime] = Field(None, description="When event occurred")


class GetEventsRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    event_type: Optional[str] = Field(None, description="Optional event type filter")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    limit: int = Field(100, description="Maximum events to return")


class EventResponse(BaseModel):
    id: int
    event_type: str
    summary: str
    details: Dict[str, Any]
    occurred_at: datetime
    created_at: datetime


class GenerateSummaryRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    week_start: Optional[datetime] = Field(None, description="Week start date")


class SummaryResponse(BaseModel):
    id: int
    week_start: datetime
    summary: str
    event_count: int
    metadata: Dict[str, Any]
    created_at: datetime


# Semantic Memory Models
class AddSemanticRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    text: str = Field(..., description="Text to embed and store")
    memory_type: str = Field(..., description="Type of memory")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchSemanticRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    query: str = Field(..., description="Search query")
    memory_type: Optional[str] = Field(None, description="Optional memory type filter")
    top_k: int = Field(10, description="Number of results")
    distance_threshold: Optional[float] = Field(None, description="Maximum distance")


class SemanticResult(BaseModel):
    index: int
    text: str
    memory_type: str
    similarity: float
    distance: float
    metadata: Dict[str, Any]
    created_at: str


class SearchSemanticResponse(BaseModel):
    results: List[SemanticResult]


# User Data Management Models
class ExportUserDataRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")


class ExportUserDataResponse(BaseModel):
    user_id: str
    preferences: List[PreferenceResponse]
    behaviors: List[BehaviorResponse]
    recent_events: List[EventResponse]
    summaries: List[SummaryResponse]
    semantic_memories: List[SemanticResult]
    export_time: datetime


class DeleteUserDataRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    confirm: bool = Field(..., description="Confirmation flag")


class DeleteUserDataResponse(BaseModel):
    user_id: str
    deleted: bool
    items_deleted: Dict[str, int]


# General Response Models
class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    components: Dict[str, str]
