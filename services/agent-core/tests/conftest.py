"""
Pytest configuration file
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture"""
    return {
        "test_mode": True,
        "mock_llm": True,
    }
