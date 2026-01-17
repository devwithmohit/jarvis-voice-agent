"""
Response Synthesizer - Generate natural language responses
Converts plan execution results into user-friendly responses
"""

from typing import List, Dict, Any
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.models.tool_action import AgentPlan, ToolActionResult
from src.llm.client import LLMClient


class ResponseSynthesizer:
    """
    Synthesizes natural language responses from plan execution results
    Uses LLM to generate contextual, user-friendly responses
    """

    def __init__(self):
        """Initialize response synthesizer"""
        self.llm_client = LLMClient()

    def synthesize(
        self,
        user_input: str,
        plan: AgentPlan,
        results: List[ToolActionResult],
    ) -> str:
        """
        Synthesize response from plan and results

        Args:
            user_input: User's original request
            plan: Execution plan
            results: Tool execution results

        Returns:
            Natural language response
        """
        try:
            # Convert to dictionaries for LLM
            plan_dict = {
                "thought_process": plan.thought_process,
                "actions": [
                    {
                        "tool": action.tool_name.value,
                        "parameters": action.parameters,
                        "reasoning": action.reasoning,
                    }
                    for action in plan.actions
                ],
                "expected_outcome": plan.expected_outcome,
            }

            results_dict = [
                {
                    "tool": result.tool_name.value,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                }
                for result in results
            ]

            # Generate response using LLM
            response = self.llm_client.synthesize_response(
                user_input=user_input,
                plan=plan_dict,
                results=results_dict,
            )

            return response

        except Exception as e:
            print(f"Error synthesizing response: {e}")
            # Fallback to simple response
            return self._generate_fallback_response(results)

    def generate_error_response(self, error: str, user_input: str) -> str:
        """
        Generate error response

        Args:
            error: Error message
            user_input: User's original request

        Returns:
            Error response
        """
        return f"I apologize, but I encountered an error while processing your request: {error}\n\nCould you please rephrase or provide more details?"

    def generate_confirmation_prompt(self, plan: AgentPlan) -> str:
        """
        Generate confirmation prompt for plan

        Args:
            plan: Plan requiring confirmation

        Returns:
            Confirmation prompt
        """
        try:
            # Get actions requiring confirmation
            actions_to_confirm = plan.get_actions_requiring_confirmation()

            if not actions_to_confirm:
                return ""

            # Generate prompt for each action
            prompts = []
            for action in actions_to_confirm:
                action_dict = {
                    "tool_name": action.tool_name.value,
                    "parameters": action.parameters,
                    "reasoning": action.reasoning,
                }

                prompt = self.llm_client.generate_confirmation_prompt(action_dict)
                prompts.append(prompt)

            # Combine prompts
            if len(prompts) == 1:
                return prompts[0] + "\n\nDo you want me to proceed? (yes/no)"
            else:
                combined = "I need your confirmation for the following actions:\n\n"
                for i, prompt in enumerate(prompts, 1):
                    combined += f"{i}. {prompt}\n\n"
                combined += "Do you want me to proceed with all these actions? (yes/no)"
                return combined

        except Exception as e:
            print(f"Error generating confirmation prompt: {e}")
            return self._generate_fallback_confirmation_prompt(plan)

    def generate_clarification_prompt(
        self, user_input: str, ambiguity_reason: str
    ) -> str:
        """
        Generate clarification prompt

        Args:
            user_input: User's input
            ambiguity_reason: Reason for ambiguity

        Returns:
            Clarification prompt
        """
        return f"I'm not entirely sure what you'd like me to do. {ambiguity_reason}\n\nCould you please clarify your request?"

    def _generate_fallback_response(self, results: List[ToolActionResult]) -> str:
        """
        Generate simple fallback response

        Args:
            results: Tool execution results

        Returns:
            Fallback response
        """
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        if failure_count == 0:
            return f"I've completed {success_count} action(s) successfully."
        elif success_count == 0:
            return f"I encountered errors executing {failure_count} action(s). Please try again or rephrase your request."
        else:
            return f"I completed {success_count} action(s) successfully, but {failure_count} action(s) failed."

    def _generate_fallback_confirmation_prompt(self, plan: AgentPlan) -> str:
        """
        Generate simple fallback confirmation prompt

        Args:
            plan: Plan requiring confirmation

        Returns:
            Fallback confirmation prompt
        """
        actions_to_confirm = plan.get_actions_requiring_confirmation()

        if not actions_to_confirm:
            return ""

        action_list = "\n".join(
            f"- {action.tool_name.value} with parameters: {action.parameters}"
            for action in actions_to_confirm
        )

        return f"I need your confirmation to proceed with these actions:\n\n{action_list}\n\nDo you want me to proceed? (yes/no)"

    def summarize_plan(self, plan: AgentPlan) -> str:
        """
        Generate human-readable plan summary

        Args:
            plan: Plan to summarize

        Returns:
            Plan summary
        """
        if not plan.actions:
            return "No actions planned."

        summary = f"Plan (confidence: {plan.confidence:.1%}):\n\n"
        summary += f"Reasoning: {plan.thought_process}\n\n"
        summary += "Actions:\n"

        for i, action in enumerate(plan.actions, 1):
            summary += f"{i}. {action.tool_name.value}: {action.reasoning}\n"

        summary += f"\nExpected outcome: {plan.expected_outcome}"

        return summary
