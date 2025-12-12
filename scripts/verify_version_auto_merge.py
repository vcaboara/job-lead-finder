#!/usr/bin/env python3
"""
Verify Version Bump Auto-Merge Script

This script verifies that the version bump auto-merge functionality works correctly
after PR merges. It simulates and validates the key components of the version-bump.yml
GitHub Actions workflow.

Tasks:
1. Validate version bump type detection
2. Test version increment logic
3. Verify pyproject.toml update
4. Test GitHub CLI PR creation command simulation
5. Validate auto-merge flag logic

Run this script after setting up VERSION_BUMP_PAT secret to verify auto-merge works.
"""

import os
import re
import subprocess
from pathlib import Path

# Test data - simulate a real PR scenario
TEST_PR_SCENARIOS = [
    {"title": "feat: add new API endpoint", "labels": ["enhancement"], "expected_bump": "minor"},
    {"title": "fix: resolve authentication bug", "labels": ["bug", "patch"], "expected_bump": "patch"},
    {"title": "feat!:BREAKING CHANGE - refactor core API", "labels": ["breaking-change"], "expected_bump": "major"},
    {"title": "docs: update README", "labels": ["documentation"], "expected_bump": "patch"},
]


def determine_bump_type(pr_title: str, pr_labels: list) -> str:
    """Determine version bump type based on PR title and labels (matches workflow logic)"""
    labels_str = ",".join(pr_labels)

    if any(label in labels_str for label in ["major", "breaking-change"]) or "BREAKING CHANGE" in pr_title:
        return "major"
    elif any(label in labels_str for label in ["minor"]) or any(
        pr_title.startswith(prefix) for prefix in ["feat:", "feat("]
    ):
        return "minor"
    else:
        return "patch"


def increment_version(current_version: str, bump_type: str) -> str:
    """Increment version number based on bump type"""
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


def get_current_version(pyproject_content: str) -> str:
    """Extract version from pyproject.toml content using regex"""
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject_content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Version not found in pyproject.toml")


def validate_pyproject_update(original_content: str, new_version: str) -> tuple[str, str]:
    """Validate and simulate pyproject.toml version update"""
    # Extract original version
    original_version = get_current_version(original_content)

    # Replace version line
    def replace_version(match):
        return f"{match.group(1)}{new_version}{match.group(3)}"

    pattern = r'^(version\s*=\s*["\'])([^"\']+)(["\'])'
    updated_content = re.sub(pattern, replace_version, original_content, flags=re.MULTILINE)

    return updated_content, original_version


def simulate_gh_pr_creation(
    branch_name: str, version: str, old_version: str, pr_number: str, pr_title: str
) -> list[str]:
    """Simulate the GitHub CLI commands that would create the version bump PR"""
    commands = []

    # Create PR command
    pr_body = f"""Automated version bump after merging PR #{pr_number}.

**Changes:**
- Bumped version from v{old_version} to v{version}
- Created release tag v{version}

**Status:**
This PR will auto-merge once CI checks pass.

---
AI-Generated-By: GitHub Actions Bot"""

    create_cmd = [
        "gh",
        "pr",
        "create",
        "--title",
        f"[AI] chore: bump version to v{version}",
        "--body",
        pr_body,
        "--base",
        "main",
        "--head",
        branch_name,
        "--label",
        "automation",
        "--label",
        "version-bump",
    ]

    commands.append(" ".join(create_cmd))

    # Auto-merge command (simulated)
    has_pat = os.getenv("VERSION_BUMP_PAT") is not None
    if has_pat:
        merge_cmd = ["gh", "pr", "merge", "<PR_URL>", "--auto", "--squash", "--delete-branch"]
        commands.append(" ".join(merge_cmd))
    else:
        commands.append("# Manual merge required - VERSION_BUMP_PAT not set")

    return commands


