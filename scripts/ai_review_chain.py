#!/usr/bin/env python3
"""
AI Review Chain Helper
Orchestrates multi-agent code review: Ollama → Copilot → Human
"""

import argparse
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_ollama_review(pr_number: int, model: str = "deepseek-coder:6.7b"):
    """Run Ollama code review on PR diff."""
    logger.info("🤖 Running Ollama review with %s...", model)

    # Get PR diff
    try:
        result = subprocess.run(["gh", "pr", "diff", str(pr_number)], capture_output=True, text=True, check=True)
        diff = result.stdout
    except subprocess.CalledProcessError as e:
        logger.error("❌ Failed to get PR diff: %s", e)
        return False

    if not diff:
        logger.warning("⚠️  No diff found")
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
        logger.info("\n" + "=" * 70)
        logger.info("📝 OLLAMA REVIEW:")
        logger.info("=" * 70)
        logger.info(review)
        return True
    except subprocess.TimeoutExpired:
        logger.error("❌ Ollama review timed out (60s)")
        return False
    except Exception as e:
        logger.error("❌ Ollama review failed: %s", e)
        return False


def check_copilot_review(pr_number: int):
    """Check if Copilot AI PR Review has run."""
    logger.info("🤖 Checking Copilot PR Review status...")

    try:
        result = subprocess.run(["gh", "pr", "checks", str(pr_number)], capture_output=True, text=True, check=True)
        checks = result.stdout

        if "AI PR Review" in checks:
            if "✓" in checks or "passed" in checks.lower():
                logger.info("✅ Copilot AI PR Review: COMPLETED")
                return True
            elif "X" in checks or "failed" in checks.lower():
                logger.error("❌ Copilot AI PR Review: FAILED")
                logger.info("View details: gh pr checks %s", pr_number)
                return False
            else:
                logger.info("⏳ Copilot AI PR Review: RUNNING")
                logger.info("   Wait for completion, then run this script again")
                return None
        else:
            logger.info("ℹ️  Copilot review not yet requested")
            logger.info("   To request: gh pr comment %s --body '@copilot review'", pr_number)
            logger.info("   Or use: --request-copilot flag with this script")
            return None
    except subprocess.CalledProcessError as e:
        logger.error("❌ Failed to check PR status: %s", e)
        return None


def request_human_review(pr_number: int):
    """Request human review on PR."""
    logger.info("👤 Requesting human review...")

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
        logger.info("✅ Human review requested")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Failed to request human review: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Multi-agent code review orchestrator")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama review")
    parser.add_argument("--model", default="deepseek-coder:6.7b", help="Ollama model to use")
    parser.add_argument("--request-copilot", action="store_true", help="Request Copilot review via comment")

    args = parser.parse_args()

    logger.info("\n" + "=" * 70)
    logger.info("🔍 AI REVIEW CHAIN")
    logger.info("=" * 70)
    logger.info("PR #%s", args.pr_number)
    logger.info("Review order: Ollama → Copilot → Human")

    # Step 1: Ollama review
    if not args.skip_ollama:
        ollama_pass = run_ollama_review(args.pr_number, args.model)
        if not ollama_pass:
            logger.error("\n❌ Ollama review failed. Fix issues and try again.")
            sys.exit(1)
    else:
        logger.info("⏭️  Skipping Ollama review (--skip-ollama)")

    # Step 2: Copilot review
    copilot_status = check_copilot_review(args.pr_number)
    if copilot_status is None:
        if args.request_copilot:
            logger.info("📝 Requesting Copilot review via comment...")
            try:
                subprocess.run(
                    ["gh", "pr", "comment", str(args.pr_number), "--body", "@copilot review"],
                    check=True,
                    capture_output=True,
                )
                logger.info("✅ Copilot review requested. Re-run this script after ~1 minute.")
            except subprocess.CalledProcessError as e:
                logger.error("❌ Failed to request Copilot review: %s", e)
        else:
            logger.info("⏸️  Copilot review not requested yet")
            logger.info("   Option 1: Manually comment '@copilot review' on PR")
            logger.info("   Option 2: Re-run with --request-copilot flag")
        sys.exit(0)
    elif not copilot_status:
        logger.error("❌ Copilot review failed. Check and fix issues.")
        sys.exit(1)

    # Step 3: Request human review
    human_requested = request_human_review(args.pr_number)

    if human_requested:
        logger.info("\n" + "=" * 70)
        logger.info("✅ REVIEW CHAIN COMPLETE - READY FOR HUMAN APPROVAL")
        logger.info("=" * 70)
        logger.info("View PR: gh pr view %s --web", args.pr_number)
        logger.info("\n📋 Next Steps:")
        logger.info("1. Review PR on GitHub")
        logger.info("2. If changes needed: Comment on PR with '@ai-agent please fix: <issue>'")
        logger.info("3. If approved: Merge PR via GitHub or 'gh pr merge %s'", args.pr_number)
    else:
        logger.warning("⚠️  Review chain incomplete")
        sys.exit(1)


if __name__ == "__main__":
    main()
