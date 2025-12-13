# AI Review Workflow Triggers

This document describes the automated triggers and human interactions in our multi-agent review workflow.

## Review Chain Flow

```
Gemini (Code) → Apply → PR Created
  ↓
Ollama (Local Review) → Auto-triggered by review script
  ↓ (if pass)
Copilot (GitHub Review) → Auto-triggered by GitHub Actions on push
  ↓ (if pass)
Human Review → Requested via comment, human decides next action
```

## Automated Triggers

### 1. Ollama Review Trigger
- **Trigger**: Manual execution of review script
- **Command**: `python scripts/ai_review_chain.py <PR_NUMBER>`
- **Action**: Reviews PR diff locally using Ollama
- **Output**: Pass/fail with specific feedback
- **On Failure**: Script exits with error, developer must fix and push
- **On Success**: Proceeds to check Copilot review status

### 2. Copilot PR Review Trigger
- **Trigger**: Manual via PR comment (saves quota!)
- **Commands**:
  - Comment on PR: `@copilot review` or `@ai-review`
  - Or use script: `python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot`
- **Workflow**: `.github/workflows/ai-pr-review.yml` (triggered by comment)
- **Action**: GitHub Copilot reviews code changes
- **Output**: Comments on PR with suggestions
- **On Failure**: Review script detects failed check, developer must address
- **On Success**: Proceeds to human review request

**Why comment-triggered?** Prevents wasting quota on WIP commits, test pushes, or expected failures.

### 3. Human Review Request Trigger
- **Trigger**: Automatic when Ollama + Copilot both pass
- **Action**: Posts comment on PR mentioning @vcaboara
- **Output**: Comment with checklist and lovable.dev reminder
- **Result**: Awaits human decision

## Human Interaction Points

### Response to AI Feedback

#### Comment Format to Request Copilot Review
Trigger Copilot review when your code is ready:

```markdown
@copilot review
```

or

```markdown
@ai-review
```

**When to request:**
- After Ollama review passes
- When code is ready for thorough review
- Skip for WIP commits or expected failures (saves quota)

#### Comment Format for AI Agent
When AI reviews find issues, use these comment formats to delegate fixes:

```markdown
@ai-agent please fix: <specific issue description>
```

Examples:
```markdown
@ai-agent please fix: Add type hints to the calculate_score function

@ai-agent please fix: Refactor nested if statements in process_data()

@ai-agent please fix: Add error handling for network timeouts
```

#### Comment Format for Gemini (Track Tasks)
For tasks assigned to Gemini, use this format:

```markdown
@gemini-agent please address: <specific feedback>
```

Examples:
```markdown
@gemini-agent please address: Logo placeholder colors too bright, use muted palette

@gemini-agent please address: Missing screenshot comparison, provide before/after
```

### Human Review Outcomes

After all AI reviews pass, human can:

1. **Approve and Merge**
   ```bash
   gh pr review <PR_NUMBER> --approve
   gh pr merge <PR_NUMBER> --squash
   ```

2. **Request Changes**
   - Comment on PR with specific issues
   - Tag appropriate agent: `@ai-agent` or `@gemini-agent`
   - Wait for updates and re-run review chain

3. **Manual Fixes**
   - Checkout PR branch
   - Make changes directly
   - Push and re-run review chain

## Re-Running Review Chain

After addressing AI feedback:

```powershell
# Push fixes
git add .
git commit -m "fix: Address AI review feedback"
git push

# Re-run review chain (Ollama only)
python scripts/ai_review_chain.py <PR_NUMBER>

# If Ollama passes, request Copilot review
python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot
# OR comment on PR: @copilot review
```

**Quota-Saving Tip:** Only request Copilot review after Ollama passes and you're confident in the code.

## Workflow States

### State 1: Ollama Review Failed
- **Who Acts**: Developer or Gemini (for Track tasks)
- **Action**: Fix issues mentioned in Ollama feedback
- **Next**: Push changes, re-run review script

### State 2: Copilot Review Not Requested
- **Who Acts**: Developer
- **Action**: Request Copilot review when code is ready
- **Options**:
  - Comment: `@copilot review` on PR
  - Script: `python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot`
- **Next**: Wait ~1 minute, then re-run review script

### State 3: Copilot Review Failed
- **Who Acts**: Developer or Gemini (for Track tasks)
- **Action**: Address comments in GitHub PR
- **Next**: Push changes, re-run Ollama, then request Copilot again

### State 4: Ready for Human Review
- **Who Acts**: Human (@vcaboara)
- **Action**: Review PR on GitHub
- **Options**:
  - Approve → Merge
  - Request changes → Comment with `@ai-agent` or `@gemini-agent`
  - Manual fix → Checkout, fix, push, re-run

## Automation Configuration

### Current Setup (Manual Trigger)
- Ollama review: Manual script execution
- Copilot review: Automatic on push
- Human review: Manual via GitHub

### Future Enhancement (Full Automation)
Could add GitHub Actions workflow:

```yaml
# .github/workflows/auto-review-chain.yml
name: Auto Review Chain
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Ollama Review
        run: python scripts/ai_review_chain.py ${{ github.event.pull_request.number }}
```

**Note**: This requires Ollama running in CI environment (Docker container or hosted service).

## Best Practices

1. **Always re-run full review chain** after making changes
2. **Be specific in AI agent comments** - vague feedback leads to vague fixes
3. **Check all three review stages** before final approval
4. **Use conventional commits** when addressing feedback
5. **Update CHANGELOG.md** if changes are significant

## Troubleshooting

### Ollama Review Stuck
```bash
# Check if Ollama is running
docker compose ps ollama

# Restart if needed
docker compose restart ollama
```

### Copilot Review Not Triggering
```bash
# Check GitHub Actions
gh pr checks <PR_NUMBER>

# Re-trigger by pushing empty commit
git commit --allow-empty -m "chore: Trigger CI"
git push
```

### Review Script Errors
```bash
# Check if gh CLI authenticated
gh auth status

# Re-authenticate if needed
gh auth login
```

## Summary

**Key Points:**
- Ollama and Copilot reviews are **automatic gates**
- Human review is the **final decision point**
- Use `@ai-agent` or `@gemini-agent` comments to **delegate fixes**
- Always **re-run full review chain** after changes
- Script provides **clear next steps** at each stage
