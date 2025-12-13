# GitHub Copilot + Ollama Task Delegation Workflow

**Created**: December 9, 2025
**Purpose**: Coordinate parallel AI work using GitHub Copilot (premium) and Ollama (free local)

---

## Overview

### Cost Model
- **GitHub Copilot**: ~1 premium token per task/review request
- **Ollama Local**: Unlimited, free (just electricity ~$0.0001/request)

### Task Assignment Strategy
```
P0 (Critical Foundation)  → GitHub Copilot (fast, reliable, 2-3 sec)
P1 (High-Value Features)  → GitHub Copilot (premium quality needed)
P2 (Enhancements)         → Ollama Local (good enough, 19 sec acceptable)
P3 (Future/Nice-to-have)  → Ollama Local (unlimited iterations)

Bug Fixes                 → Ollama Local (fast iteration, low risk)
PR Reviews                → Ollama Local (save premium tokens)
Refactoring               → Ollama Local (non-critical)
Documentation             → Either (Ollama good at docs)
```

---

## Workflow: Delegating Tasks to GitHub Copilot

### Method 1: GitHub Issues (Recommended)

**Create Task Issue**:
```bash
gh issue create \
  --title "[AI] P0: Task Name Here" \
  --body "$(cat task-template.md)"
```

**Trigger Copilot via Comment**:
```bash
gh issue comment 82 --body "@github-copilot Please complete this task following the requirements in the issue description. Create a PR when done."
```

**Monitor Progress**:
```bash
gh issue view 82
gh pr list --search "linked:issue-82"
```

### Method 2: Pull Request Reviews

**Request Copilot Review**:
```bash
gh pr create --title "[AI] Feature: XYZ" --body "..."
gh pr comment 81 --body "@github-copilot Please review this PR for:
- Code quality and best practices
- Test coverage
- Security issues
- Performance concerns"
```

**Cost**: 1 premium token per review request

### Method 3: Direct PR Creation

**Let Copilot Implement**:
1. Create issue with detailed requirements
2. Comment: `@github-copilot Please create a PR to implement this`
3. Copilot creates branch + commits + PR
4. You review and merge

---

## Workflow: Delegating Tasks to Ollama

### Method 1: Task Executor Script

**Generate Task Guidance**:
```bash
python scripts/autonomous_task_executor.py
```

**Output**: Creates `.ai-tasks/track-X-local.md` files

**Execute with Ollama**:
```bash
# Read the guidance file
$prompt = Get-Content .ai-tasks/track-4-local.md -Raw

# Run Ollama
python tools/llm_api.py \
  --provider local \
  --model "deepseek-coder:6.7b" \
  --prompt "$prompt"
```

### Method 2: Direct Prompting

**For Bug Fixes**:
```bash
python tools/llm_api.py \
  --provider local \
  --model "deepseek-coder:6.7b" \
  --prompt "Fix the bug in src/app/job_finder.py where search results are not being filtered correctly. The issue is on line 145."
```

**For Refactoring**:
```bash
python tools/llm_api.py \
  --provider local \
  --model "codellama:7b" \
  --prompt "Refactor the validate_email function in utils.py to be more Pythonic and add comprehensive type hints."
```

### Method 3: PR Review with Ollama

**Review a PR**:
```bash
# Get PR diff
gh pr diff 81 > pr-81.diff

# Ask Ollama to review
python tools/llm_api.py \
  --provider local \
  --model "deepseek-coder:6.7b" \
  --prompt "Review this PR diff for code quality, bugs, and improvements: $(cat pr-81.diff)"
```

**Cost**: $0 (saves premium tokens)

---

## Active Tasks (Current State)

### GitHub Issues Created

**Issue #82: P0 Memory Bank Documentation** ✅ Created
- **Agent**: GitHub Copilot
- **Status**: Waiting for Copilot trigger
- **Next**: Comment `@github-copilot Please complete this task`
- **Branch**: docs/memory-bank-p0-detailed
- **Estimated Cost**: 1 premium token

**Issue #83: P2 Kanban Board Service** ✅ Created
- **Agent**: TBD (Evaluation task - will try both)
- **Status**: Ready for assignment
- **Options**:
  - GitHub Copilot: Fast, 2-3 premium tokens
  - Ollama: Slower (19 sec per response), unlimited iterations
- **Branch**: feature/kanban-board

### Next Steps

1. **Trigger Copilot for Issue #82**:
   ```bash
   gh issue comment 82 --body "@github-copilot Please implement this task. Create a feature branch, update the files as specified, and open a PR when complete."
   ```

2. **Choose Agent for Issue #83** (Evaluation):
   - **Option A**: Delegate to Copilot (benchmark speed + quality)
   - **Option B**: Use Ollama (benchmark free alternative)
   - **Recommendation**: Try Ollama first (save tokens, good learning)

---

## Monitoring Parallel Work

