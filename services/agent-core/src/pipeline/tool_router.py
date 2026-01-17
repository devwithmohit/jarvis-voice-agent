"""
Tool Router - Validates and routes tool actions
Enforces security policies, rate limits, and parameter validation
"""

import re
import yaml
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sys
import os

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.models.tool_action import ToolAction, ToolActionResult, ConfirmationLevel
from src.security.allowlist import AllowlistValidator
from src.security.rate_limiter import RateLimiter


class ToolRouter:
    """
    Routes tool actions to appropriate services
    Validates parameters and enforces security policies
    """

    def __init__(self):
        """Initialize tool router"""
        self.tool_configs = self._load_tool_configs()
        self.allowlist_validator = AllowlistValidator()
        self.rate_limiter = RateLimiter()

    def _load_tool_configs(self) -> Dict[str, Any]:
        """Load tool configurations from YAML"""
        config_path = Path(__file__).parent.parent.parent / "config" / "tools.yaml"

        if not config_path.exists():
            print(f"Warning: tools.yaml not found at {config_path}")
            return {}

        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
                # Index by tool name
                return {tool["name"]: tool for tool in data.get("tools", [])}
        except Exception as e:
            print(f"Error loading tools.yaml: {e}")
            return {}

    def validate_action(
        self, action: ToolAction, user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate tool action against security policies

        Args:
            action: Tool action to validate
            user_id: User identifier for rate limiting

        Returns:
            Tuple of (is_valid, error_message)
        """
        tool_name = action.tool_name.value
        tool_config = self.tool_configs.get(tool_name)

        if not tool_config:
            return False, f"Tool '{tool_name}' not found in configuration"

        # Check if tool is enabled
        if not tool_config.get("enabled", True):
            return False, f"Tool '{tool_name}' is disabled"

        # Validate parameters
        is_valid, error = self._validate_parameters(action, tool_config)
        if not is_valid:
            return False, error

        # Check rate limits
        is_valid, error = self._check_rate_limit(tool_name, user_id, tool_config)
        if not is_valid:
            return False, error

        # Validate against allowlist/blocklist
        is_valid, error = self._validate_security_policies(action, tool_config)
        if not is_valid:
            return False, error

        # Validate confirmation level
        is_valid, error = self._validate_confirmation_level(action, tool_config)
        if not is_valid:
            return False, error

        return True, None

    def _validate_parameters(
        self, action: ToolAction, tool_config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate action parameters against tool schema

        Args:
            action: Tool action
            tool_config: Tool configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        parameters = action.parameters
        param_schema = tool_config.get("parameters", [])

        # Check required parameters
        for param_def in param_schema:
            param_name = param_def.get("name")
            required = param_def.get("required", False)

            if required and param_name not in parameters:
                return False, f"Missing required parameter: {param_name}"

            # Validate parameter if present
            if param_name in parameters:
                is_valid, error = self._validate_parameter_value(
                    param_name, parameters[param_name], param_def
                )
                if not is_valid:
                    return False, error

        return True, None

    def _validate_parameter_value(
        self, param_name: str, value: Any, param_def: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single parameter value

        Args:
            param_name: Parameter name
            value: Parameter value
            param_def: Parameter definition

        Returns:
            Tuple of (is_valid, error_message)
        """
        param_type = param_def.get("type")
        validation = param_def.get("validation", {})

        # Type validation
        if param_type == "string" and not isinstance(value, str):
            return False, f"Parameter '{param_name}' must be a string"
        elif param_type == "integer" and not isinstance(value, int):
            return False, f"Parameter '{param_name}' must be an integer"
        elif param_type == "boolean" and not isinstance(value, bool):
            return False, f"Parameter '{param_name}' must be a boolean"

        # Pattern validation
        if "pattern" in validation:
            pattern = validation["pattern"]
            if isinstance(value, str) and not re.match(pattern, value):
                return (
                    False,
                    f"Parameter '{param_name}' does not match pattern: {pattern}",
                )

        # Enum validation
        if "enum" in validation:
            allowed_values = validation["enum"]
            if value not in allowed_values:
                return (
                    False,
                    f"Parameter '{param_name}' must be one of: {allowed_values}",
                )

        # Min/max validation for integers
        if param_type == "integer":
            if "min" in validation and value < validation["min"]:
                return False, f"Parameter '{param_name}' must be >= {validation['min']}"
            if "max" in validation and value > validation["max"]:
                return False, f"Parameter '{param_name}' must be <= {validation['max']}"

        return True, None

    def _check_rate_limit(
        self, tool_name: str, user_id: str, tool_config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check rate limit for tool

        Args:
            tool_name: Tool name
            user_id: User identifier
            tool_config: Tool configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        rate_limit = tool_config.get("rate_limit")
        if not rate_limit:
            return True, None

        # Parse rate limit (e.g., "10/minute")
        try:
            limit, period = rate_limit.split("/")
            limit = int(limit)

            is_allowed = self.rate_limiter.check_rate_limit(
                user_id=user_id, tool_name=tool_name, limit=limit, period=period
            )

            if not is_allowed:
                return False, f"Rate limit exceeded for '{tool_name}': {rate_limit}"

            return True, None
        except Exception as e:
            print(f"Error parsing rate limit '{rate_limit}': {e}")
            return True, None  # Allow if rate limit config is invalid

    def _validate_security_policies(
        self, action: ToolAction, tool_config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate against allowlist/blocklist

        Args:
            action: Tool action
            tool_config: Tool configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        allowlist = tool_config.get("security", {}).get("allowlist", [])
        blocklist = tool_config.get("security", {}).get("blocklist", [])

        # Extract sensitive parameters (path, url, command, etc.)
        sensitive_params = ["path", "url", "command", "selector"]
        for param_name in sensitive_params:
            if param_name in action.parameters:
                param_value = action.parameters[param_name]

                # Check blocklist first
                if blocklist:
                    is_blocked = self.allowlist_validator.is_blocked(
                        param_value, blocklist
                    )
                    if is_blocked:
                        return (
                            False,
                            f"Parameter '{param_name}' value is blocked: {param_value}",
                        )

                # Check allowlist
                if allowlist:
                    is_allowed = self.allowlist_validator.is_allowed(
                        param_value, allowlist
                    )
                    if not is_allowed:
                        return (
                            False,
                            f"Parameter '{param_name}' value not in allowlist: {param_value}",
                        )

        return True, None

    def _validate_confirmation_level(
        self, action: ToolAction, tool_config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate confirmation level matches tool requirements

        Args:
            action: Tool action
            tool_config: Tool configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_level = tool_config.get("confirmation_level", "none")

        try:
            required = ConfirmationLevel(required_level)
        except ValueError:
            required = ConfirmationLevel.NONE

        # Ensure action has at least the required confirmation level
        level_order = {
            ConfirmationLevel.NONE: 0,
            ConfirmationLevel.SOFT: 1,
            ConfirmationLevel.HARD: 2,
        }

        if level_order[action.confirmation_level] < level_order[required]:
            action.confirmation_level = required  # Upgrade to required level

        return True, None

    def route_action(self, action: ToolAction) -> str:
        """
        Determine which service should execute this action

        Args:
            action: Tool action

        Returns:
            Service name (e.g., 'web-service', 'tool-executor')
        """
        tool_name = action.tool_name.value

        # Web tools go to web-service
        if tool_name in [
            "web_search",
            "web_fetch",
            "browser_navigate",
            "browser_click",
            "browser_type",
        ]:
            return "web-service"

        # File and system tools go to tool-executor
        return "tool-executor"

    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a tool

        Args:
            tool_name: Tool name

        Returns:
            Tool configuration or None
        """
        return self.tool_configs.get(tool_name)
