"""
Unit tests for Conversation Manager
Tests multi-turn conversation state management
"""

import pytest
from datetime import timedelta
from src.pipeline.conversation_manager import ConversationManager
from src.models.tool_action import AgentPlan, ToolAction, ToolName, ConfirmationLevel


class TestConversationManager:
    """Test suite for ConversationManager"""

    @pytest.fixture
    def manager(self):
        """Create conversation manager instance"""
        return ConversationManager()

    @pytest.fixture
    def session_id(self):
        """Test session ID"""
        return "test_session_123"

    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "test_user_456"

    def test_create_new_conversation(self, manager, session_id, user_id):
        """Test creation of new conversation"""
        conversation = manager.get_or_create_conversation(session_id, user_id)

        assert conversation is not None
        assert conversation.session_id == session_id
        assert conversation.user_id == user_id
        assert len(conversation.messages) == 0

    def test_add_user_message(self, manager, session_id, user_id):
        """Test adding user message"""
        manager.add_user_message(session_id, user_id, "Hello, assistant!")

        conversation = manager.get_or_create_conversation(session_id, user_id)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "user"
        assert conversation.messages[0].content == "Hello, assistant!"

    def test_add_assistant_message(self, manager, session_id, user_id):
        """Test adding assistant message"""
        manager.add_assistant_message(session_id, user_id, "Hello! How can I help?")

        conversation = manager.get_or_create_conversation(session_id, user_id)
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == "assistant"

    def test_conversation_history(self, manager, session_id, user_id):
        """Test conversation history tracking"""
        # Add multiple messages
        manager.add_user_message(session_id, user_id, "Message 1")
        manager.add_assistant_message(session_id, user_id, "Response 1")
        manager.add_user_message(session_id, user_id, "Message 2")
        manager.add_assistant_message(session_id, user_id, "Response 2")

        conversation = manager.get_or_create_conversation(session_id, user_id)
        assert len(conversation.messages) == 4

        # Check order
        assert conversation.messages[0].content == "Message 1"
        assert conversation.messages[1].content == "Response 1"
        assert conversation.messages[2].content == "Message 2"
        assert conversation.messages[3].content == "Response 2"

    def test_set_pending_confirmation(self, manager, session_id, user_id):
        """Test setting pending confirmation"""
        plan = AgentPlan(
            actions=[
                ToolAction(
                    tool_name=ToolName.FILE_WRITE,
                    parameters={"path": "test.txt", "content": "test"},
                    reasoning="Test",
                    confirmation_level=ConfirmationLevel.HARD,
                )
            ],
            thought_process="Test plan",
            expected_outcome="File created",
            confidence=0.9,
            needs_user_confirmation=True,
        )

        manager.set_pending_confirmation(session_id, user_id, plan)

        pending = manager.get_pending_confirmation(session_id)
        assert pending is not None
        assert len(pending.actions) == 1
        assert pending.actions[0].tool_name == ToolName.FILE_WRITE

    def test_clear_pending_confirmation(self, manager, session_id, user_id):
        """Test clearing pending confirmation"""
        plan = AgentPlan(
            actions=[],
            thought_process="Test",
            expected_outcome="Test",
            confidence=0.9,
        )

        manager.set_pending_confirmation(session_id, user_id, plan)
        manager.clear_pending_confirmation(session_id)

        pending = manager.get_pending_confirmation(session_id)
        assert pending is None

    def test_get_context(self, manager, session_id, user_id):
        """Test getting conversation context"""
        # Add some messages
        manager.add_user_message(session_id, user_id, "Hello")
        manager.add_assistant_message(session_id, user_id, "Hi there!")

        context = manager.get_context(session_id, user_id)

        assert context is not None
        assert context.session_id == session_id
        assert context.user_id == user_id
        assert len(context.conversation_history) > 0

    def test_update_user_preferences(self, manager, session_id, user_id):
        """Test updating user preferences"""
        # Create conversation first
        manager.get_or_create_conversation(session_id, user_id)

        # Update preferences
        manager.update_user_preferences(
            session_id, {"language": "en", "detail_level": "high"}
        )

        conversation = manager.conversations[session_id]
        assert conversation.user_preferences["language"] == "en"
        assert conversation.user_preferences["detail_level"] == "high"

    def test_set_current_task(self, manager, session_id, user_id):
        """Test setting current task"""
        manager.get_or_create_conversation(session_id, user_id)
        manager.set_current_task(session_id, "Learning Python")

        conversation = manager.conversations[session_id]
        assert conversation.current_task == "Learning Python"

        # Clear task
        manager.set_current_task(session_id, None)
        assert conversation.current_task is None

    def test_get_conversation_summary(self, manager, session_id, user_id):
        """Test getting conversation summary"""
        manager.add_user_message(session_id, user_id, "Hello")
        manager.add_assistant_message(session_id, user_id, "Hi!")

        summary = manager.get_conversation_summary(session_id)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_end_conversation(self, manager, session_id, user_id):
        """Test ending conversation"""
        manager.add_user_message(session_id, user_id, "Hello")

        assert session_id in manager.conversations

        manager.end_conversation(session_id)

        assert session_id not in manager.conversations

    def test_conversation_timeout(self, manager, session_id, user_id):
        """Test conversation timeout cleanup"""
        # Create conversation
        conversation = manager.get_or_create_conversation(session_id, user_id)

        # Set very short timeout
        original_timeout = manager.conversation_timeout
        manager.conversation_timeout = timedelta(seconds=0)

        # Trigger cleanup
        manager._cleanup_expired_conversations()

        # Conversation should be removed
        assert session_id not in manager.conversations

        # Restore original timeout
        manager.conversation_timeout = original_timeout

    def test_multiple_sessions(self, manager):
        """Test managing multiple sessions"""
        session1 = "session_1"
        session2 = "session_2"
        user1 = "user_1"
        user2 = "user_2"

        manager.add_user_message(session1, user1, "Message from session 1")
        manager.add_user_message(session2, user2, "Message from session 2")

        assert session1 in manager.conversations
        assert session2 in manager.conversations

        conv1 = manager.conversations[session1]
        conv2 = manager.conversations[session2]

        assert conv1.user_id == user1
        assert conv2.user_id == user2
        assert conv1.messages[0].content != conv2.messages[0].content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
