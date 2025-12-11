"""
Test for check_model_updates refactoring - validates behavior remains unchanged.
"""
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ollama_code_assistant import _parse_model_age  # noqa: E402, F401


def test_parse_model_age():
    """Test that _parse_model_age categorizes correctly"""

    # Test cases: (modified_string, expected_category)
    test_cases = [
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
    ]

    passed = 0
    failed = 0

    for modified, expected_category in test_cases:
        result = _parse_model_age(modified)
        if result.category == expected_category:
            print(f"✅ PASS: '{modified}' -> {result.category}")
            passed += 1
        else:
            print(f"❌ FAIL: '{modified}' -> Expected {expected_category}, got {result.category}")
            print(f"   Full result: {result}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_status_icons():
    """Verify all expected status icons are preserved"""

    test_cases = [
        ("1 second ago", "✅"),
        ("15 days ago", "⚠️"),
        ("10 weeks ago", "🔴"),
        ("5 years ago", "🔴"),
        ("invalid format", "❓"),
    ]

    passed = 0
    failed = 0

    for modified, expected_icon_prefix in test_cases:
        result = _parse_model_age(modified)
        if result.status_icon.startswith(expected_icon_prefix):
            print(f"✅ PASS: '{modified}' has correct icon: {result.status_icon}")
            passed += 1
        else:
            print(
                f"❌ FAIL: '{modified}' -> Expected icon starting with {expected_icon_prefix}, got {result.status_icon}"
            )
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("=" * 80)
    print("Testing check_model_updates refactoring")
    print("=" * 80)
    print()

    print("Test 1: Model age parsing and categorization")
    print("-" * 80)
    test1_passed = test_parse_model_age()

    print("\n" + "=" * 80)
    print("Test 2: Status icons preserved")
    print("-" * 80)
    test2_passed = test_status_icons()

    print("\n" + "=" * 80)
    if test1_passed and test2_passed:
        print("✅ All tests PASSED - refactoring maintains behavior")
        sys.exit(0)
    else:
        print("❌ Some tests FAILED - refactoring changed behavior")
        sys.exit(1)
