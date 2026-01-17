"""
Allowlist Validator - Path and command security validation
Checks paths and commands against allowlist/blocklist patterns
"""

import re
from pathlib import Path
from typing import List


class AllowlistValidator:
    """
    Validates paths and commands against security policies
    Supports glob patterns for flexible allowlist/blocklist rules
    """

    def __init__(self):
        """Initialize allowlist validator"""
        pass

    def is_allowed(self, value: str, allowlist: List[str]) -> bool:
        """
        Check if value matches any allowlist pattern

        Args:
            value: Value to check (path, URL, command, etc.)
            allowlist: List of allowed patterns

        Returns:
            True if allowed, False otherwise
        """
        if not allowlist:
            return True  # No allowlist means everything is allowed

        for pattern in allowlist:
            if self._matches_pattern(value, pattern):
                return True

        return False

    def is_blocked(self, value: str, blocklist: List[str]) -> bool:
        """
        Check if value matches any blocklist pattern

        Args:
            value: Value to check
            blocklist: List of blocked patterns

        Returns:
            True if blocked, False otherwise
        """
        if not blocklist:
            return False  # No blocklist means nothing is blocked

        for pattern in blocklist:
            if self._matches_pattern(value, pattern):
                return True

        return False

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """
        Check if value matches a pattern (supports glob and regex)

        Args:
            value: Value to check
            pattern: Pattern to match against

        Returns:
            True if matches, False otherwise
        """
        # Normalize paths
        value = value.replace("\\", "/")
        pattern = pattern.replace("\\", "/")

        # Exact match
        if value == pattern:
            return True

        # Glob pattern with wildcard
        if "*" in pattern:
            regex = self._glob_to_regex(pattern)
            if re.match(regex, value):
                return True

        # Prefix match for paths
        if pattern.endswith("/"):
            if value.startswith(pattern):
                return True

        # Check if value is under pattern directory
        try:
            value_path = Path(value).resolve()
            pattern_path = Path(pattern.rstrip("*")).resolve()
            if self._is_subpath(value_path, pattern_path):
                return True
        except Exception:
            # Path resolution failed, continue with string matching
            pass

        return False

    def _glob_to_regex(self, pattern: str) -> str:
        """
        Convert glob pattern to regex

        Args:
            pattern: Glob pattern

        Returns:
            Regex pattern
        """
        # Escape special regex characters except *
        pattern = re.escape(pattern)
        # Replace escaped * with regex equivalent
        pattern = pattern.replace(r"\*", ".*")
        return f"^{pattern}$"

    def _is_subpath(self, path: Path, parent: Path) -> bool:
        """
        Check if path is under parent directory

        Args:
            path: Path to check
            parent: Parent directory

        Returns:
            True if path is under parent
        """
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    def validate_file_path(
        self, path: str, allowlist: List[str], blocklist: List[str]
    ) -> bool:
        """
        Validate file path against allowlist and blocklist

        Args:
            path: File path to validate
            allowlist: Allowed path patterns
            blocklist: Blocked path patterns

        Returns:
            True if valid, False otherwise
        """
        # Check blocklist first
        if self.is_blocked(path, blocklist):
            return False

        # Then check allowlist
        return self.is_allowed(path, allowlist)

    def validate_command(self, command: str, allowlist: List[str]) -> bool:
        """
        Validate system command against allowlist

        Args:
            command: Command to validate
            allowlist: Allowed command patterns

        Returns:
            True if valid, False otherwise
        """
        if not allowlist:
            return False  # Commands require explicit allowlist

        # Extract command name (first token)
        command_name = command.strip().split()[0] if command.strip() else ""

        return self.is_allowed(command_name, allowlist)
