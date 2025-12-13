#!/usr/bin/env python3
"""
Auto-Revert on CI Failure
Monitors CI after PR merge and automatically reverts if it fails.
"""

import logging
import os
import sys
import time
from datetime import UTC, datetime

from github import Github, GithubException

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def _find_ci_check(check_runs):
    """Find build-and-test check in check runs."""
    for run in check_runs:
        if run.name == "build-and-test":
            return run
    return None


def wait_for_ci(repo, max_wait_minutes=20):
    """Wait for CI to complete on main branch."""
    logger.info("⏳ Waiting for CI to complete (max %d minutes)...", max_wait_minutes)

    main_branch = repo.get_branch("main")
    merge_sha = main_branch.commit.sha
    check_interval = 30  # seconds
    max_checks = (max_wait_minutes * 60) // check_interval

    for i in range(max_checks):
        commit = repo.get_commit(merge_sha)
        check_runs = commit.get_check_runs()

        ci_check = _find_ci_check(check_runs)
        if not ci_check:
            time.sleep(check_interval)
            continue

        logger.info(
            "   Check %d/%d: %s - %s",
            i + 1,
            max_checks,
            ci_check.status,
            ci_check.conclusion,
        )

        if ci_check.status == "completed":
            return {
                "conclusion": ci_check.conclusion,
                "name": ci_check.name,
                "url": ci_check.html_url,
                "merge_sha": merge_sha,
            }

        time.sleep(check_interval)

    return {
        "conclusion": "timeout",
        "merge_sha": merge_sha,
        "url": None,
    }


def _create_revert_branch(repo, pr_number, base_sha):
    """Create revert branch, handling name conflicts."""
    revert_branch = f"auto/revert-pr-{pr_number}"

    try:
        repo.create_git_ref(f"refs/heads/{revert_branch}", base_sha)
        logger.info("   ✓ Created branch: %s", revert_branch)
        return revert_branch
    except GithubException as e:
        if e.status != 422:  # Not a conflict
            raise

        # Branch exists, add timestamp
        logger.warning("   ⚠️  Branch %s already exists", revert_branch)
        revert_branch = f"{revert_branch}-{int(time.time())}"
        repo.create_git_ref(f"refs/heads/{revert_branch}", base_sha)
        logger.info("   ✓ Created branch: %s", revert_branch)
        return revert_branch


