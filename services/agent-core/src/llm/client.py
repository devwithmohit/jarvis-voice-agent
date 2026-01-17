"""
LLM Client for interacting with language models
Supports OpenRouter, OpenAI, and local LLMs
"""

import os
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from config import get_settings

settings = get_settings()


class LLMClient:
    """
    Client for interacting with Large Language Models
    Handles retries, error handling, and response parsing
    """

    def __init__(self):
        """Initialize LLM client with configuration"""
        self.api_key = settings.llm_api_key or settings.openrouter_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout

        if not self.api_key:
            raise ValueError(
                "LLM API key not configured. Set LLM_API_KEY or OPENROUTER_API_KEY"
            )

        # Initialize OpenAI client (compatible with OpenRouter)
        extra_headers = {}
        if "openrouter" in self.base_url.lower():
            extra_headers = {
                "HTTP-Referer": settings.openrouter_site_url or "http://localhost",
                "X-Title": settings.openrouter_app_name or "Voice AI Agent",
            }

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            default_headers=extra_headers,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text from the LLM

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            json_mode: Force JSON output format

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "temperature": temperature
            if temperature is not None
            else settings.llm_temperature,
        }

        # JSON mode (not all providers support this)
        if json_mode:
            try:
                kwargs["response_format"] = {"type": "json_object"}
            except Exception:
                # Fallback: add JSON instruction to prompt
                if system_prompt:
                    messages[0]["content"] += "\n\nIMPORTANT: Return ONLY valid JSON."
                messages[-1]["content"] += "\n\nReturn your response as valid JSON."

        try:
            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            if json_mode:
                # Validate JSON
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    raise ValueError(f"LLM did not return valid JSON: {e}")

            return content
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            raise

    def generate_plan(
        self, user_input: str, context: Dict[str, Any], available_tools: List[str]
    ) -> str:
        """
        Generate an execution plan for the user's request

        Args:
            user_input: User's request
            context: Conversation context
            available_tools: List of available tool names

        Returns:
            JSON string containing the plan
        """
        from .prompts import PLANNING_SYSTEM_PROMPT

        prompt = f"""User request: {user_input}

Available tools: {", ".join(available_tools)}

Context summary:
- Recent conversation: {context.get("conversation_summary", "None")}
- Current task: {context.get("current_task", "None")}
- User preferences: {context.get("user_preferences", {})}

Generate a plan to fulfill the user's request using the available tools.
Consider the context and choose the most appropriate tools.
Keep the plan simple and focused."""

        return self.generate(
            prompt=prompt,
            system_prompt=PLANNING_SYSTEM_PROMPT,
            max_tokens=800,
            temperature=0.3,
            json_mode=True,
        )

    def classify_intent(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Classify the user's intent using LLM

        Args:
            user_input: User's input text
            context: Conversation context

        Returns:
            JSON string with classification result
        """
        from .prompts import INTENT_CLASSIFICATION_PROMPT

        context_summary = context.get("conversation_summary", "No recent conversation")

        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            user_input=user_input, context=context_summary
        )

        return self.generate(
            prompt=prompt, max_tokens=150, temperature=0.2, json_mode=True
        )

    def synthesize_response(
        self, user_input: str, plan: Dict[str, Any], results: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize a natural response based on plan and results

        Args:
            user_input: User's original request
            plan: Execution plan
            results: Tool execution results

        Returns:
            Natural language response
        """
        from .prompts import RESPONSE_SYNTHESIS_PROMPT, CONVERSATION_SYSTEM_PROMPT

        prompt = RESPONSE_SYNTHESIS_PROMPT.format(
            user_input=user_input,
            plan=json.dumps(plan, indent=2),
            results=json.dumps(results, indent=2),
        )

        return self.generate(
            prompt=prompt,
            system_prompt=CONVERSATION_SYSTEM_PROMPT,
            max_tokens=500,
            temperature=0.7,
        )

    def generate_confirmation_prompt(self, action: Dict[str, Any]) -> str:
        """
        Generate a user-friendly confirmation prompt

        Args:
            action: Tool action details

        Returns:
            Confirmation prompt text
        """
        from .prompts import CONFIRMATION_REQUEST_PROMPT

        prompt = CONFIRMATION_REQUEST_PROMPT.format(
            tool_name=action.get("tool_name"),
            parameters=json.dumps(action.get("parameters", {}), indent=2),
            reasoning=action.get("reasoning", ""),
        )

        return self.generate(prompt=prompt, max_tokens=200, temperature=0.5)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Simple chat completion

        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            Assistant response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in chat completion: {e}")
            raise
