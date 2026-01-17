"""
Conversation Manager - Multi-turn conversation state management
Tracks conversation history, pending confirmations, and context
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.models.conversation import ConversationState, ConversationContext, Message
from src.models.tool_action import AgentPlan
from config import get_settings

settings = get_settings()


class ConversationManager:
    """
    Manages conversation state and context
    Tracks multi-turn conversations and pending confirmations
    """

    def __init__(self):
        """Initialize conversation manager"""
        self.conversations: Dict[str, ConversationState] = {}
        self.conversation_timeout = timedelta(
            minutes=30
        )  # Timeout after 30 min inactivity

    def get_or_create_conversation(
        self, session_id: str, user_id: str
    ) -> ConversationState:
        """
        Get existing conversation or create new one

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            ConversationState
        """
        # Clean up expired conversations
        self._cleanup_expired_conversations()

        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationState(
                session_id=session_id,
                user_id=user_id,
            )

        return self.conversations[session_id]

    def add_user_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        """
        Add user message to conversation

        Args:
            session_id: Session identifier
            user_id: User identifier
            content: Message content
            metadata: Optional metadata

        Returns:
            Updated ConversationState
        """
        conversation = self.get_or_create_conversation(session_id, user_id)

        message = Message(
            role="user",
            content=content,
            metadata=metadata or {},
        )

        conversation.add_message(message)
        return conversation

    def add_assistant_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        plan: Optional[AgentPlan] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationState:
        """
        Add assistant message to conversation

        Args:
            session_id: Session identifier
            user_id: User identifier
            content: Message content
            plan: Optional execution plan
            metadata: Optional metadata

        Returns:
            Updated ConversationState
        """
        conversation = self.get_or_create_conversation(session_id, user_id)

        message_metadata = metadata or {}
        if plan:
            message_metadata["plan"] = {
                "actions": [
                    {
                        "tool": action.tool_name.value,
                        "parameters": action.parameters,
                        "reasoning": action.reasoning,
                    }
                    for action in plan.actions
                ],
                "confidence": plan.confidence,
            }

        message = Message(
            role="assistant",
            content=content,
            metadata=message_metadata,
        )

        conversation.add_message(message)
        return conversation

    def set_pending_confirmation(
        self, session_id: str, user_id: str, plan: AgentPlan
    ) -> ConversationState:
        """
        Set pending confirmation for plan

        Args:
            session_id: Session identifier
            user_id: User identifier
            plan: Plan requiring confirmation

        Returns:
            Updated ConversationState
        """
        conversation = self.get_or_create_conversation(session_id, user_id)
        conversation.pending_confirmation = {
            "plan": plan.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        return conversation

    def get_pending_confirmation(self, session_id: str) -> Optional[AgentPlan]:
        """
        Get pending confirmation plan

        Args:
            session_id: Session identifier

        Returns:
            AgentPlan if pending, None otherwise
        """
        if session_id not in self.conversations:
            return None

        conversation = self.conversations[session_id]
        if not conversation.pending_confirmation:
            return None

        # Check if confirmation expired (5 minutes)
        try:
            timestamp = datetime.fromisoformat(
                conversation.pending_confirmation["timestamp"]
            )
            if datetime.utcnow() - timestamp > timedelta(minutes=5):
                # Expired
                conversation.clear_pending_confirmations()
                return None

            plan_data = conversation.pending_confirmation["plan"]
            return AgentPlan(**plan_data)
        except Exception as e:
            print(f"Error retrieving pending confirmation: {e}")
            return None

    def clear_pending_confirmation(self, session_id: str) -> None:
        """
        Clear pending confirmation

        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            self.conversations[session_id].clear_pending_confirmations()

    def get_context(self, session_id: str, user_id: str) -> ConversationContext:
        """
        Get conversation context for processing

        Args:
            session_id: Session identifier
            user_id: User identifier

        Returns:
            ConversationContext
        """
        conversation = self.get_or_create_conversation(session_id, user_id)

        # Get recent context (last 10 messages)
        recent_context = conversation.get_recent_context(max_messages=10)

        # Build context
        return ConversationContext(
            session_id=session_id,
            user_id=user_id,
            conversation_history=recent_context,
            user_preferences=conversation.user_preferences,
            current_task=conversation.current_task,
        )

    def update_user_preferences(
        self, session_id: str, preferences: Dict[str, Any]
    ) -> None:
        """
        Update user preferences

        Args:
            session_id: Session identifier
            preferences: Preferences to update
        """
        if session_id in self.conversations:
            self.conversations[session_id].user_preferences.update(preferences)

    def set_current_task(self, session_id: str, task: Optional[str]) -> None:
        """
        Set current task

        Args:
            session_id: Session identifier
            task: Task description or None to clear
        """
        if session_id in self.conversations:
            self.conversations[session_id].current_task = task

    def get_conversation_summary(self, session_id: str) -> str:
        """
        Get conversation summary

        Args:
            session_id: Session identifier

        Returns:
            Summary string
        """
        if session_id not in self.conversations:
            return "No conversation history"

        conversation = self.conversations[session_id]
        return conversation.get_conversation_summary()

    def end_conversation(self, session_id: str) -> None:
        """
        End conversation and clean up

        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]

    def _cleanup_expired_conversations(self) -> None:
        """Clean up expired conversations"""
        expired = []

        for session_id, conversation in self.conversations.items():
            if conversation.is_expired(self.conversation_timeout):
                expired.append(session_id)

        for session_id in expired:
            del self.conversations[session_id]
            print(f"Cleaned up expired conversation: {session_id}")
