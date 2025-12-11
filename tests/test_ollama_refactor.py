"""
Test for check_model_updates refactoring - validates behavior remains unchanged.
"""
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ollama_code_assistant import _parse_model_age  # noqa: E402


@pytest.mark.parametrize(
    "modified,expected_category",
    [
        ("5 seconds ago", "up_to_date"),
        ("2 minutes ago", "up_to_date"),
        ("1 hour ago", "up_to_date"),
        ("3 days ago", "up_to_date"),
        ("15 days ago", "needs_check"),
        ("45 days ago", "needs_check"),
        ("1 week ago", "up_to_date"),
        ("5 weeks ago", "needs_check"),
        ("10 weeks ago", "updates_available"),
        ("1 month ago", "needs_check"),
        ("3 months ago", "updates_available"),
        ("1 year ago", "updates_available"),
    ],
)
def test_parse_model_age_categorization(modified, expected_category):
    """Test that _parse_model_age categorizes time strings correctly"""
    result = _parse_model_age(modified)
    assert result.category == expected_category, (
        f"Expected '{modified}' to be categorized as '{expected_category}', "
        f"but got '{result.category}'. Full result: {result}"
    )


@pytest.mark.parametrize(
    "modified,expected_icon_prefix",
    [
        ("1 second ago", "✅"),
        ("15 days ago", "⚠️"),
        ("10 weeks ago", "🔴"),
        ("5 years ago", "🔴"),
        ("invalid format", "❓"),
    ],
)
def test_parse_model_age_status_icons(modified, expected_icon_prefix):
    """Verify all expected status icons are preserved"""
    result = _parse_model_age(modified)
    assert result.status_icon.startswith(expected_icon_prefix), (
        f"Expected '{modified}' to have icon starting with '{expected_icon_prefix}', " f"but got '{result.status_icon}'"
    )


def test_parse_model_age_returns_correct_structure():
    """Verify _parse_model_age returns ModelUpdateStatus with all required fields"""
    result = _parse_model_age("1 week ago")
    assert hasattr(result, "status_icon"), "Missing status_icon attribute"
    assert hasattr(result, "recommendation"), "Missing recommendation attribute"
    assert hasattr(result, "category"), "Missing category attribute"
    assert isinstance(result.status_icon, str), "status_icon should be a string"
    assert isinstance(result.recommendation, str), "recommendation should be a string"
    assert isinstance(result.category, str), "category should be a string"