def test_version_bump_logic():
    """Test the core version bump logic with various scenarios"""
    print("🧪 Testing Version Bump Logic")
    print("=" * 50)

    # Read current pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False

    with open(pyproject_path, "r") as f:
        original_content = f.read()

    current_version = get_current_version(original_content)
    print(f"Current version: {current_version}")

    all_passed = True

    for i, scenario in enumerate(TEST_PR_SCENARIOS, 1):
        print(f"\nTest Scenario {i}: {scenario['title']}")
        print(f"Labels: {scenario['labels']}")

        # Test bump type determination
        actual_bump = determine_bump_type(scenario["title"], scenario["labels"])
        expected_bump = scenario["expected_bump"]

        if actual_bump == expected_bump:
            print(f"✅ Bump type: {actual_bump}")
        else:
            print(f"❌ Bump type mismatch: expected {expected_bump}, got {actual_bump}")
            all_passed = False

        # Test version increment
        new_version = increment_version(current_version, actual_bump)
        print(f"   New version would be: {current_version} → {new_version}")

    return all_passed


def test_auto_merge_setup():
    """Test auto-merge setup and PAT availability"""
    print("\n🔧 Testing Auto-Merge Setup")
    print("=" * 50)

    # Check for VERSION_BUMP_PAT
    pat = os.getenv("VERSION_BUMP_PAT")
    if pat:
        # Don't print the actual PAT for security
        print("✅ VERSION_BUMP_PAT is set")
        # Basic PAT format validation (GitHub PATs start with ghp_)
        if pat.startswith("ghp_"):
            print("✅ VERSION_BUMP_PAT appears to be a valid GitHub PAT")
        else:
            print("⚠️  VERSION_BUMP_PAT doesn't look like a GitHub PAT (should start with 'ghp_')")
    else:
        print("⚠️  VERSION_BUMP_PAT not set - auto-merge will require manual intervention")

    # Check if GitHub CLI is available
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ GitHub CLI available: {result.stdout.strip().split()[2]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI not available - required for PR operations")


def simulate_complete_workflow():
    """Simulate the complete version bump workflow with realistic data"""
    print("\n🚀 Simulating Complete Version Bump Workflow")
    print("=" * 50)

    # Use realistic scenario
    scenario = TEST_PR_SCENARIOS[0]  # feat PR
    print(f"Scenario: {scenario['title']}")

    # Read current version
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        original_content = f.read()

    current_version = get_current_version(original_content)
    print(f"Current version: {current_version}")

    # Step 1: Determine bump type
    bump_type = determine_bump_type(scenario["title"], scenario["labels"])
    print(f"Bump type determined: {bump_type}")

    # Step 2: Calculate new version
    new_version = increment_version(current_version, bump_type)
    print(f"New version: {new_version}")

    # Step 3: Update pyproject.toml
    updated_content, old_version = validate_pyproject_update(original_content, new_version)
    print("✅ pyproject.toml content updated (simulation)")

    # Step 4: Simulate PR creation
    branch_name = f"auto/version-bump-v{new_version}"
    pr_number = "123"  # Mock PR number
    commands = simulate_gh_pr_creation(branch_name, new_version, old_version, pr_number, scenario["title"])

    print("\n📋 GitHub CLI Commands (simulated):")
    for cmd in commands:
        print(f"   {cmd}")

    return True


def main():
    """Run all verification tests"""
    print("🔍 Version Bump Auto-Merge Verification")
    print("=" * 50)
    print("This script verifies the version bump workflow logic and auto-merge setup.\n")

    # Run tests
    logic_ok = test_version_bump_logic()
    test_auto_merge_setup()
    simulation_ok = simulate_complete_workflow()

    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)

    if logic_ok and simulation_ok:
        print("✅ All version bump logic tests passed")
    else:
        print("❌ Some version bump logic tests failed")

    pat_set = os.getenv("VERSION_BUMP_PAT") is not None
    if pat_set:
        print("✅ VERSION_BUMP_PAT is configured for auto-merge")
    else:
        print("⚠️  VERSION_BUMP_PAT not set - auto-merge will be manual")

    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
        gh_available = True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        gh_available = False

    if gh_available:
        print("✅ GitHub CLI is available")
    else:
        print("❌ GitHub CLI not available")

    print("\n🔧 Next Steps:")
    if not pat_set:
        print("1. Set VERSION_BUMP_PAT secret in GitHub repository settings")
        print("2. Create a PAT with 'repo' permissions")
    print("3. Test with a real PR merge to verify auto-merge works in production")

    return 0


if __name__ == "__main__":
    exit(main())
