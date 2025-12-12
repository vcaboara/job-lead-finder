# Monitoring Autonomous Development - Quick Reference

## Real-Time Monitoring Options

### 1. **Cline Extension (Primary View)**

**What:** Live view of AI agent's actions in VS Code

**How to Access:**
```
Open VS Code → Sidebar → Cline icon
Or: Ctrl+Shift+P → "Cline: Open"
```

**What You'll See:**
- Current task being worked on
- Real-time thought process
- Commands being executed
- File changes being made
- Test results
- Error messages

**Status Indicators:**
- 🟢 Green: Task in progress
- 🟡 Yellow: Waiting for approval (if enabled)
- 🔴 Red: Error encountered
- ✅ Check: Task complete

---

### 2. **Memory Bank (Current State)**

**What:** Written record of what's happening

**Files to Watch:**
```powershell
# Active context (current work)
code memory\tasks\active_context.md

# Task plan (overall progress)
code memory\tasks\tasks_plan.md

# TODO list (next tasks)
code TODO.md
```

**Update Frequency:**
- `active_context.md`: Updated during task execution
- `tasks_plan.md`: Updated on task completion
- `TODO.md`: Updated when tasks start/finish

---

### 3. **Git Activity (File System)**

**What:** See branches, commits, and PRs being created

**Commands:**
```powershell
# Watch for new branches (auto/* pattern)
git branch | Select-String "auto/"

# See recent commits
git log --oneline -10

# Watch open PRs
gh pr list --state open

# Watch PR updates in real-time
gh pr list --state open --json number,title,statusCheckRollup
```

**What to Look For:**
- New branches: `auto/track-{id}-{task-name}`
- Commits with `[AI]` tag
- PRs with auto-merge enabled

---

### 4. **Dashboard - AI Monitor**

**What:** Resource usage and recommendations

**URL:** http://localhost:9000

**Shows:**
- Copilot usage (1500/month limit)
- Gemini usage (20/day limit)
- Local Ollama status
- GPU utilization
- Recommendations for which AI to use

**Check When:**
- Starting a new work session
- Planning task priorities
- Investigating quota issues

---

### 5. **Dashboard - Vibe Kanban**

**What:** Task board synchronized with TODO.md

**URL:** http://localhost:3001

**Shows:**
- Tasks in progress
- Completed tasks
- Blocked tasks
- Task assignments to AI agents

**Current Status:** ⚠️ Service stopped (first task in TODO.md is to fix this)

---

### 6. **Dashboard - Vibe Check MCP**

**What:** Code quality validation results

**URL:** http://localhost:3000

**Shows:**
- Code validation results
- Pre-commit check status
- Code quality scores
- Suggestions for improvement

---

### 7. **PR Monitor Logs**

**What:** Automated PR tracking and actions

**View Logs:**
```powershell
# Docker container logs
docker logs pr-monitor -f

# Or check log files
Get-Content logs\pr_monitor.log -Tail 50 -Wait
```

**What You'll See:**
- PR status changes
- CI status updates
- Merge conflict detection
- Auto-merge triggers

---

## Quick Monitoring Commands

### One-Liner Status Check

```powershell
# Complete status in one command
@{
    'Active Branches' = (git branch | Select-String "auto/" | Measure-Object).Count
    'Open PRs' = (gh pr list --state open --json number | ConvertFrom-Json).Count
    'TODO Tasks' = (Get-Content TODO.md | Select-String "- \[ \]" | Measure-Object).Count
    'Services' = @{
        'AI Monitor' = (Test-NetConnection localhost -Port 9000 -WarningAction SilentlyContinue).TcpTestSucceeded
        'Vibe Check' = (Test-NetConnection localhost -Port 3000 -WarningAction SilentlyContinue).TcpTestSucceeded
        'Vibe Kanban' = (Test-NetConnection localhost -Port 3001 -WarningAction SilentlyContinue).TcpTestSucceeded
    }
}
```

### Watch Mode Commands

```powershell
# Watch TODO.md for changes
Get-Content TODO.md -Wait

# Watch Memory Bank active context
Get-Content memory\tasks\active_context.md -Wait

# Watch Git branches
while ($true) {
    Clear-Host
    git branch | Select-String "auto/"
    Start-Sleep 10
}

# Watch open PRs
while ($true) {
    Clear-Host
    gh pr list --state open
    Start-Sleep 30
}
```

---

## Notification Setup

### Terminal Notifications

Add to your PowerShell profile:
```powershell
# Watch for new PRs and notify
function Watch-AutoDev {
    $lastPRCount = 0
    while ($true) {
        $currentPRs = (gh pr list --state open --json number | ConvertFrom-Json).Count
        if ($currentPRs -gt $lastPRCount) {
            Write-Host "`n🚨 NEW PR CREATED!" -ForegroundColor Green
            gh pr list --state open --limit 1
        }
        $lastPRCount = $currentPRs
        Start-Sleep 60
    }
}
```

### VS Code Notifications

Cline will show notifications in VS Code when:
- Task completes
- Error occurs
- Approval needed (if configured)

---

## Monitoring Workflows

### Morning Check (5 minutes)

```powershell
# 1. Check AI quota
Start-Process "http://localhost:9000"

# 2. Review overnight progress
git log --since="yesterday" --oneline

# 3. Check open PRs
gh pr list --state open

# 4. Review TODO status
code TODO.md

