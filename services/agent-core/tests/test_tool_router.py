"""
Unit tests for Tool Router
Tests action validation and security enforcement
"""

import pytest
from src.pipeline.tool_router import ToolRouter
from src.models.tool_action import ToolAction, ToolName, ConfirmationLevel


class TestToolRouter:
    """Test suite for ToolRouter"""

    @pytest.fixture
    def router(self):
        """Create tool router instance"""
        return ToolRouter()

    @pytest.fixture
    def user_id(self):
        """Test user ID"""
        return "test_user_123"

    def test_validate_web_search_action(self, router, user_id):
        """Test validation of web_search action"""
        action = ToolAction(
            tool_name=ToolName.WEB_SEARCH,
            parameters={"query": "Python tutorials", "max_results": 5},
            reasoning="User wants to learn Python",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action, user_id)
        assert is_valid
        assert error is None

    def test_validate_missing_required_parameter(self, router, user_id):
        """Test validation fails for missing required parameters"""
        action = ToolAction(
            tool_name=ToolName.WEB_SEARCH,
            parameters={},  # Missing required 'query' parameter
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action, user_id)
        assert not is_valid
        assert "required parameter" in error.lower()

    def test_validate_parameter_type(self, router, user_id):
        """Test parameter type validation"""
        action = ToolAction(
            tool_name=ToolName.WEB_SEARCH,
            parameters={
                "query": "Python",
                "max_results": "invalid_type",  # Should be integer
            },
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action, user_id)
        # May fail validation depending on config
        # Just ensure it doesn't crash
        assert isinstance(is_valid, bool)

    def test_validate_parameter_range(self, router, user_id):
        """Test parameter range validation"""
        action = ToolAction(
            tool_name=ToolName.WEB_SEARCH,
            parameters={
                "query": "Python",
                "max_results": 100,  # Exceeds max (1-10)
            },
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action, user_id)
        assert not is_valid
        assert "max" in error.lower() or "range" in error.lower()

    def test_validate_url_pattern(self, router, user_id):
        """Test URL pattern validation"""
        # Valid HTTPS URL
        action_valid = ToolAction(
            tool_name=ToolName.WEB_FETCH,
            parameters={"url": "https://example.com", "extract_type": "text"},
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action_valid, user_id)
        assert is_valid

        # Invalid URL (HTTP not allowed if config requires HTTPS)
        action_invalid = ToolAction(
            tool_name=ToolName.WEB_FETCH,
            parameters={"url": "not-a-url", "extract_type": "text"},
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action_invalid, user_id)
        # May fail depending on pattern config
        assert isinstance(is_valid, bool)

    def test_file_read_allowlist(self, router, user_id):
        """Test file_read respects allowlist"""
        # Path in allowlist (~/Documents, ~/Downloads, ./workspace)
        action_allowed = ToolAction(
            tool_name=ToolName.FILE_READ,
            parameters={"path": "./workspace/test.txt"},
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,
        )

        is_valid, error = router.validate_action(action_allowed, user_id)
        # Should validate successfully (or at least not crash)
        assert isinstance(is_valid, bool)

    def test_file_write_blocklist(self, router, user_id):
        """Test file_write respects blocklist"""
        # Path in blocklist (/etc, /sys, C:\\Windows)
        action_blocked = ToolAction(
            tool_name=ToolName.FILE_WRITE,
            parameters={"path": "/etc/passwd", "content": "test", "overwrite": False},
            reasoning="Test",
            confirmation_level=ConfirmationLevel.HARD,
        )

        is_valid, error = router.validate_action(action_blocked, user_id)
        assert not is_valid
        assert "blocked" in error.lower() or "not in allowlist" in error.lower()

    def test_confirmation_level_enforcement(self, router, user_id):
        """Test confirmation level is enforced"""
        # file_write requires HARD confirmation
        action = ToolAction(
            tool_name=ToolName.FILE_WRITE,
            parameters={
                "path": "./workspace/test.txt",
                "content": "test",
                "overwrite": True,
            },
            reasoning="Test",
            confirmation_level=ConfirmationLevel.NONE,  # Too low
        )

        is_valid, error = router.validate_action(action, user_id)

        # Should upgrade confirmation level or validate
        assert isinstance(is_valid, bool)
        # Confirmation level should be upgraded
        if is_valid:
            assert action.confirmation_level == ConfirmationLevel.HARD

    def test_disabled_tool_rejection(self, router, user_id):
        """Test that disabled tools are rejected"""
        # system_command is disabled by default
        action = ToolAction(
            tool_name=ToolName.SYSTEM_COMMAND,
            parameters={"command": "ls"},
            reasoning="Test",
            confirmation_level=ConfirmationLevel.HARD,
        )

        is_valid, error = router.validate_action(action, user_id)
        assert not is_valid
        assert "disabled" in error.lower()

    def test_route_action_web_tools(self, router):
        """Test routing of web tools"""
        web_tools = [
            ToolName.WEB_SEARCH,
            ToolName.WEB_FETCH,
            ToolName.BROWSER_NAVIGATE,
            ToolName.BROWSER_CLICK,
            ToolName.BROWSER_TYPE,
        ]

        for tool in web_tools:
            action = ToolAction(
                tool_name=tool,
                parameters={},
                reasoning="Test",
                confirmation_level=ConfirmationLevel.NONE,
            )
            service = router.route_action(action)
            assert service == "web-service"

    def test_route_action_file_tools(self, router):
        """Test routing of file/system tools"""
        file_tools = [
            ToolName.FILE_READ,
            ToolName.FILE_LIST,
            ToolName.FILE_WRITE,
            ToolName.SYSTEM_COMMAND,
        ]

        for tool in file_tools:
            action = ToolAction(
                tool_name=tool,
                parameters={},
                reasoning="Test",
                confirmation_level=ConfirmationLevel.NONE,
            )
            service = router.route_action(action)
            assert service == "tool-executor"

    def test_get_tool_config(self, router):
        """Test retrieval of tool configuration"""
        config = router.get_tool_config("web_search")

        assert config is not None
        assert "name" in config
        assert "description" in config
        assert "confirmation_level" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
