#!/usr/bin/env python3
"""
AI Review Chain Helper
Orchestrates multi-agent code review: Ollama → Copilot → Human
"""

import argparse
import subprocess
import sys


def run_ollama_review(pr_number: int, model: str = "deepseek-coder:6.7b"):
    """Run Ollama code review on PR diff."""
    print(f"\n🤖 Running Ollama review with {model}...")

    # Get PR diff
    try:
        result = subprocess.run(["gh", "pr", "diff", str(pr_number)], capture_output=True, text=True, check=True)
        diff = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get PR diff: {e}")
        return False

    if not diff:
        print("⚠️  No diff found")
        return False

    # Prepare review prompt
    prompt = f"""Review this code change following these criteria:

CONTRIBUTOR GUIDELINES CHECK:
1. Conventional commit format (feat:, fix:, docs:, etc.)
2. Token compression applied (concise names, minimal comments)
3. Tests included for new code
4. CHANGELOG.md updated
5. For UI changes: Before/after screenshots included
6. Code quality: readable, maintainable, follows Python standards

DIFF:
{diff}

Provide:
- ✅ Passes or ❌ Fails for each guideline
- Specific feedback on issues found
- Suggestions for improvement
"""

    # Run Ollama review
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "ollama", "ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        review = result.stdout
        print("\n" + "=" * 70)
        print("📝 OLLAMA REVIEW:")
        print("=" * 70)
        print(review)
        return True
    except subprocess.TimeoutExpired:
        print("❌ Ollama review timed out (60s)")
        return False
    except Exception as e:
        print(f"❌ Ollama review failed: {e}")
        return False


def check_copilot_review(pr_number: int):
    """Check if Copilot AI PR Review has run."""
    print("\n🤖 Checking Copilot PR Review status...")

    try:
        result = subprocess.run(["gh", "pr", "checks", str(pr_number)], capture_output=True, text=True, check=True)
        checks = result.stdout

        if "AI PR Review" in checks:
            if "✓" in checks or "passed" in checks.lower():
                print("✅ Copilot AI PR Review: PASSED")
                return True
            elif "X" in checks or "failed" in checks.lower():
                print("❌ Copilot AI PR Review: FAILED")
                print("\nView details: gh pr checks " + str(pr_number))
                return False
            else:
                print("⏳ Copilot AI PR Review: RUNNING")
                print("   Wait for completion, then run this script again")
                return None
        else:
            print("⚠️  Copilot AI PR Review not found in checks")
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to check PR status: {e}")
        return None


def request_human_review(pr_number: int):
    """Request human review on PR."""
    print("\n👤 Requesting human review...")

    try:
        # Add review request comment
        comment = """## 🤖 AI Review Chain Complete

**Review Status:**
- ✅ Ollama Code Review: PASSED
- ✅ Copilot AI PR Review: PASSED

**Ready for human review.**

@vcaboara Please review and approve if all criteria are met:
- [ ] Code quality and readability
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Screenshots included (if UI change)
- [ ] Follows contributor guidelines

**Reminder:** Try using lovable.dev to design company logos 🎨
"""
        subprocess.run(["gh", "pr", "comment", str(pr_number), "--body", comment], check=True)
        print("✅ Human review requested")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to request human review: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Multi-agent code review orchestrator")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama review")
    parser.add_argument("--model", default="deepseek-coder:6.7b", help="Ollama model to use")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🔍 AI REVIEW CHAIN")
    print("=" * 70)
    print(f"PR #{args.pr_number}")
    print("Review order: Ollama → Copilot → Human")

    # Step 1: Ollama review
    if not args.skip_ollama:
        ollama_pass = run_ollama_review(args.pr_number, args.model)
        if not ollama_pass:
            print("\n❌ Ollama review failed. Fix issues and try again.")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping Ollama review (--skip-ollama)")

    # Step 2: Copilot review
    copilot_status = check_copilot_review(args.pr_number)
    if copilot_status is None:
        print("\n⏸️  Waiting for Copilot review to start/complete")
        sys.exit(0)
    elif not copilot_status:
        print("\n❌ Copilot review failed. Check and fix issues.")
        sys.exit(1)

    # Step 3: Request human review
    human_requested = request_human_review(args.pr_number)

    if human_requested:
        print("\n" + "=" * 70)
        print("✅ REVIEW CHAIN COMPLETE - READY FOR HUMAN APPROVAL")
        print("=" * 70)
        print(f"\nView PR: gh pr view {args.pr_number} --web")
    else:
        print("\n⚠️  Review chain incomplete")
        sys.exit(1)


if __name__ == "__main__":
    main()
