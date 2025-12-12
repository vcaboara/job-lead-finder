# Autonomous Development Guide

## Overview

The repository is configured for fully hands-free autonomous development using Cline (Claude-dev extension). Once enabled, AI agents work through tasks from TODO.md automatically with no human intervention required.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Autonomous Dev Cycle                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   TODO.md (Task Queue)   │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  autodev_loop.ps1        │
                    │  (5-min polling)         │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  .ai-tasks/current-task  │
                    │  (Task handoff)          │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Cline Extension         │
                    │  (Autonomous execution)  │
                    └──────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
        ┌────────────────────┐      ┌────────────────────┐
        │  Memory Bank       │      │  MCP Services      │
        │  - architecture    │      │  - Vibe Check      │
        │  - technical       │      │  - Vibe Kanban     │
        │  - tasks_plan      │      │  - Memory Bank     │
        │  - active_context  │      └────────────────────┘
        └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │  Implementation    │
        │  - Write code      │
        │  - Write tests     │
        │  - Run validation  │
        └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │  Auto-Commit       │
        │  (autoCommit: true)│
        └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │  Auto-PR           │
        │  (autoPR: true)    │
        │  [AI] tag          │
        └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │  Version Bump PR   │
        │  (auto-created)    │
        │  (auto-merged)     │
        └────────────────────┘
```

## Configuration

### `.claude/settings.json`

```json
{
  "autonomousMode": {
    "enabled": true,
    "requireApproval": {
      "fileCreation": false,       // ✅ No approval
      "fileModification": false,   // ✅ No approval
      "terminalCommands": false,   // ✅ No approval (HANDS-FREE)
      "apiCalls": false            // ✅ No approval
    },
    "maxIterations": 50,
    "autoCommit": true,            // ✅ Auto-commit
    "autoPR": true                 // ✅ Auto-PR creation
  }
}
```

**Key Settings:**
- `terminalCommands: false` - Allows running tests, git commands, etc. without approval
- `autoCommit: true` - Commits changes automatically when task completes
- `autoPR: true` - Creates PR automatically with [AI] tag
- `maxIterations: 50` - Up to 50 actions per task

## Workflow

### 1. Task Definition (TODO.md)

```markdown
## Immediate (Do Now)
- [ ] Implement feature X
- [ ] Fix bug Y
```

### 2. Task Pickup (autodev_loop.ps1)

Runs every 5 minutes:
- Checks TODO.md for uncompleted tasks (`- [ ]`)
- Verifies no active auto/* branches (prevents conflicts)
- Writes task to `.ai-tasks/current-task.md`
- Cline picks up and executes

### 3. Autonomous Execution (Cline)

**Pre-Task:**
1. Read Memory Bank files
2. Check AI resource availability (AI Monitor)
3. Create feature branch: `auto/track-{id}-{task}`

**During Task:**
4. Follow coding standards from `memory/docs/technical.md`
5. Write implementation with tests
6. Run `pytest` before committing
7. Update `memory/tasks/active_context.md` with progress

**Post-Task:**
8. Validate with Vibe Check MCP
9. Run full test suite: `pytest -n auto`
10. Update `memory/tasks/tasks_plan.md` (mark completed)
11. **Auto-commit** with conventional commit format
12. **Auto-create PR** with [AI] tag and checklist

### 4. Version Bump & Merge

- Version bump workflow triggers on PR merge
- Auto-creates version bump PR
- Auto-merges when CI passes
- Auto-deletes branch

## Starting Autonomous Development

### Option 1: Manual Trigger (First Task)

```powershell
# Start Cline on the next TODO task
.\scripts\start_cline.ps1

# Open Cline in VS Code
# Ctrl+Shift+P → "Cline: Open"
# Paste the generated prompt
```

### Option 2: Continuous Loop (Fully Hands-Free)

```powershell
# Start the continuous monitoring loop
.\scripts\autodev_loop.ps1

# Or run in background
Start-Job -ScriptBlock { .\scripts\autodev_loop.ps1 }
```

### Option 3: VS Code Integration (Recommended)

Cline automatically monitors `.ai-tasks/current-task.md` and picks up tasks when they appear.

## Safety & Controls

### Branch Protection
- Direct pushes to `main` blocked
- All changes go through PRs
- CI must pass before merge
- Pre-commit hooks enforce code quality

### Resource Monitoring
- AI Monitor tracks API quota usage
- Gemini: 20 calls/day (free tier)
- Copilot: 1500 calls/month (premium)
- Auto-stops on quota exhaustion

### Destructive Operations
Always require approval:
- File deletion
- Branch deletion
- Force push

### Validation Gates
Every commit goes through:
- Black (code formatting)
- Flake8 (linting)
- isort (import sorting)
- Pytest (tests must pass)
- Vibe Check MCP (code validation)

## Monitoring Dashboards

### AI Resource Monitor
- **URL:** http://localhost:9000
- **Purpose:** Track AI API usage, get recommendations
- **Alerts:** Warns when quota is low

### Vibe Check MCP
- **URL:** http://localhost:3000
- **Purpose:** Code validation, quality checks
- **Integration:** Pre-commit and pre-PR validation

### Vibe Kanban
- **URL:** http://localhost:3001
- **Purpose:** Task tracking, status updates
- **Sync:** Auto-updates from TODO.md and PR status

### PR Monitor
- **Service:** `scripts/pr_monitor.py` (Docker)
- **Interval:** 5 minutes
- **Actions:** Track CI, detect conflicts, trigger AI assistance

## Task Format

### TODO.md Structure

```markdown
# TODO - Active Development Tasks