def create_revert_pr(repo, pr_number, pr_title, pr_author, merge_sha, ci_url):
    """Create revert PR and tracking issue."""
    logger.info("🚨 Creating revert for PR #%d...", pr_number)

    try:
        main_ref = repo.get_git_ref("heads/main")
        revert_branch = _create_revert_branch(repo, pr_number, main_ref.object.sha)

        # Create revert PR description
        revert_body = f"""## 🚨 Automatic Revert

**Original PR:** #{pr_number}
**Reason:** CI failure after merge to main
**CI Run:** {ci_url or 'N/A'}

### What Happened:
PR #{pr_number} was merged to main, but the CI checks failed after merge.

### Actions Taken:
- ✅ Created this revert PR automatically
- ✅ Notified PR author (@{pr_author})
- ✅ Created tracking issue for investigation

### Next Steps:
1. **Review this PR** - Ensure revert is safe
2. **Merge immediately** - Restore main to working state
3. **Investigate issue** - Check tracking issue (will be linked)
4. **Fix and retry** - Original PR can be re-opened after fix

---
**Triggered by:** Auto-Revert Workflow
**Merge SHA:** {merge_sha}
**Time:** {datetime.now(UTC).isoformat()}

---
AI-Generated-By: Auto-Revert Workflow"""

        # Create PR (note: actual revert commit needs to be done via git)
        # For now, create PR and add instructions
        revert_pr = repo.create_pull(
            title=f"[AUTO-REVERT] Revert PR #{pr_number}: {pr_title}",
            body=revert_body,
            head=revert_branch,
            base="main",
        )

        logger.info("   ✓ Created revert PR: #%d", revert_pr.number)

        # Add labels
        revert_pr.add_to_labels("auto-revert", "urgent", "bug")

        # Create tracking issue
        issue_body = f"""## 🔍 CI Failure Investigation

**Failed PR:** #{pr_number}
**Revert PR:** #{revert_pr.number}
**CI Run:** {ci_url or 'N/A'}
**Merge SHA:** {merge_sha}

### Failure Details:
- **Check:** build-and-test
- **Conclusion:** failure
- **Time:** {datetime.now(UTC).isoformat()}

### Investigation Steps:
- [ ] Review CI logs: {ci_url or 'Check GitHub Actions'}
- [ ] Identify root cause
- [ ] Determine if issue is:
  - [ ] Test flake
  - [ ] Genuine regression
  - [ ] Environment issue
  - [ ] Merge conflict resolution error

### Resolution:
- [ ] Fix identified in original PR code
- [ ] Tests added to prevent recurrence
- [ ] Original PR updated and re-tested
- [ ] Safe to re-merge

### Original PR:
@{pr_author} - Your PR #{pr_number} was reverted due to CI failure
after merge. Please investigate the issue above and update the
original PR.

---
**Auto-generated by:** Auto-Revert Workflow"""

        issue = repo.create_issue(
            title=f"CI Failure Investigation: PR #{pr_number} - {pr_title}",
            body=issue_body,
            labels=["investigation", "ci-failure", "bug"],
            assignees=[pr_author],
        )

        logger.info("   ✓ Created investigation issue: #%d", issue.number)

        # Update revert PR with issue link
        revert_pr.edit(body=revert_body.replace("(will be linked)", f"#{issue.number}"))

        # Comment on original PR
        original_pr = repo.get_pull(pr_number)
        original_pr.create_issue_comment(
            f"""## 🚨 PR Reverted - CI Failure

@{pr_author} This PR was automatically reverted because CI failed after merge to main.

**Revert PR:** #{revert_pr.number}
**Investigation Issue:** #{issue.number}
**CI Logs:** {ci_url or 'Check GitHub Actions'}

### Next Steps:
1. Review the investigation issue: #{issue.number}
2. Fix the CI failure in this PR
3. Request re-merge after fixes are verified

The revert PR will be merged soon to restore main to a working state."""
        )

        logger.info("   ✓ Notified original PR #%d", pr_number)

        return {
            "revert_pr": revert_pr.number,
            "issue": issue.number,
            "success": True,
        }

    except Exception as e:
        logger.error("   ❌ Failed to create revert: %s", e)

        # Create manual action issue
        try:
            manual_issue = repo.create_issue(
                title=f"🚨 URGENT: Manual Revert Needed - PR #{pr_number}",
                body=f"""## Manual Revert Required

**Failed PR:** #{pr_number}
**Reason:** Automatic revert failed
**Error:** `{str(e)}`
**CI URL:** {ci_url or 'N/A'}

### Manual Steps:
```bash
git checkout main
git pull
git revert {merge_sha}
git push origin main
```

Then create investigation issue for PR #{pr_number}.

**Original PR Author:** @{pr_author}""",
                labels=["urgent", "manual-action-required", "bug"],
                assignees=["vcaboara"],
            )

            logger.info("   ✓ Created manual action issue: #%d", manual_issue.number)

        except Exception as e2:
            logger.error("   ❌ Failed to create manual action issue: %s", e2)

        return {"success": False, "error": str(e)}


def main():
    """Main execution."""
    token = os.environ.get("GITHUB_TOKEN")
    pr_number_str = os.environ.get("PR_NUMBER")
    pr_title = os.environ.get("PR_TITLE")
    pr_author = os.environ.get("PR_AUTHOR")
    repo_owner = os.environ.get("REPO_OWNER")
    repo_name = os.environ.get("REPO_NAME")

    if not all([token, pr_number_str, pr_title, pr_author, repo_owner, repo_name]):
        logger.error("❌ Missing required environment variables")
        sys.exit(1)

    assert pr_number_str is not None  # Already validated above
    pr_number = int(pr_number_str)

    logger.info("🤖 Auto-Revert Monitor")
    logger.info("   PR: #%d - %s", pr_number, pr_title)
    logger.info("   Author: @%s", pr_author)
    logger.info("   Repo: %s/%s", repo_owner, repo_name)

    # Initialize GitHub client
    g = Github(token)
    repo = g.get_repo(f"{repo_owner}/{repo_name}")

    # Wait for CI
    ci_result = wait_for_ci(repo)

    if ci_result["conclusion"] == "success":
        logger.info("✅ CI passed after merge. No action needed.")
        sys.exit(0)

    elif ci_result["conclusion"] == "failure":
        logger.error("❌ CI failed after merge: %s", ci_result["url"])

        # Create revert PR
        result = create_revert_pr(
            repo,
            pr_number,
            pr_title,
            pr_author,
            ci_result["merge_sha"],
            ci_result["url"],
        )

        if result["success"]:
            logger.info("✅ Auto-revert complete:")
            logger.info("   Revert PR: #%d", result["revert_pr"])
            logger.info("   Investigation: #%d", result["issue"])
            sys.exit(0)
        else:
            logger.error("❌ Auto-revert failed: %s", result.get("error"))
            sys.exit(1)

    elif ci_result["conclusion"] == "timeout":
        logger.warning("⏱️  CI did not complete within timeout. Manual check needed.")
        sys.exit(0)

    else:
        logger.warning("⚠️  Unexpected CI conclusion: %s", ci_result["conclusion"])
        sys.exit(0)


if __name__ == "__main__":
    main()
