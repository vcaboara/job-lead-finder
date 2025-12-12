# PR Monitor Service

Continuous monitoring of open PRs for status changes.

## Features

- **CI Status Monitoring**: Detects when checks start, complete, pass, or fail
- **Merge Conflict Detection**: Alerts when conflicts appear or are resolved
- **Stale PR Detection**: Flags PRs with no activity in 7+ days
- **Configurable Interval**: Check every 5 minutes (default) or customize

## Running

### Docker Compose (Recommended)

```bash
# Start the monitor
docker compose up pr-monitor -d

# View logs
docker compose logs -f pr-monitor

# Stop
docker compose stop pr-monitor
```

### Standalone Docker

```bash
# Build
docker build -f Dockerfile.pr-monitor -t pr-monitor .

# Run
docker run --rm \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e REPO_OWNER=vcaboara \
  -e REPO_NAME=job-lead-finder \
  -e CHECK_INTERVAL=300 \
  pr-monitor
```

### Local Python

```bash
# Install dependency
pip install httpx

# Run
export GITHUB_TOKEN=your_token
export CHECK_INTERVAL=300  # 5 minutes
python scripts/pr_monitor.py
```

## Configuration

Environment variables:

- **GITHUB_TOKEN** (required): GitHub personal access token with `repo` scope
- **REPO_OWNER** (default: vcaboara): Repository owner
- **REPO_NAME** (default: job-lead-finder): Repository name
- **CHECK_INTERVAL** (default: 300): Seconds between checks

## Notifications

Currently logs to stdout. Extend `PRMonitor.send_notification()` to add:
- Slack webhooks
- Discord webhooks
- Email alerts
- GitHub comments
- Custom integrations

## Example Output

```
2025-12-12 15:30:00 - INFO - Starting PR monitor for vcaboara/job-lead-finder
2025-12-12 15:30:00 - INFO - Check interval: 300s
2025-12-12 15:30:01 - INFO - Found 3 open PRs
2025-12-12 15:30:02 - INFO - 📢 🔄 PR #119 - build-and-test: running
2025-12-12 15:35:02 - INFO - 📢 ✅ PR #119 - build-and-test: passed
2025-12-12 15:35:03 - INFO - 📢 ✅ PR #119 conflicts resolved
2025-12-12 15:40:02 - INFO - 📢 🕒 PR #117 stale (7+ days): [AI] fix: Version bump workflow
```

## Advantages Over Scheduled Workflows

| Feature | PR Monitor Service | GitHub Actions Schedule |
|---------|-------------------|------------------------|
| Check frequency | Every 5 minutes | Every 2 hours (free tier limit) |
| Real-time updates | Yes | No |
| Continuous running | Yes | Discrete runs |
| State persistence | In-memory cache | Must recreate each run |
| Cost | Docker container | GitHub Actions minutes |
| Customization | Full control | Limited by Actions API |

## Adding Custom Checks

Edit `scripts/pr_monitor.py`:

```python
def check_pr_changes(self, pr: Dict[str, Any]) -> List[str]:
    # ... existing checks ...

    # Add your custom check
    if pr["draft"] == False and last_status["draft"] == True:
        notifications.append(f"📝 PR #{pr_number} marked ready for review")

    return notifications
```

## Integration Ideas

### Slack Notifications

```python
def send_notification(self, message: str):
    import httpx
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        httpx.post(webhook_url, json={"text": message})
    logger.info(f"📢 {message}")
```

### Auto-merge on Success

```python
def check_pr_changes(self, pr: Dict[str, Any]) -> List[str]:
    # ... existing checks ...

    # Auto-merge if all checks pass
    all_passed = all(
        c["status"] == "completed" and c["conclusion"] == "success"
        for c in current_status.get("checks", [])
    )

    if all_passed and current_status.get("mergeable") == True:
        self.merge_pr(pr_number)
        notifications.append(f"✅ PR #{pr_number} auto-merged")

    return notifications
```

## Monitoring the Monitor

Health check endpoint at container level:
```bash
docker inspect pr-monitor --format='{{.State.Health.Status}}'
```

Add to compose for restart on failure:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 3s
  retries: 3
restart: unless-stopped
```
