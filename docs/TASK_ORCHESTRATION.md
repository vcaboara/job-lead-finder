# Task Orchestration Configuration

How the different AI systems work together for autonomous development.

## Task Sources (Priority Order)

1. **Critical/Blocking** → PR Monitor alerts
2. **Planned Work** → docs/TODO.md
3. **Structured Projects** → Vibe Kanban
4. **Bug Reports** → GitHub Issues with [AUTO]

## Workflow Integration

### 1. PR Monitor → Task Creation

When PR monitor detects issues, it can create tasks for other systems:

```python
# In pr_monitor.py
def on_ci_failure(pr_number):
    # Option 1: Add to TODO.md
    append_to_todo(f"- [ ] Fix CI failure in PR #{pr_number}")

    # Option 2: Create GitHub issue for autonomous executor
    create_issue(
        title=f"[AUTO] Investigate CI failure PR #{pr_number}",
        labels=["automation", "bug"]
    )

    # Option 3: Add to Kanban board
    kanban_api.create_task({
        "title": f"Fix CI in PR #{pr_number}",
        "priority": "high",
        "assignee": "copilot"
    })
```

### 2. Claude Task Master → PR Monitor

Task Master creates PRs, PR Monitor watches them:

```
1. Cline reads docs/TODO.md
2. Cline implements feature X
3. Cline creates PR #125
4. PR Monitor detects PR #125
5. PR Monitor watches CI status
6. On failure → alerts or triggers fix
```

### 3. Complete Autonomous Loop

```
docs/TODO.md
  → Cline implements
    → Creates PR
      → PR Monitor watches
        → CI fails
          → PR Monitor creates issue
            → Autonomous Executor fixes
              → Updates PR
                → PR Monitor detects fix
                  → CI passes
                    → PR Monitor auto-merges
                      → Done!
```

## Configuration Files

### `.claude/settings.json` (Task Master)
- Defines what Cline can do autonomously
- Connects to Kanban and TODO sources
- Sets approval requirements

### `.github/workflows/autonomous-execution.yml`
- Runs every 2 hours
- Picks up [AUTO] issues
- Uses Gemini/Anthropic/OpenAI

### `scripts/pr_monitor.py` + `scripts/pr_actions.py`
- Runs continuously (5 min intervals)
- Monitors PR status
- Creates tasks when needed

### Environment Variables

```bash
# PR Monitor
GITHUB_TOKEN=ghp_xxx
ENABLE_AUTO_MERGE=true
ENABLE_COPILOT_TRIGGERS=true
ENABLE_GEMINI_TASKS=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxx

# Autonomous Executor
GEMINI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx

# Task Master (Cline)
# Configured in VS Code settings
```

## Example: Full Autonomous Feature

Let's say you want to add a new job provider:

### Step 1: Add to TODO
```markdown
- [ ] Create provider for WeWorkRemotely RSS feed
```

### Step 2: Cline Picks It Up
- Reads TODO.md
- Understands task from context
- Generates code in `src/app/providers/weworkremotely.py`
- Writes tests
- Creates PR #126

### Step 3: PR Monitor Watches
```
PR #126 created
→ Monitor: "New PR detected, watching..."
→ CI starts
→ Monitor: "🔄 CI running on PR #126"
→ CI passes
→ Monitor: "✅ CI passed on PR #126"
→ Monitor: "All checks passed! Ready to merge."
```

### Step 4: Merge Decision
```python
# In pr_actions.py
if pr_title.startswith("[AI]") and all_checks_passed:
    # Auto-merge AI-generated PRs that pass CI
    merge_pr(pr_number, method="squash")
else:
    # Notify human for review
    notify_slack(f"PR #{pr_number} ready for review")
```

### Step 5: Post-Merge
```
PR merged
→ Version bump workflow creates PR #127
→ PR Monitor detects version bump PR
→ Auto-merges (trusted automation)
→ Done!
```

## Adding Task Direction to PR Monitor

Currently PR Monitor is **reactive** (responds to events). To make it **directive** (creates work), extend it:

```python
# In pr_monitor.py
class TaskDirector:
    """Convert PR events into actionable tasks."""

    def on_stale_pr(self, pr_number: int):
        # Check if PR is blocked on something
        blockers = self.analyze_pr_blockers(pr_number)

        for blocker in blockers:
            if blocker == "merge_conflicts":
                # Add to TODO for Cline
                self.add_todo(f"Resolve conflicts in PR #{pr_number}")

            elif blocker == "failing_tests":
                # Create issue for autonomous executor
                self.create_auto_issue(
                    f"Fix failing tests in PR #{pr_number}",
                    priority="high"
                )

            elif blocker == "needs_review":
                # Just notify human
                self.notify_slack(f"PR #{pr_number} needs review")
```

Want me to implement this integration?
