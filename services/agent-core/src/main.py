"""
FastAPI Application for Agent Core Service
Provides REST API for testing and integration
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.grpc_server import AgentServicer
from config import get_settings

settings = get_settings()

# Global agent servicer instance
agent_servicer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global agent_servicer

    # Startup
    print("Starting Agent Core service...")
    agent_servicer = AgentServicer()

    # Connect to downstream services (gracefully handle failures)
    try:
        agent_servicer.grpc_clients.connect_all()
        print("Connected to downstream services")
    except Exception as e:
        print(f"Warning: Could not connect to all downstream services: {e}")
        print("Service will continue with limited functionality")

    yield

    # Shutdown
    print("Shutting down Agent Core service...")
    if agent_servicer and agent_servicer.grpc_clients:
        agent_servicer.grpc_clients.close_all()


# Create FastAPI app
app = FastAPI(
    title="Agent Core API",
    description="Voice AI Agent - Reasoning Engine and Orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ProcessRequestModel(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    user_input: str = Field(..., description="User's input text")
    metadata: Optional[Dict[str, str]] = Field(
        default=None, description="Optional metadata"
    )


class ProcessResponseModel(BaseModel):
    success: bool
    response: str
    error: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    action_results: Optional[List[Dict[str, Any]]] = None
    needs_confirmation: bool = False


class ClassifyIntentModel(BaseModel):
    user_input: str = Field(..., description="User input to classify")
    context: Optional[Dict[str, str]] = Field(
        default=None, description="Optional context"
    )


class IntentResponseModel(BaseModel):
    intent_type: str
    confidence: float
    entities: Dict[str, str]
    reasoning: str
    required_llm_fallback: bool


class CreatePlanModel(BaseModel):
    user_input: str = Field(..., description="User request")
    intent_type: str = Field(..., description="Intent type")
    context: Optional[Dict[str, str]] = Field(
        default=None, description="Optional context"
    )


class PlanResponseModel(BaseModel):
    success: bool
    plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConfirmActionModel(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    confirmed: bool = Field(..., description="Whether user confirmed")


class ConfirmResponseModel(BaseModel):
    success: bool
    response: str
    action_results: List[Dict[str, Any]]


# Health Check Endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "agent-core", "version": "1.0.0"}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    components = {
        "intent_classifier": "healthy",
        "planner": "healthy",
        "tool_router": "healthy",
        "conversation_manager": "healthy",
        "response_synthesizer": "healthy",
    }

    # Check gRPC clients
    grpc_status = "disconnected"
    if agent_servicer and agent_servicer.grpc_clients:
        grpc_status = (
            "connected"
            if agent_servicer.grpc_clients.is_connected()
            else "disconnected"
        )

    components["grpc_clients"] = grpc_status

    return {
        "status": "healthy",
        "service": "agent-core",
        "components": components,
        "config": {
            "llm_model": settings.llm_model,
            "grpc_port": settings.grpc_port,
            "rest_port": settings.rest_port,
        },
    }


# Main API Endpoints
@app.post("/api/v1/process", response_model=ProcessResponseModel)
async def process_request(request: ProcessRequestModel):
    """
    Process user request end-to-end

    This endpoint handles the complete flow:
    1. Intent classification
    2. Plan creation
    3. Security validation
    4. Action execution (if confirmed)
    5. Response synthesis
    """
    try:
        # Convert to proto-like request
        proto_request = type(
            "Request",
            (),
            {
                "session_id": request.session_id,
                "user_id": request.user_id,
                "user_input": request.user_input,
                "metadata": request.metadata or {},
            },
        )()

        # Process through gRPC servicer
        response = agent_servicer.ProcessRequest(proto_request, None)

        return ProcessResponseModel(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/intent/classify", response_model=IntentResponseModel)
async def classify_intent(request: ClassifyIntentModel):
    """
    Classify user intent

    Uses hybrid rule-based and LLM classification to determine user's intent
    """
    try:
        proto_request = type(
            "Request",
            (),
            {"user_input": request.user_input, "context": request.context or {}},
        )()

        response = agent_servicer.ClassifyIntent(proto_request, None)

        return IntentResponseModel(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/plan/create", response_model=PlanResponseModel)
async def create_plan(request: CreatePlanModel):
    """
    Create execution plan

    Generates a sequence of tool actions to fulfill the user's request
    """
    try:
        proto_request = type(
            "Request",
            (),
            {
                "user_input": request.user_input,
                "intent_type": request.intent_type,
                "context": request.context or {},
            },
        )()

        response = agent_servicer.CreatePlan(proto_request, None)

        return PlanResponseModel(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/action/confirm", response_model=ConfirmResponseModel)
async def confirm_action(request: ConfirmActionModel):
    """
    Confirm or decline pending action

    Executes pending actions if confirmed, or cancels them if declined
    """
    try:
        proto_request = type(
            "Request",
            (),
            {
                "session_id": request.session_id,
                "user_id": request.user_id,
                "confirmed": request.confirmed,
            },
        )()

        response = agent_servicer.ConfirmAction(proto_request, None)

        return ConfirmResponseModel(**response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversation/{session_id}")
async def get_conversation(session_id: str):
    """
    Get conversation history

    Retrieves conversation state and message history for a session
    """
    try:
        proto_request = type("Request", (), {"session_id": session_id})()

        response = agent_servicer.GetConversation(proto_request, None)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/conversation/{session_id}")
async def end_conversation(session_id: str):
    """
    End conversation and clean up

    Removes conversation state from memory
    """
    try:
        agent_servicer.conversation_manager.end_conversation(session_id)
        return {"success": True, "message": f"Conversation {session_id} ended"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Test/Debug Endpoints
@app.get("/api/v1/tools")
async def list_tools():
    """List available tools and their configurations"""
    try:
        tools = agent_servicer.tool_router.tool_configs
        return {
            "tools": [
                {
                    "name": name,
                    "description": config.get("description"),
                    "confirmation_level": config.get("confirmation_level"),
                    "rate_limit": config.get("rate_limit"),
                    "enabled": config.get("enabled", True),
                }
                for name, config in tools.items()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config")
async def get_config():
    """Get service configuration (excluding secrets)"""
    return {
        "llm": {
            "provider": "OpenRouter"
            if "openrouter" in settings.llm_base_url.lower()
            else "Other",
            "model": settings.llm_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        },
        "ports": {
            "grpc": settings.grpc_port,
            "rest": settings.rest_port,
        },
        "services": {
            "memory": f"{settings.memory_service_host}:{settings.memory_service_port}",
            "tool_executor": f"{settings.tool_executor_host}:{settings.tool_executor_port}",
            "web": f"{settings.web_service_host}:{settings.web_service_port}",
        },
        "features": {
            "rate_limiting": True,
            "confirmation_required": True,
            "multi_turn_conversations": True,
        },
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.rest_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
