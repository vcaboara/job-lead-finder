"""
PR Monitor Service - Continuous PR status checking.

Monitors open PRs for:
- CI status changes (queued → in_progress → completed)
- Merge conflicts
- Review status
- Staleness (no activity in N days)

Runs continuously with configurable check intervals.
"""
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PRMonitor:
    """Monitor PRs for status changes."""

    def __init__(
        self,
        github_token: str,
        repo_owner: str,
        repo_name: str,
        check_interval: int = 300,  # 5 minutes default
        slack_webhook_url: str = None,
    ):
        """
        Initialize PR monitor.

        Args:
            github_token: GitHub API token
            repo_owner: Repository owner
            repo_name: Repository name
            check_interval: Seconds between checks
            slack_webhook_url: Optional Slack webhook URL for notifications
        """
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.check_interval = check_interval
        self.slack_webhook_url = slack_webhook_url
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = "https://api.github.com"
        self._last_check = {}  # PR number -> last status

    def get_open_prs(self) -> List[Dict[str, Any]]:
        """Get all open PRs."""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
        params = {"state": "open", "per_page": 100}

        try:
            response = httpx.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch PRs: {e}")
            return []

    def get_pr_status(self, pr_number: int) -> Dict[str, Any]:
        """Get detailed PR status including CI checks."""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}"

        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            pr = response.json()

            # Get check runs
            checks_url = (
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/commits/{pr['head']['sha']}/check-runs"
            )
            checks_response = httpx.get(checks_url, headers=self.headers, timeout=10)
            checks = checks_response.json().get("check_runs", [])

            return {
                "number": pr_number,
                "title": pr["title"],
                "mergeable": pr.get("mergeable"),
                "mergeable_state": pr.get("mergeable_state"),
                "state": pr["state"],
                "updated_at": pr["updated_at"],
                "checks": [
                    {"name": check["name"], "status": check["status"], "conclusion": check.get("conclusion")}
                    for check in checks
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get PR #{pr_number} status: {e}")
            return {}

    def check_pr_changes(self, pr: Dict[str, Any]) -> List[str]:
        """
        Check for changes in PR status.

        Returns:
            List of notifications
        """
        pr_number = pr["number"]
        current_status = self.get_pr_status(pr_number)

        if not current_status:
            return []

        notifications = []

        # First time seeing this PR
        if pr_number not in self._last_check:
            logger.info(f"Monitoring PR #{pr_number}: {current_status['title']}")
            self._last_check[pr_number] = current_status
            return []

        last_status = self._last_check[pr_number]

        # Check for merge conflicts
        if current_status.get("mergeable") is False and last_status.get("mergeable") is not False:
            notifications.append(f"⚠️ PR #{pr_number} has merge conflicts")

        # Check for resolved conflicts
        if current_status.get("mergeable") is True and last_status.get("mergeable") is False:
            notifications.append(f"✅ PR #{pr_number} conflicts resolved")

        # Check CI status changes
        for check in current_status.get("checks", []):
            last_check = next((c for c in last_status.get("checks", []) if c["name"] == check["name"]), None)

            if not last_check:
                continue

            # Status changed
            if check["status"] != last_check["status"]:
                if check["status"] == "completed":
                    conclusion = check.get("conclusion", "unknown")
                    if conclusion == "success":
                        notifications.append(f"✅ PR #{pr_number} - {check['name']}: passed")
                    elif conclusion == "failure":
                        notifications.append(f"❌ PR #{pr_number} - {check['name']}: failed")
                elif check["status"] == "in_progress":
                    notifications.append(f"🔄 PR #{pr_number} - {check['name']}: running")

        # Update last check
        self._last_check[pr_number] = current_status

        return notifications

    def check_stale_prs(self, days: int = 7) -> List[str]:
        """Find PRs with no activity in N days."""
        notifications = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for pr_number, status in self._last_check.items():
            updated_at = datetime.fromisoformat(status["updated_at"].replace("Z", "+00:00"))

            if updated_at < cutoff:
                notifications.append(f"🕒 PR #{pr_number} stale ({days}+ days): {status['title']}")

        return notifications

    def send_notification(self, message: str, pr_data: Dict[str, Any] = None):
        """
        Send notification via Slack webhook and log to console.

        Args:
            message: Notification message
            pr_data: Optional PR data for enriched Slack messages
        """
        logger.info(f"📢 {message}")

        # Send to Slack if webhook configured
        if self.slack_webhook_url:
            try:
                payload = {"text": message}

                # Add rich formatting if PR data provided
                if pr_data:
                    pr_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/pull/{pr_data['number']}"
                    pr_title = pr_data.get("title", "Unknown")
                    payload = {
                        "text": message,
                        "blocks": [
                            {"type": "section", "text": {"type": "mrkdwn", "text": message}},
                            {
                                "type": "context",
                                "elements": [
                                    {"type": "mrkdwn", "text": f"<{pr_url}|View PR #{pr_data['number']}> • {pr_title}"}
                                ],
                            },
                        ],
                    }

                response = httpx.post(self.slack_webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.debug("Slack notification sent successfully")
            except Exception as e:
                logger.warning(f"Failed to send Slack notification: {e}")

    def run(self):
        """Main monitoring loop."""
        logger.info(f"Starting PR monitor for {self.repo_owner}/{self.repo_name}")
        logger.info(f"Check interval: {self.check_interval}s")

        while True:
            try:
                logger.info("Checking open PRs...")

                # Get all open PRs
                prs = self.get_open_prs()
                logger.info(f"Found {len(prs)} open PRs")

                # Check each PR for changes
                all_notifications = []
                for pr in prs:
                    notifications = self.check_pr_changes(pr)
                    all_notifications.extend(notifications)

                # Check for stale PRs (once per day)
                if int(time.time()) % 86400 < self.check_interval:
                    stale = self.check_stale_prs(days=7)
                    all_notifications.extend(stale)

                # Send notifications
                for notification in all_notifications:
                    self.send_notification(notification)

                # Clean up closed PRs from cache
                open_pr_numbers = {pr["number"] for pr in prs}
                closed = set(self._last_check.keys()) - open_pr_numbers
                for pr_number in closed:
                    logger.info(f"PR #{pr_number} closed, removing from monitor")
                    del self._last_check[pr_number]

                logger.info(f"Next check in {self.check_interval}s")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down PR monitor")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(60)  # Wait 1 minute on error


def main():
    """Run PR monitor."""
    # Configuration from environment
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("REPO_OWNER", "vcaboara")
    repo_name = os.getenv("REPO_NAME", "job-lead-finder")
    check_interval = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 minutes
    slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable required")

    if slack_webhook_url:
        logger.info("Slack notifications enabled")
    else:
        logger.info("Slack notifications disabled (SLACK_WEBHOOK_URL not set)")

    monitor = PRMonitor(
        github_token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        check_interval=check_interval,
        slack_webhook_url=slack_webhook_url,
    )

    monitor.run()


if __name__ == "__main__":
    main()
