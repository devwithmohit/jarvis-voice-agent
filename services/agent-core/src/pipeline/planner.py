"""
Planner - LLM-based execution planning
Generates tool action sequences from user requests
"""

import json
from typing import Dict, Any, List
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.models.tool_action import AgentPlan, ToolAction, ToolName, ConfirmationLevel
from src.models.intent import Intent
from src.llm.client import LLMClient
from config import get_settings

settings = get_settings()


class Planner:
    """
    LLM-based planner that generates execution plans
    Creates sequences of tool actions to fulfill user requests
    """

    def __init__(self, available_tools: List[str]):
        """
        Initialize planner

        Args:
            available_tools: List of available tool names
        """
        self.llm_client = LLMClient()
        self.available_tools = available_tools
        self.max_actions = 5  # Safety limit

    def create_plan(
        self,
        user_input: str,
        intent: Intent,
        context: Dict[str, Any],
    ) -> AgentPlan:
        """
        Create an execution plan for the user's request

        Args:
            user_input: User's original request
            intent: Classified intent
            context: Conversation context

        Returns:
            AgentPlan with actions and metadata
        """
        try:
            # Generate plan using LLM
            plan_json = self.llm_client.generate_plan(
                user_input=user_input,
                context=context,
                available_tools=self.available_tools,
            )

            # Parse LLM response
            plan_data = json.loads(plan_json)

            # Extract plan components
            thought_process = plan_data.get("thought_process", "")
            actions_data = plan_data.get("actions", [])
            expected_outcome = plan_data.get("expected_outcome", "")
            needs_confirmation = plan_data.get("needs_confirmation", False)

            # Enforce max actions limit
            if len(actions_data) > self.max_actions:
                print(
                    f"Warning: Plan has {len(actions_data)} actions, truncating to {self.max_actions}"
                )
                actions_data = actions_data[: self.max_actions]

            # Parse actions
            actions = []
            for action_data in actions_data:
                try:
                    action = self._parse_action(action_data)
                    if action:
                        actions.append(action)
                except Exception as e:
                    print(f"Error parsing action: {e}")
                    continue

            # Calculate overall confidence
            confidence = self._calculate_confidence(actions, intent)

            # Create plan
            plan = AgentPlan(
                actions=actions,
                thought_process=thought_process,
                expected_outcome=expected_outcome,
                confidence=confidence,
                needs_user_confirmation=needs_confirmation
                or self._requires_confirmation(actions),
            )

            return plan

        except Exception as e:
            print(f"Error creating plan: {e}")
            # Return empty plan with error
            return AgentPlan(
                actions=[],
                thought_process=f"Error creating plan: {str(e)}",
                expected_outcome="Unable to create plan",
                confidence=0.0,
                needs_user_confirmation=False,
            )

    def _parse_action(self, action_data: Dict[str, Any]) -> ToolAction:
        """
        Parse action from LLM response

        Args:
            action_data: Action data from LLM

        Returns:
            ToolAction object
        """
        tool_name = action_data.get("tool")
        parameters = action_data.get("parameters", {})
        reasoning = action_data.get("reasoning", "")

        # Validate tool name
        try:
            tool_enum = ToolName(tool_name)
        except ValueError:
            print(f"Invalid tool name: {tool_name}")
            return None

        # Determine confirmation level (will be validated against tool config later)
        confirmation_str = action_data.get("confirmation_level", "soft")
        try:
            confirmation_level = ConfirmationLevel(confirmation_str)
        except ValueError:
            confirmation_level = ConfirmationLevel.SOFT

        return ToolAction(
            tool_name=tool_enum,
            parameters=parameters,
            reasoning=reasoning,
            confirmation_level=confirmation_level,
        )

    def _calculate_confidence(self, actions: List[ToolAction], intent: Intent) -> float:
        """
        Calculate overall plan confidence

        Args:
            actions: List of actions
            intent: Classified intent

        Returns:
            Confidence score (0-1)
        """
        if not actions:
            return 0.0

        # Base confidence from intent
        confidence = intent.confidence

        # Reduce confidence for complex plans
        if len(actions) > 3:
            confidence *= 0.9
        if len(actions) > 4:
            confidence *= 0.85

        # Reduce confidence if many destructive actions
        destructive_count = sum(
            1
            for action in actions
            if action.confirmation_level == ConfirmationLevel.HARD
        )
        if destructive_count > 0:
            confidence *= max(0.7, 1 - (destructive_count * 0.1))

        return min(1.0, max(0.0, confidence))

    def _requires_confirmation(self, actions: List[ToolAction]) -> bool:
        """
        Check if any actions require user confirmation

        Args:
            actions: List of actions

        Returns:
            True if confirmation required
        """
        return any(
            action.confirmation_level
            in [ConfirmationLevel.SOFT, ConfirmationLevel.HARD]
            for action in actions
        )

    def refine_plan(
        self,
        original_plan: AgentPlan,
        user_feedback: str,
        context: Dict[str, Any],
    ) -> AgentPlan:
        """
        Refine plan based on user feedback

        Args:
            original_plan: Original plan
            user_feedback: User's feedback
            context: Conversation context

        Returns:
            Refined AgentPlan
        """
        # Create refinement prompt
        refinement_prompt = f"""Original plan:
{
            json.dumps(
                {
                    "thought_process": original_plan.thought_process,
                    "actions": [
                        {
                            "tool": action.tool_name.value,
                            "parameters": action.parameters,
                            "reasoning": action.reasoning,
                        }
                        for action in original_plan.actions
                    ],
                    "expected_outcome": original_plan.expected_outcome,
                },
                indent=2,
            )
        }

User feedback: {user_feedback}

Refine the plan based on user feedback. Generate a new improved plan."""

        try:
            # Generate refined plan
            return self.create_plan(
                user_input=refinement_prompt,
                intent=Intent(type="EXECUTE", confidence=0.8),
                context=context,
            )
        except Exception as e:
            print(f"Error refining plan: {e}")
            return original_plan
