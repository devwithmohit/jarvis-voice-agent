"""
gRPC Server Implementation for Memory Service
Implements all RPCs defined in memory.proto
"""

import grpc
from concurrent import futures
import sys
import os
from typing import Dict, Any
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import generated protobuf code (will be generated from proto files)
# from generated import memory_pb2, memory_pb2_grpc

from stores.short_term import ShortTermStore
from stores.long_term import LongTermStore
from stores.episodic import EpisodicStore
from stores.semantic import SemanticStore
from utils.cache import redis_client
from config import get_settings

settings = get_settings()


class MemoryServiceServicer:
    """
    Implementation of MemoryService gRPC service
    Manages all four memory stores: short-term, long-term, episodic, semantic
    """

    def __init__(self):
        """Initialize all memory stores"""
        self.short_term = ShortTermStore(redis_client)
        self.long_term = LongTermStore()
        self.episodic = EpisodicStore()
        self.semantic = SemanticStore()
        print(f"✓ Memory stores initialized")

    # Short-term Memory RPCs

    def StoreShortTerm(self, request, context):
        """Store session context in Redis with TTL"""
        try:
            success = self.short_term.store(
                session_id=request.session_id,
                key=request.key,
                value=request.value,
                ttl=request.ttl_seconds if request.ttl_seconds > 0 else None,
            )

            return {
                "success": success,
                "message": "Stored successfully" if success else "Storage failed",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error storing short-term memory: {str(e)}")
            return {"success": False, "message": str(e)}

    def RetrieveContext(self, request, context):
        """Retrieve all session context from Redis"""
        try:
            if request.key:
                # Retrieve specific key
                value = self.short_term.retrieve(request.session_id, request.key)
                context_data = {request.key: value} if value is not None else {}
            else:
                # Retrieve all context
                context_data = self.short_term.get_all_context(request.session_id)

            return {
                "session_id": request.session_id,
                "context": json.dumps(context_data),
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error retrieving context: {str(e)}")
            return {"session_id": request.session_id, "context": "{}"}

    def ClearSession(self, request, context):
        """Clear all context for a session"""
        try:
            deleted_count = self.short_term.clear_session(request.session_id)
            return {"success": True, "message": f"Cleared {deleted_count} items"}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error clearing session: {str(e)}")
            return {"success": False, "message": str(e)}

    # Long-term Memory RPCs

    def StoreLongTerm(self, request, context):
        """Store user preference or record behavior"""
        try:
            if hasattr(request, "category"):
                # Store preference
                success = self.long_term.store_preference(
                    user_id=request.user_id,
                    category=request.category,
                    key=request.key,
                    value=request.value,
                )
            else:
                # Record behavior
                success = self.long_term.record_behavior(
                    user_id=request.user_id,
                    behavior_type=request.behavior_type,
                    pattern=request.pattern,
                    metadata=json.loads(request.metadata) if request.metadata else None,
                    confidence=request.confidence,
                )

            return {
                "success": success,
                "message": "Stored successfully" if success else "Storage failed",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error storing long-term memory: {str(e)}")
            return {"success": False, "message": str(e)}

    def GetPreferences(self, request, context):
        """Retrieve user preferences"""
        try:
            preferences = self.long_term.get_preferences(
                user_id=request.user_id,
                category=request.category if request.category else None,
            )

            return {"preferences": json.dumps(preferences)}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error retrieving preferences: {str(e)}")
            return {"preferences": "[]"}

    def GetBehaviors(self, request, context):
        """Retrieve learned behaviors"""
        try:
            behaviors = self.long_term.get_behaviors(
                user_id=request.user_id,
                behavior_type=request.behavior_type if request.behavior_type else None,
                min_confidence=request.min_confidence
                if request.min_confidence > 0
                else 0.5,
            )

            return {"behaviors": json.dumps(behaviors)}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error retrieving behaviors: {str(e)}")
            return {"behaviors": "[]"}

    # Episodic Memory RPCs

    def StoreEpisode(self, request, context):
        """Store episodic event"""
        try:
            event_id = self.episodic.store_event(
                user_id=request.user_id,
                event_type=request.event_type,
                summary=request.summary,
                details=json.loads(request.details) if request.details else None,
                occurred_at=request.occurred_at if request.occurred_at else None,
            )

            return {
                "success": event_id is not None,
                "event_id": event_id or 0,
                "message": "Event stored" if event_id else "Storage failed",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error storing episode: {str(e)}")
            return {"success": False, "event_id": 0, "message": str(e)}

    def GetEpisodes(self, request, context):
        """Retrieve episodic events"""
        try:
            events = self.episodic.get_events(
                user_id=request.user_id,
                event_type=request.event_type if request.event_type else None,
                start_time=request.start_time if request.start_time else None,
                end_time=request.end_time if request.end_time else None,
                limit=request.limit if request.limit > 0 else 100,
            )

            return {"events": json.dumps(events, default=str)}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error retrieving episodes: {str(e)}")
            return {"events": "[]"}

    def GenerateWeeklySummary(self, request, context):
        """Generate weekly summary from events"""
        try:
            summary_id = self.episodic.generate_weekly_summary(
                user_id=request.user_id,
                week_start=request.week_start if request.week_start else None,
            )

            return {
                "success": summary_id is not None,
                "summary_id": summary_id or 0,
                "message": "Summary generated" if summary_id else "Generation failed",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error generating summary: {str(e)}")
            return {"success": False, "summary_id": 0, "message": str(e)}

    # Semantic Memory RPCs

    def SearchSemantic(self, request, context):
        """Search semantic memory using vector similarity"""
        try:
            results = self.semantic.search(
                query=request.query,
                user_id=request.user_id if request.user_id else None,
                memory_type=request.memory_type if request.memory_type else None,
                top_k=request.top_k if request.top_k > 0 else 10,
                distance_threshold=request.distance_threshold
                if request.distance_threshold > 0
                else None,
            )

            return {"results": json.dumps(results, default=str)}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error searching semantic memory: {str(e)}")
            return {"results": "[]"}

    def AddSemantic(self, request, context):
        """Add text to semantic memory with embeddings"""
        try:
            vector_idx = self.semantic.store(
                user_id=request.user_id,
                text=request.text,
                memory_type=request.memory_type,
                metadata=json.loads(request.metadata) if request.metadata else None,
            )

            return {
                "success": vector_idx is not None,
                "vector_id": vector_idx or 0,
                "message": "Added to semantic memory"
                if vector_idx
                else "Storage failed",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error adding semantic memory: {str(e)}")
            return {"success": False, "vector_id": 0, "message": str(e)}

    # User Data Management RPCs

    def ExportUserData(self, request, context):
        """Export all user data across all stores"""
        try:
            data = {
                "user_id": request.user_id,
                "preferences": self.long_term.get_preferences(request.user_id),
                "behaviors": self.long_term.get_behaviors(request.user_id),
                "recent_events": self.episodic.get_recent_events(
                    request.user_id, days=30
                ),
                "summaries": self.episodic.get_all_summaries(request.user_id),
                "semantic_memories": self.semantic.get_user_memories(
                    request.user_id, limit=100
                ),
            }

            return {"success": True, "data": json.dumps(data, default=str)}
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error exporting user data: {str(e)}")
            return {"success": False, "data": "{}"}

    def DeleteUserData(self, request, context):
        """Delete all user data across all stores"""
        try:
            if not request.confirm:
                return {"success": False, "message": "Deletion not confirmed"}

            # Delete from all stores
            deleted_counts = {
                "preferences": self.long_term.clear_all_preferences(request.user_id),
                "behaviors": self.long_term.clear_all_behaviors(request.user_id),
                "events": self.episodic.clear_all_events(request.user_id),
                "summaries": self.episodic.clear_all_summaries(request.user_id),
                "semantic": self.semantic.delete_user_memories(request.user_id),
            }

            return {
                "success": True,
                "message": f"Deleted user data: {json.dumps(deleted_counts)}",
            }
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting user data: {str(e)}")
            return {"success": False, "message": str(e)}


def serve():
    """Start the gRPC server"""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=settings.grpc_max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
        ],
    )

    # Add servicer to server
    # Note: This requires generated protobuf code
    # memory_pb2_grpc.add_MemoryServiceServicer_to_server(
    #     MemoryServiceServicer(), server
    # )

    # For now, we'll initialize the servicer to test the stores
    servicer = MemoryServiceServicer()

    server.add_insecure_port(f"[::]:{settings.grpc_port}")
    server.start()

    print(f"✓ Memory gRPC server started on port {settings.grpc_port}")
    print(f"✓ Max workers: {settings.grpc_max_workers}")
    print(f"✓ All memory stores operational")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n✓ Shutting down gRPC server...")
        server.stop(0)


if __name__ == "__main__":
    serve()
