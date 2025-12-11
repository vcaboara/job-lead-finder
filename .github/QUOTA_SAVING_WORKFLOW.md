# Quota-Saving AI Review Workflow

## Problem Solved

Previously, Copilot PR Review ran automatically on **every push**, which:
- ❌ Wasted quota on WIP commits
- ❌ Reviewed test/debug pushes unnecessarily
- ❌ Triggered on commits expected to fail
- ❌ No control over when review happens

## New Comment-Triggered Workflow

Now Copilot review **only runs when explicitly requested** via PR comment:

```markdown
@copilot review
```

or

```markdown
@ai-review
```

## Benefits

✅ **Save Quota**: Only review when code is ready
✅ **Skip WIP Commits**: No review for test/debug pushes
✅ **Explicit Control**: You decide when to spend quota
✅ **Multi-Stage Gate**: Ollama first, then Copilot only if needed

## Recommended Workflow

### 1. Local Review First (Free)
```powershell
# Run Ollama review locally (unlimited, free)
python scripts/ai_review_chain.py <PR_NUMBER>
```

**If Ollama finds issues:** Fix them before using paid Copilot quota!

### 2. Request Copilot Review (Uses Quota)
Only after Ollama passes:

**Option A - Via Script:**
```powershell
python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot
```

**Option B - Via Comment:**
```powershell
gh pr comment <PR_NUMBER> --body "@copilot review"
```

Or comment directly on GitHub PR: `@copilot review`

### 3. Check Copilot Status
Wait ~1 minute for workflow to complete:

```powershell
python scripts/ai_review_chain.py <PR_NUMBER>
```

### 4. Human Review
When both AI reviews pass:

```powershell
gh pr view <PR_NUMBER> --web
gh pr merge <PR_NUMBER> --squash
```

## When to Skip Copilot Review

You can skip Copilot entirely for:
- 📝 Documentation-only changes
- 🧪 Test/debug commits
- 🚧 WIP or experimental code
- 🔧 Minor fixes already reviewed locally
- 📦 Dependency updates

Just rely on Ollama review and human approval.

## Quota Usage Estimates

**Before (auto-trigger):**
- Every push = 1 quota unit
- 10 WIP commits = 10 quota units wasted

**After (comment-trigger):**
- Only final review = 1 quota unit
- 10 WIP commits = 0 quota units (use Ollama instead)

**Savings: ~80-90% reduction in quota usage!**

## Technical Implementation

### Workflow Trigger
`.github/workflows/ai-pr-review.yml` now uses:

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  ai-review:
    if: |
      github.event.issue.pull_request &&
      (
        contains(github.event.comment.body, '@copilot review') ||
        contains(github.event.comment.body, '@ai-review')
      )
```

### Review Chain Detection
`scripts/ai_review_chain.py` detects:
1. If `@copilot review` comment exists
2. If workflow has run (check GitHub Actions status)
3. Provides guidance if not requested yet

### Auto-Request Flag
New `--request-copilot` flag posts comment automatically:

```python
python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot
```

Equivalent to:
```powershell
gh pr comment <PR_NUMBER> --body "@copilot review"
```

## Migration Notes

**Old command** (auto-triggered on every push):
```bash
git push  # Copilot review auto-starts
```

**New command** (explicit trigger):
```bash
git push
python scripts/ai_review_chain.py <PR_NUMBER>  # Ollama first
python scripts/ai_review_chain.py <PR_NUMBER> --request-copilot  # Then Copilot
```

## FAQ

**Q: What if I forget to request Copilot review?**
A: The review script will remind you with the exact command to run.

**Q: Can I still trigger multiple times?**
A: Yes, comment `@copilot review` as many times as needed. Each triggers a new review.

**Q: What about other CI checks?**
A: Other checks (tests, linting, etc.) still run on every push. Only Copilot review is comment-triggered.

**Q: Will this slow down development?**
A: No! Most issues caught by free Ollama review. Copilot only for final polish.

**Q: Can I use both `@copilot review` and `@ai-review`?**
A: Yes, both trigger the same workflow. Use whichever you prefer.

## See Also

- [AI_REVIEW_TRIGGERS.md](AI_REVIEW_TRIGGERS.md) - Complete trigger workflow
- [AUTODEVELOPMENT_QUICKSTART.md](../AUTODEVELOPMENT_QUICKSTART.md) - Quick reference
- [AUTODEVELOPMENT_STATUS.md](../AUTODEVELOPMENT_STATUS.md) - Full setup guide