### Check GitHub Copilot Tasks
```bash
# List all AI task issues
gh issue list --label "AI"

# Check specific task
gh issue view 82

# See related PRs
gh pr list --search "linked:issue-82"
```

### Check Ollama Tasks
```bash
# List guidance files
ls .ai-tasks/

# Check recent Ollama responses (if logging enabled)
ls logs/ollama-*.log
```

### Overall Progress
```bash
# Git branches show active work
git branch -a | grep -E "(auto/|feature/|docs/)"

# PRs show pending merges
gh pr list --state open

# Memory Bank status
cat memory/tasks/active_context.md
```

---

## Parallel Execution Example

### Scenario: Work on P0, P1, and P2 simultaneously

**Step 1: Assign Tasks** (Morning):
```bash
# P0 to Copilot (fast, critical)
gh issue comment 82 --body "@github-copilot Start working on this"

# P1 to Copilot (high-value)
gh issue create --title "[AI] P1: Email Server Integration"
gh issue comment 84 --body "@github-copilot Implement email integration per spec"

# P2 to Ollama (background, unlimited)
python scripts/autonomous_task_executor.py
python tools/llm_api.py --provider local --prompt "$(cat .ai-tasks/track-5-local.md)"
```

**Step 2: Monitor Progress** (Throughout Day):
```bash
# Check Copilot tasks
gh pr list --label "AI"

# Check Ollama output (if saved)
cat ollama-output-track-5.md
```

**Step 3: Review & Merge** (Afternoon):
```bash
# Review Copilot PRs (auto-created)
gh pr view 85
gh pr review 85 --approve

# Create PR from Ollama output (manual)
git checkout -b feature/track-5
# ... copy Ollama code ...
git commit -m "[AI] feat: Implementation from Ollama"
gh pr create
```

---

## Cost Analysis

### GitHub Copilot Usage
```
Issue #82 (P0 Memory Bank):       1 token  (task completion)
Issue #84 (P1 Email Integration): 2 tokens (implementation + review)
PR Review on #81:                  1 token  (code review)

Total: 4 premium tokens
```

### Ollama Usage
```
Issue #83 (P2 Kanban):     0 tokens (unlimited local)
Bug fixes (5 iterations):  0 tokens (unlimited)
PR reviews (3 PRs):        0 tokens (unlimited)
Refactoring (2 tasks):     0 tokens (unlimited)

Total: $0
```

### Optimization Strategy
- Use **Copilot for P0/P1** where speed and quality are critical
- Use **Ollama for P2/P3** where iteration and cost-savings matter
- Use **Ollama for reviews** to save premium tokens
- Use **Ollama for refactoring** (low risk, iterative)

---

## Evaluation: Issue #83 (Kanban Board)

### Test Both Agents on Same Task

**Approach A: Copilot First**
```bash
gh issue comment 83 --body "@github-copilot Build the Kanban board service as specified. Optimize for speed and quality."
```

**Track**: Time to PR, code quality, tests included

**Approach B: Ollama After**
```bash
python tools/llm_api.py \
  --provider local \
  --model "deepseek-coder:6.7b" \
  --prompt "$(gh issue view 83 --json body -q .body)"
```

**Track**: Time to completion, iterations needed, final quality

**Compare**:
- Speed: Copilot vs Ollama
- Quality: Both implementations
- Cost: Premium tokens vs $0
- Decide: Which for future P2 tasks?

---

## Quick Reference

### Create Task for Copilot
```bash
gh issue create --title "[AI] P0/P1: Task Name" --body "Detailed requirements..."
gh issue comment <ID> --body "@github-copilot Please implement this"
```

### Create Task for Ollama
```bash
python scripts/autonomous_task_executor.py  # Generates .ai-tasks/*.md
python tools/llm_api.py --provider local --prompt "$(cat .ai-tasks/track-X-local.md)"
```

### Monitor All Work
```bash
gh issue list --label "AI"          # Copilot tasks
gh pr list --state open             # All PRs
git branch -a | grep -E "auto/|feature/"  # Active branches
```

### Check Resources
```bash
open http://localhost:9000          # AI Monitor dashboard
cat memory/tasks/active_context.md  # Current work status
```

---

## Current Status Summary

✅ **Infrastructure Ready**:
- GitHub issues created (#82, #83)
- Ollama running locally (deepseek-coder:6.7b, llama3.2:3b, codellama:7b)
- Task executor script functional
- AI Monitor dashboard active

🎯 **Next Actions**:
1. Trigger Copilot on Issue #82 (P0 Memory Bank)
2. Decide Copilot vs Ollama for Issue #83 (P2 Kanban)
3. Monitor parallel execution
4. Compare results and optimize strategy

📊 **Token Budget**:
- Copilot: Available for P0/P1 high-value work
- Ollama: Unlimited for P2/P3, reviews, bug fixes