## Immediate (Do Now)
- [ ] High priority task (picked up first)
- [x] Completed task

## High Priority (This Week)
- [ ] Important feature
- [ ] Critical bug fix

## Medium Priority (Next Sprint)
- [ ] Enhancement
- [ ] Refactoring

## Low Priority (Future)
- [ ] Nice-to-have feature
```

### Task Prompt Template

```markdown
**Task:** [Brief description]

**Priority:** [Immediate/High/Medium/Low]

**Instructions:**
1. Read Memory Bank files
2. Implement with tests
3. Follow .claude/settings.json workflow
4. Auto-commit and auto-PR when complete

**Expected Outcome:**
- [Specific deliverables]
- Memory Bank updated
```

## Memory Bank Integration

Cline reads and updates these files automatically:

**Read on Task Start:**
- `memory/docs/architecture.md` - System design
- `memory/docs/technical.md` - Tech stack, standards
- `memory/docs/product_requirement_docs.md` - Requirements
- `memory/tasks/tasks_plan.md` - Overall plan
- `memory/tasks/active_context.md` - Current state

**Update on Task Complete:**
- `memory/tasks/tasks_plan.md` - Mark task complete
- `memory/tasks/active_context.md` - Document changes
- `memory/docs/lessons-learned.md` - Capture learnings

## Commit Messages

All commits follow Conventional Commits with [AI] tag:

```
[AI] feat: Add new feature
[AI] fix: Resolve bug in module X
[AI] docs: Update documentation
[AI] test: Add test coverage for Y
[AI] refactor: Improve code structure
```

Footer includes AI attribution:
```
---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```

## Pull Request Template

Auto-created PRs include:
- Description of changes
- Checklist of completed items
- Test results
- Memory Bank updates
- Next steps

## Troubleshooting

### Cline Not Picking Up Tasks

**Check:**
1. Is `.ai-tasks/current-task.md` present?
2. Is Cline extension installed and running?
3. Check VS Code → Output → Cline for errors

**Fix:**
```powershell
# Regenerate task file
.\scripts\start_cline.ps1
```

### Task Stuck in Progress

**Check:**
1. Is there an active `auto/*` branch?
   ```powershell
   git branch | Select-String "auto/"
   ```
2. Check Cline output for errors

**Fix:**
```powershell
# Clean up stuck branch
git checkout main
git branch -D auto/stuck-branch
```

### Auto-Merge Not Triggering

**Check:**
1. Is auto-merge enabled in repository settings?
2. Is VERSION_BUMP_PAT secret configured?
3. Check CI status (must pass)

**Fix:**
```powershell
# Manually enable auto-merge
gh pr merge <PR-NUMBER> --auto --squash
```

### Quota Exhausted

**Check AI Monitor:**
- http://localhost:9000

**Strategy:**
1. Use local Ollama for lower-priority tasks
2. Reserve Gemini for documentation (free tier)
3. Use Copilot for high-value implementation

## Best Practices

### Task Writing
- ✅ Be specific and actionable
- ✅ Include acceptance criteria
- ✅ Reference relevant Memory Bank files
- ❌ Don't be vague ("improve code")
- ❌ Don't combine multiple unrelated tasks

### Memory Bank Hygiene
- Review `active_context.md` weekly
- Archive completed tracks in `tasks_plan.md`
- Keep `lessons-learned.md` updated
- Don't let context files grow too large

### Monitoring
- Check AI Monitor daily for quota
- Review PR monitor logs weekly
- Verify auto-merge working monthly

## Future Enhancements

Planned improvements:
- Slack notifications for task completion
- Web dashboard for task queue
- Multi-agent task allocation
- Automatic task breakdown for large tasks
- Learning from past task patterns

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Memory Bank files for context
3. Check dashboard status (AI Monitor, Vibe Check)
4. Manually intervene if needed (Cline supports manual mode)

---

**Status:** ✅ Fully operational and hands-free
**Last Updated:** December 12, 2025
