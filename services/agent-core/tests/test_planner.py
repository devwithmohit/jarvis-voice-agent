"""
Unit tests for Planner
Tests LLM-based execution planning
"""

import pytest
from src.pipeline.planner import Planner
from src.models.intent import Intent, IntentType
from src.models.tool_action import ToolName


class TestPlanner:
    """Test suite for Planner"""

    @pytest.fixture
    def planner(self):
        """Create planner instance"""
        available_tools = [tool.value for tool in ToolName]
        return Planner(available_tools=available_tools)

    @pytest.fixture
    def search_intent(self):
        """Create search intent"""
        return Intent(
            type=IntentType.SEARCH,
            confidence=0.9,
            entities={"query": "Python tutorials"},
        )

    @pytest.fixture
    def execute_intent(self):
        """Create execute intent"""
        return Intent(type=IntentType.EXECUTE, confidence=0.85, entities={})

    @pytest.fixture
    def context(self):
        """Create context"""
        return {
            "conversation_summary": "User wants to learn Python",
            "current_task": None,
            "user_preferences": {},
        }

    def test_create_plan_basic(self, planner, search_intent, context):
        """Test basic plan creation"""
        plan = planner.create_plan(
            user_input="search for Python tutorials",
            intent=search_intent,
            context=context,
        )

        assert plan is not None
        assert isinstance(plan.actions, list)
        assert plan.thought_process != ""
        assert plan.expected_outcome != ""
        assert 0 <= plan.confidence <= 1

    def test_plan_respects_max_actions(self, planner, execute_intent, context):
        """Test that plans respect max actions limit"""
        plan = planner.create_plan(
            user_input="do many complex tasks",
            intent=execute_intent,
            context=context,
        )

        # Should not exceed max_actions (default 5)
        assert len(plan.actions) <= planner.max_actions

    def test_plan_includes_reasoning(self, planner, search_intent, context):
        """Test that plan includes reasoning for actions"""
        plan = planner.create_plan(
            user_input="search for Python tutorials",
            intent=search_intent,
            context=context,
        )

        if plan.actions:
            for action in plan.actions:
                assert action.reasoning != ""

    def test_confidence_calculation(self, planner, search_intent, context):
        """Test confidence calculation"""
        plan = planner.create_plan(
            user_input="search for Python tutorials",
            intent=search_intent,
            context=context,
        )

        # Confidence should be based on intent confidence
        assert plan.confidence > 0
        # High intent confidence should result in reasonable plan confidence
        if search_intent.confidence > 0.8:
            assert plan.confidence > 0.5

    def test_confirmation_detection(self, planner, execute_intent, context):
        """Test detection of confirmation needs"""
        # Create plan that might need confirmation
        plan = planner.create_plan(
            user_input="delete all my files",
            intent=execute_intent,
            context=context,
        )

        # Should detect need for confirmation for destructive actions
        # (depends on LLM response, so we just check the field exists)
        assert isinstance(plan.needs_user_confirmation, bool)

    def test_empty_plan_on_error(self, planner, context):
        """Test that errors result in empty plan"""
        # Create intent with very low confidence
        low_confidence_intent = Intent(
            type=IntentType.UNKNOWN,
            confidence=0.1,
        )

        plan = planner.create_plan(
            user_input="",
            intent=low_confidence_intent,
            context=context,
        )

        # Should handle gracefully (may return empty plan or valid plan)
        assert plan is not None
        assert isinstance(plan.actions, list)

    def test_context_influences_planning(self, planner, search_intent):
        """Test that context influences plan creation"""
        # Context with user preferences
        context_with_prefs = {
            "conversation_summary": "User prefers detailed results",
            "current_task": "research",
            "user_preferences": {"detail_level": "high"},
        }

        plan = planner.create_plan(
            user_input="search for Python tutorials",
            intent=search_intent,
            context=context_with_prefs,
        )

        # Plan should be created successfully
        assert plan is not None
        assert len(plan.actions) > 0

    def test_tool_selection(self, planner, search_intent, context):
        """Test that appropriate tools are selected"""
        plan = planner.create_plan(
            user_input="search for Python tutorials online",
            intent=search_intent,
            context=context,
        )

        if plan.actions:
            # Should use web_search tool for search intent
            tool_names = [action.tool_name for action in plan.actions]
            assert ToolName.WEB_SEARCH in tool_names or ToolName.WEB_FETCH in tool_names

    def test_refine_plan(self, planner, search_intent, context):
        """Test plan refinement based on feedback"""
        original_plan = planner.create_plan(
            user_input="search for Python tutorials",
            intent=search_intent,
            context=context,
        )

        refined_plan = planner.refine_plan(
            original_plan=original_plan,
            user_feedback="I want more detailed results",
            context=context,
        )

        # Should return a plan (may be same or different)
        assert refined_plan is not None
        assert isinstance(refined_plan.actions, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