# 5. Check Memory Bank for blockers
code memory\tasks\active_context.md
```

### Active Development Watch (Continuous)

**Terminal 1: Cline Monitor**
```
Open VS Code → Cline panel
```

**Terminal 2: Git Activity**
```powershell
# Watch git activity
while ($true) {
    Clear-Host
    Write-Host "Active Branches:" -ForegroundColor Cyan
    git branch | Select-String "auto/"
    Write-Host "`nRecent Commits:" -ForegroundColor Cyan
    git log --oneline -5
    Write-Host "`nOpen PRs:" -ForegroundColor Cyan
    gh pr list --state open
    Start-Sleep 30
}
```

**Terminal 3: Service Status**
```powershell
# Watch services
while ($true) {
    Clear-Host
    Write-Host "Service Status:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}"
    Start-Sleep 10
}
```

### End of Day Review (10 minutes)

```powershell
# 1. Review all PRs created today
gh pr list --state all --search "created:>=$(Get-Date -Format yyyy-MM-dd)"

# 2. Check version bumps
gh release list --limit 5

# 3. Review Memory Bank updates
git diff HEAD~1 memory/

# 4. Check AI usage
Start-Process "http://localhost:9000"

# 5. Plan tomorrow's tasks
code TODO.md
```

---

## Troubleshooting Monitoring

### Can't See Cline Activity

**Check:**
1. Is Cline extension installed?
   ```powershell
   code --list-extensions | Select-String "saoudrizwan.claude-dev"
   ```

2. Is Cline running?
   - Look for Cline panel in VS Code sidebar
   - Check for `.ai-tasks/current-task.md`

**Fix:**
- Install: `code --install-extension saoudrizwan.claude-dev`
- Open: `Ctrl+Shift+P → "Cline: Open"`

### Dashboards Not Loading

**Check Services:**
```powershell
docker ps | Select-String "ai-monitor|vibe-check|vibe-kanban|pr-monitor"
```

**Restart Services:**
```powershell
cd C:\Users\vcabo\job-lead-finder
docker-compose restart
```

### Memory Bank Not Updating

**Check:**
1. Are files writable?
   ```powershell
   Test-Path memory\tasks\active_context.md -PathType Leaf
   ```

2. Is Cline configured to update?
   ```powershell
   code .claude\settings.json
   # Check: "updateOnTaskComplete": true
   ```

### No Git Activity

**Check:**
1. Are there pending TODO tasks?
   ```powershell
   Get-Content TODO.md | Select-String "- \[ \]"
   ```

2. Is autodev loop running?
   ```powershell
   Get-Job | Where-Object { $_.Name -like "*autodev*" }
   ```

3. Is `.ai-tasks/current-task.md` present?
   ```powershell
   Get-Content .ai-tasks\current-task.md
   ```

**Start Loop:**
```powershell
Start-Job -Name "AutoDev" -ScriptBlock { .\scripts\autodev_loop.ps1 }
```

---

## Best Practices

### Do:
✅ Keep Cline panel open in VS Code for real-time view
✅ Check AI Monitor dashboard daily for quota
✅ Review Memory Bank files for context
✅ Watch git branches for new work starting
✅ Monitor open PRs for merge readiness

### Don't:
❌ Interrupt running tasks (let them complete)
❌ Manually edit files while Cline is working
❌ Force-push to branches Cline is using
❌ Delete `.ai-tasks/` files while tasks are running
❌ Ignore error notifications from Cline

---

## Quick Reference Card

| What to Monitor | Where                            | Update Frequency |
| --------------- | -------------------------------- | ---------------- |
| Current Task    | Cline Panel                      | Real-time        |
| Active Work     | `memory/tasks/active_context.md` | Per action       |
| Task Progress   | `TODO.md`                        | Per task         |
| New Branches    | `git branch`                     | Per task         |
| Open PRs        | `gh pr list`                     | Per PR           |
| AI Quota        | http://localhost:9000            | Real-time        |
| Code Quality    | http://localhost:3000            | Per commit       |
| Task Board      | http://localhost:3001            | Per task         |
| PR Tracking     | Docker logs                      | Every 5 min      |

---

## Example Monitoring Session

```powershell
# Terminal 1: Open VS Code with Cline
code .

# Terminal 2: Watch git activity
while ($true) {
    Clear-Host
    Write-Host "=== Auto-Dev Status ===" -ForegroundColor Cyan
    Write-Host "`nActive Branches:"
    git branch | Select-String "auto/"
    Write-Host "`nOpen PRs:"
    gh pr list --state open --json number,title,statusCheckRollup |
        ConvertFrom-Json |
        Format-Table -AutoSize
    Write-Host "`nTODO Tasks Remaining:"
    (Get-Content TODO.md | Select-String "- \[ \]").Count
    Start-Sleep 30
}

# Terminal 3: Watch services
docker-compose logs -f pr-monitor

# Browser: Open dashboards
Start-Process "http://localhost:9000"  # AI Monitor
Start-Process "http://localhost:3000"  # Vibe Check
```

**What You'll See:**
1. **VS Code/Cline:** Real-time task execution, thought process, actions
2. **Terminal 2:** New branches appearing, PRs being created, TODO count decreasing
3. **Terminal 3:** PR monitor checking status, triggering actions
4. **Browser:** AI quota usage, code quality scores

---

## Summary: Best Monitoring Setup

**Primary View: VS Code with Cline Panel**
- Real-time task execution
- Thought process and actions
- Error messages and fixes

**Secondary View: Memory Bank Files**
- `active_context.md` for current state
- `tasks_plan.md` for overall progress
- `TODO.md` for upcoming work

**Background Monitoring: Dashboards**
- AI Monitor for quota management
- Vibe Check for code quality
- PR list for merge status

**Passive Alerts: Git & PRs**
- Watch for new `auto/*` branches
- Monitor PR creation/merge
- Review commits with `[AI]` tags

This gives you complete visibility into autonomous development without interrupting the AI's work! 🚀
