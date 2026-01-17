"""
gRPC Server for Agent Core Service
Implements AgentService with intent classification, planning, and orchestration
"""

import grpc
from concurrent import futures
from typing import Dict, Any
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline.intent_classifier import IntentClassifier
from src.pipeline.planner import Planner
from src.pipeline.tool_router import ToolRouter
from src.pipeline.conversation_manager import ConversationManager
from src.pipeline.response_synthesizer import ResponseSynthesizer
from src.models.intent import Intent, IntentType
from src.models.tool_action import (
    AgentPlan,
    ToolAction,
    ToolActionResult,
    ToolName,
    ConfirmationLevel,
)
from src.utils.grpc_clients import GrpcClientManager
from config import get_settings

settings = get_settings()


class AgentServicer:
    """
    gRPC service implementation for Agent Core
    Orchestrates intent classification, planning, and execution
    """

    def __init__(self):
        """Initialize agent servicer"""
        # Initialize pipeline components
        self.intent_classifier = IntentClassifier()
        self.available_tools = [tool.value for tool in ToolName]
        self.planner = Planner(available_tools=self.available_tools)
        self.tool_router = ToolRouter()
        self.conversation_manager = ConversationManager()
        self.response_synthesizer = ResponseSynthesizer()

        # Initialize gRPC clients for downstream services
        self.grpc_clients = GrpcClientManager()

        print("AgentServicer initialized successfully")

    def ProcessRequest(self, request, context):
        """
        Process user request end-to-end

        Args:
            request: ProcessRequestRequest
            context: gRPC context

        Returns:
            ProcessRequestResponse
        """
        try:
            session_id = request.session_id
            user_id = request.user_id
            user_input = request.user_input

            print(f"Processing request from user {user_id}: {user_input}")

            # Add user message to conversation
            self.conversation_manager.add_user_message(
                session_id=session_id,
                user_id=user_id,
                content=user_input,
                metadata=dict(request.metadata) if request.metadata else None,
            )

            # Check for pending confirmation
            pending_plan = self.conversation_manager.get_pending_confirmation(
                session_id
            )
            if pending_plan:
                # Handle confirmation response
                return self._handle_confirmation_response(
                    session_id, user_id, user_input, pending_plan, context
                )

            # Get conversation context
            conv_context = self.conversation_manager.get_context(session_id, user_id)
            context_dict = {
                "conversation_summary": self.conversation_manager.get_conversation_summary(
                    session_id
                ),
                "user_preferences": conv_context.user_preferences,
                "current_task": conv_context.current_task,
            }

            # Classify intent
            intent_result = self.intent_classifier.classify(user_input, context_dict)
            print(
                f"Intent classified as: {intent_result.intent.type.value} (confidence: {intent_result.intent.confidence:.2f})"
            )

            # Handle clarification needed
            if intent_result.intent.type == IntentType.CLARIFICATION:
                response_text = self.response_synthesizer.generate_clarification_prompt(
                    user_input,
                    intent_result.intent.reasoning or "I need more information",
                )
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, response_text
                )
                return self._create_response(success=True, response=response_text)

            # Handle conversation (greetings, thanks, etc.)
            if intent_result.intent.type == IntentType.CONVERSATION:
                response_text = self._handle_conversation(user_input)
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, response_text
                )
                return self._create_response(success=True, response=response_text)

            # Create execution plan
            plan = self.planner.create_plan(
                user_input=user_input,
                intent=intent_result.intent,
                context=context_dict,
            )

            if not plan.actions:
                response_text = "I understand your request, but I'm not sure how to proceed. Could you provide more details?"
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, response_text
                )
                return self._create_response(success=True, response=response_text)

            print(
                f"Plan created with {len(plan.actions)} actions (confidence: {plan.confidence:.2f})"
            )

            # Validate actions
            validation_errors = []
            for action in plan.actions:
                is_valid, error = self.tool_router.validate_action(action, user_id)
                if not is_valid:
                    validation_errors.append(f"{action.tool_name.value}: {error}")

            if validation_errors:
                error_msg = "Some actions failed validation:\n" + "\n".join(
                    validation_errors
                )
                print(f"Validation errors: {error_msg}")
                response_text = self.response_synthesizer.generate_error_response(
                    error_msg, user_input
                )
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, response_text
                )
                return self._create_response(
                    success=False, response=response_text, error=error_msg
                )

            # Check if confirmation needed
            if plan.needs_user_confirmation or plan.has_destructive_actions():
                confirmation_prompt = (
                    self.response_synthesizer.generate_confirmation_prompt(plan)
                )
                self.conversation_manager.set_pending_confirmation(
                    session_id, user_id, plan
                )
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, confirmation_prompt, plan=plan
                )
                return self._create_response(
                    success=True,
                    response=confirmation_prompt,
                    plan=plan,
                    needs_confirmation=True,
                )

            # Execute plan
            action_results = self._execute_plan(plan, user_id)

            # Synthesize response
            response_text = self.response_synthesizer.synthesize(
                user_input=user_input,
                plan=plan,
                results=action_results,
            )

            # Add to conversation
            self.conversation_manager.add_assistant_message(
                session_id, user_id, response_text, plan=plan
            )

            return self._create_response(
                success=True,
                response=response_text,
                plan=plan,
                action_results=action_results,
            )

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)
            return self._create_response(
                success=False,
                response="I encountered an error processing your request.",
                error=error_msg,
            )

    def ClassifyIntent(self, request, context):
        """
        Classify user intent

        Args:
            request: ClassifyIntentRequest
            context: gRPC context

        Returns:
            ClassifyIntentResponse
        """
        try:
            user_input = request.user_input
            context_dict = dict(request.context) if request.context else {}

            result = self.intent_classifier.classify(user_input, context_dict)

            # Create response (placeholder - replace with actual proto message)
            return {
                "intent_type": result.intent.type.value,
                "confidence": result.intent.confidence,
                "entities": result.intent.entities,
                "reasoning": result.intent.reasoning or "",
                "required_llm_fallback": result.required_llm_fallback,
            }

        except Exception as e:
            print(f"Error classifying intent: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    def CreatePlan(self, request, context):
        """
        Create execution plan

        Args:
            request: CreatePlanRequest
            context: gRPC context

        Returns:
            CreatePlanResponse
        """
        try:
            user_input = request.user_input
            intent_type_str = request.intent_type
            context_dict = dict(request.context) if request.context else {}

            # Create intent from type
            try:
                intent_type = IntentType(intent_type_str)
            except ValueError:
                intent_type = IntentType.UNKNOWN

            intent = Intent(type=intent_type, confidence=0.8)

            # Create plan
            plan = self.planner.create_plan(
                user_input=user_input,
                intent=intent,
                context=context_dict,
            )

            return {
                "success": True,
                "plan": self._plan_to_dict(plan),
                "error": "",
            }

        except Exception as e:
            print(f"Error creating plan: {e}")
            return {
                "success": False,
                "plan": None,
                "error": str(e),
            }

    def ValidateAction(self, request, context):
        """
        Validate tool action

        Args:
            request: ValidateActionRequest
            context: gRPC context

        Returns:
            ValidateActionResponse
        """
        try:
            user_id = request.user_id
            action_proto = request.action

            # Convert proto to ToolAction
            action = ToolAction(
                tool_name=ToolName(action_proto.tool_name),
                parameters=dict(action_proto.parameters),
                reasoning=action_proto.reasoning,
                confirmation_level=ConfirmationLevel(action_proto.confirmation_level),
            )

            # Validate
            is_valid, error = self.tool_router.validate_action(action, user_id)

            return {
                "is_valid": is_valid,
                "error_message": error or "",
            }

        except Exception as e:
            print(f"Error validating action: {e}")
            return {
                "is_valid": False,
                "error_message": str(e),
            }

    def ConfirmAction(self, request, context):
        """
        Confirm pending action

        Args:
            request: ConfirmActionRequest
            context: gRPC context

        Returns:
            ConfirmActionResponse
        """
        try:
            session_id = request.session_id
            user_id = request.user_id
            confirmed = request.confirmed

            # Get pending plan
            pending_plan = self.conversation_manager.get_pending_confirmation(
                session_id
            )

            if not pending_plan:
                return {
                    "success": False,
                    "response": "No pending actions to confirm.",
                    "action_results": [],
                }

            if not confirmed:
                # User declined
                self.conversation_manager.clear_pending_confirmation(session_id)
                response_text = "Understood. I've cancelled the pending actions. Is there anything else I can help you with?"
                self.conversation_manager.add_assistant_message(
                    session_id, user_id, response_text
                )
                return {
                    "success": True,
                    "response": response_text,
                    "action_results": [],
                }

            # User confirmed - execute plan
            self.conversation_manager.clear_pending_confirmation(session_id)
            action_results = self._execute_plan(pending_plan, user_id)

            # Synthesize response
            response_text = self.response_synthesizer.synthesize(
                user_input="[Confirmed action]",
                plan=pending_plan,
                results=action_results,
            )

            self.conversation_manager.add_assistant_message(
                session_id, user_id, response_text, plan=pending_plan
            )

            return {
                "success": True,
                "response": response_text,
                "action_results": [
                    self._action_result_to_dict(r) for r in action_results
                ],
            }

        except Exception as e:
            print(f"Error confirming action: {e}")
            return {
                "success": False,
                "response": "Error processing confirmation.",
                "action_results": [],
            }

    def GetConversation(self, request, context):
        """
        Get conversation context

        Args:
            request: GetConversationRequest
            context: gRPC context

        Returns:
            GetConversationResponse
        """
        try:
            session_id = request.session_id

            if session_id not in self.conversation_manager.conversations:
                return {
                    "session_id": session_id,
                    "user_id": "",
                    "messages": [],
                    "user_preferences": {},
                    "current_task": "",
                }

            conversation = self.conversation_manager.conversations[session_id]

            return {
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata,
                    }
                    for msg in conversation.messages
                ],
                "user_preferences": conversation.user_preferences,
                "current_task": conversation.current_task or "",
            }

        except Exception as e:
            print(f"Error getting conversation: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return None

    def _handle_confirmation_response(
        self,
        session_id: str,
        user_id: str,
        user_input: str,
        pending_plan: AgentPlan,
        context,
    ):
        """Handle user response to confirmation prompt"""
        user_input_lower = user_input.lower().strip()

        # Check for affirmative response
        affirmative = ["yes", "y", "ok", "sure", "proceed", "go ahead", "confirm"]
        negative = ["no", "n", "cancel", "stop", "abort"]

        if any(word in user_input_lower for word in affirmative):
            # Confirmed - use ConfirmAction logic
            return self.ConfirmAction(
                type(
                    "Request",
                    (),
                    {"session_id": session_id, "user_id": user_id, "confirmed": True},
                )(),
                context,
            )
        elif any(word in user_input_lower for word in negative):
            # Declined
            return self.ConfirmAction(
                type(
                    "Request",
                    (),
                    {"session_id": session_id, "user_id": user_id, "confirmed": False},
                )(),
                context,
            )
        else:
            # Ambiguous response
            response_text = "I'm not sure if you want to proceed. Please respond with 'yes' to confirm or 'no' to cancel."
            return self._create_response(success=True, response=response_text)

    def _handle_conversation(self, user_input: str) -> str:
        """Handle conversational intents (greetings, thanks, etc.)"""
        user_input_lower = user_input.lower().strip()

        if any(
            greeting in user_input_lower
            for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]
        ):
            return "Hello! I'm your AI assistant. How can I help you today?"
        elif any(
            thanks in user_input_lower for thanks in ["thank", "thanks", "appreciate"]
        ):
            return "You're welcome! Is there anything else I can help you with?"
        elif any(bye in user_input_lower for bye in ["bye", "goodbye", "see you"]):
            return "Goodbye! Feel free to reach out anytime you need assistance."
        else:
            return "I'm here to help. What would you like me to do?"

    def _execute_plan(self, plan: AgentPlan, user_id: str) -> list:
        """Execute plan actions"""
        results = []

        for action in plan.actions:
            try:
                # Route action to appropriate service
                service_name = self.tool_router.route_action(action)

                # Execute based on service
                if service_name == "web-service":
                    result = self._execute_web_action(action)
                elif service_name == "tool-executor":
                    result = self._execute_tool_action(action)
                else:
                    result = ToolActionResult(
                        tool_name=action.tool_name,
                        success=False,
                        error=f"Unknown service: {service_name}",
                    )

                results.append(result)

            except Exception as e:
                print(f"Error executing action {action.tool_name.value}: {e}")
                results.append(
                    ToolActionResult(
                        tool_name=action.tool_name,
                        success=False,
                        error=str(e),
                    )
                )

        return results

    def _execute_web_action(self, action: ToolAction) -> ToolActionResult:
        """Execute web-related action"""
        try:
            if action.tool_name == ToolName.WEB_SEARCH:
                result = self.grpc_clients.web_client.web_search(
                    query=action.parameters.get("query", ""),
                    max_results=action.parameters.get("max_results", 5),
                )
            elif action.tool_name == ToolName.WEB_FETCH:
                result = self.grpc_clients.web_client.web_fetch(
                    url=action.parameters.get("url", ""),
                    extract_type=action.parameters.get("extract_type", "text"),
                )
            else:
                # Browser actions
                result = self.grpc_clients.web_client.browser_action(
                    action=action.tool_name.value,
                    parameters=action.parameters,
                )

            return ToolActionResult(
                tool_name=action.tool_name,
                success=result.get("success", False),
                result=result.get("result")
                or result.get("content")
                or result.get("results"),
                error=result.get("error"),
            )

        except Exception as e:
            return ToolActionResult(
                tool_name=action.tool_name,
                success=False,
                error=str(e),
            )

    def _execute_tool_action(self, action: ToolAction) -> ToolActionResult:
        """Execute file/system action"""
        try:
            result = self.grpc_clients.tool_executor_client.execute_tool(
                tool_name=action.tool_name.value,
                parameters=action.parameters,
            )

            return ToolActionResult(
                tool_name=action.tool_name,
                success=result.get("success", False),
                result=result.get("result"),
                error=result.get("error"),
            )

        except Exception as e:
            return ToolActionResult(
                tool_name=action.tool_name,
                success=False,
                error=str(e),
            )

    def _create_response(
        self,
        success: bool,
        response: str,
        error: str = "",
        plan: AgentPlan = None,
        action_results: list = None,
        needs_confirmation: bool = False,
    ):
        """Create ProcessRequestResponse (placeholder - replace with actual proto)"""
        return {
            "success": success,
            "response": response,
            "error": error,
            "plan": self._plan_to_dict(plan) if plan else None,
            "action_results": [
                self._action_result_to_dict(r) for r in (action_results or [])
            ],
            "needs_confirmation": needs_confirmation,
        }

    def _plan_to_dict(self, plan: AgentPlan) -> Dict:
        """Convert AgentPlan to dictionary"""
        if not plan:
            return None
        return {
            "actions": [
                {
                    "tool_name": action.tool_name.value,
                    "parameters": action.parameters,
                    "reasoning": action.reasoning,
                    "confirmation_level": action.confirmation_level.value,
                }
                for action in plan.actions
            ],
            "thought_process": plan.thought_process,
            "expected_outcome": plan.expected_outcome,
            "confidence": plan.confidence,
            "needs_confirmation": plan.needs_user_confirmation,
        }

    def _action_result_to_dict(self, result: ToolActionResult) -> Dict:
        """Convert ToolActionResult to dictionary"""
        return {
            "tool_name": result.tool_name.value,
            "success": result.success,
            "result": result.result,
            "error": result.error,
        }


def serve():
    """Start gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add servicer (placeholder - replace with actual proto-generated method)
    # agent_pb2_grpc.add_AgentServiceServicer_to_server(AgentServicer(), server)

    servicer = AgentServicer()

    # For now, just print that server would start
    port = settings.grpc_port
    server.add_insecure_port(f"[::]:{port}")

    server.start()
    print(f"Agent Core gRPC server started on port {port}")
    print("Available services:")
    print("  - ProcessRequest: End-to-end request processing")
    print("  - ClassifyIntent: Intent classification")
    print("  - CreatePlan: Execution planning")
    print("  - ValidateAction: Action validation")
    print("  - ConfirmAction: Confirmation handling")
    print("  - GetConversation: Conversation retrieval")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gRPC server...")
        server.stop(0)


if __name__ == "__main__":
    serve()
