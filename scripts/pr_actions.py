"""
PR Monitor Actions - Automated responses to PR events.

This module defines actions that can be triggered automatically
or notify humans/AI assistants to take action.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PRAction:
    """Base class for PR actions."""

    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Execute the action. Returns True if successful."""
        raise NotImplementedError


class CommentOnPRAction(PRAction):
    """Add a comment to a PR."""

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Post a comment on the PR."""
        import httpx

        message = context.get("message", "Automated notification")

        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{pr_number}/comments"
        headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json"}

        try:
            response = httpx.post(url, headers=headers, json={"body": message}, timeout=10)
            response.raise_for_status()
            logger.info("Posted comment on PR #%d", pr_number)
            return True
        except Exception as e:
            logger.error("Failed to comment on PR #%d: %s", pr_number, e)
            return False


class MergePRAction(PRAction):
    """Auto-merge a PR when conditions are met."""

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Merge the PR."""
        import httpx

        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/merge"
        headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json"}

        merge_method = context.get("merge_method", "squash")
        commit_message = context.get("commit_message", "Auto-merged by PR monitor")

        try:
            response = httpx.put(
                url, headers=headers, json={"merge_method": merge_method, "commit_title": commit_message}, timeout=10
            )
            response.raise_for_status()
            logger.info("Merged PR #%d", pr_number)
            return True
        except Exception as e:
            logger.error("Failed to merge PR #%d: %s", pr_number, e)
            return False


class NotifySlackAction(PRAction):
    """Send notification to Slack."""

    def __init__(self, github_token: str, repo_owner: str, repo_name: str, webhook_url: str):
        super().__init__(github_token, repo_owner, repo_name)
        self.webhook_url = webhook_url

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Send Slack notification."""
        import httpx

        message = context.get("message", "PR update")
        pr_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/pull/{pr_number}"

        payload = {"text": f"{message}\n<{pr_url}|PR #{pr_number}>"}

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent Slack notification for PR #%d", pr_number)
            return True
        except Exception as e:
            logger.error("Failed to send Slack notification: %s", e)
            return False


class TriggerCopilotAction(PRAction):
    """Trigger GitHub Copilot to review/fix PR."""

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Post a comment that triggers Copilot."""
        action_type = context.get("action_type", "review")

        if action_type == "review":
            message = "@copilot review this PR"
        elif action_type == "fix_conflicts":
            message = "@copilot please resolve the merge conflicts in this PR"
        elif action_type == "fix_tests":
            message = "@copilot the tests are failing, please investigate and fix"
        else:
            message = f"@copilot {context.get('custom_message', 'help with this PR')}"

        comment_action = CommentOnPRAction(self.github_token, self.repo_owner, self.repo_name)

        return comment_action.execute(pr_number, {"message": message})


class TriggerGeminiAction(PRAction):
    """Create an issue for Gemini to handle."""

    def execute(self, pr_number: int, context: Dict[str, Any]) -> bool:
        """Create an issue that autonomous execution will pick up."""
        import httpx

        action_type = context.get("action_type", "investigate")
        pr_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/pull/{pr_number}"

        if action_type == "fix_conflicts":
            title = f"[AUTO] Resolve merge conflicts in PR #{pr_number}"
            body = f"""PR #{pr_number} has merge conflicts that need resolution.

PR: {pr_url}

**Task:**
1. Checkout the PR branch
2. Rebase onto main
3. Resolve conflicts
4. Push the updated branch

This issue was created automatically by the PR monitor."""

        elif action_type == "investigate_failure":
            title = f"[AUTO] Investigate CI failure in PR #{pr_number}"
            body = f"""CI checks failed for PR #{pr_number}.

PR: {pr_url}

**Task:**
1. Review the CI logs
2. Identify the root cause
3. Fix the issue or report findings

This issue was created automatically by the PR monitor."""

        else:
            title = f"[AUTO] Review PR #{pr_number}"
            body = f"""PR #{pr_number} needs attention.

PR: {pr_url}

{context.get('description', 'Please review and take appropriate action.')}

This issue was created automatically by the PR monitor."""

        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
        headers = {"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json"}

        try:
            response = httpx.post(
                url,
                headers=headers,
                json={"title": title, "body": body, "labels": ["automation", "pr-monitor"]},
                timeout=10,
            )
            response.raise_for_status()
            issue = response.json()
            logger.info("Created issue #%d for PR #%d", issue["number"], pr_number)
            return True
        except Exception as e:
            logger.error("Failed to create issue for PR #%d: %s", pr_number, e)
            return False


# Action registry - configure which actions to take on which events
AUTOMATION_RULES = {
    "ci_failed": [
        # Human notification first
        {"action": "comment", "message": "⚠️ CI checks failed. Please review the logs."},
        # Optional: Auto-trigger investigation after 1 hour
        # {"action": "trigger_gemini", "action_type": "investigate_failure", "delay": 3600},
    ],
    "ci_passed_and_mergeable": [
        # For version bump PRs, auto-merge
        {"action": "merge", "condition": "is_version_bump", "merge_method": "squash"},
        # For other PRs, just notify
        {"action": "comment", "message": "✅ All checks passed! Ready to merge."},
    ],
    "merge_conflicts": [
        # Notify immediately
        {"action": "comment", "message": "⚠️ This PR has merge conflicts that need resolution."},
        # Trigger Copilot after 5 minutes if conflicts still exist
        {"action": "trigger_copilot", "action_type": "fix_conflicts", "delay": 300},
    ],
    "stale_pr": [
        {"action": "comment", "message": "🕒 This PR has been inactive for 7+ days. Is it still needed?"},
    ],
}
