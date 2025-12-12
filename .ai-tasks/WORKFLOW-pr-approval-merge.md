# Workflow: PR Approval → Merge Process

**Trigger**: PR receives approval
**Goal**: Safely merge approved PR after verifying main branch stability

## Process Steps

### 1. Verify PR Approval Status
```powershell
gh pr view <PR_NUMBER> --json reviewDecision,mergeable,mergeStateStatus
```

**Expected Output:**
```json
{
  "reviewDecision": "APPROVED",
  "mergeable": "MERGEABLE",
  "mergeStateStatus": "CLEAN"
}
```

### 2. Check PR CI Status
```powershell
gh pr view <PR_NUMBER> --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS")'
```

**Expected**: Empty output (all checks passing)

### 3. Verify Main Branch CI Status
```powershell
gh run list --branch main --limit 1 --json conclusion,status,workflowName,createdAt
```

**Expected Output:**
```json
[
  {
    "conclusion": "SUCCESS",
    "status": "COMPLETED",
    "workflowName": "CI"
  }
]
```

**If main CI is failing or stale:**
- Option A: Trigger new CI run: `gh workflow run .github/workflows/ci.yml --ref main`
- Option B: Merge PR anyway if failures are unrelated (document in merge commit)

### 4. Check for Merge Conflicts
```powershell
gh pr view <PR_NUMBER> --json mergeable
```

**If conflicts exist:**
```powershell
git checkout <PR_BRANCH>
git pull origin main
# Resolve conflicts
git push origin <PR_BRANCH>
```

### 5. Perform Merge
```powershell
gh pr merge <PR_NUMBER> --squash --delete-branch
```

**Options:**
- `--squash`: Squash all commits into one (preferred for feature branches)
- `--merge`: Keep all commits (for large features with meaningful history)
- `--rebase`: Rebase and merge (for linear history)
- `--delete-branch`: Automatically delete branch after merge
- `--auto`: Enable auto-merge when checks pass

**With message:**
```powershell
gh pr merge <PR_NUMBER> --squash --delete-branch --subject "[AI] <title>" --body "Merged via automated workflow

Approval verified: <approver>
CI status: All checks passing
Main branch: Verified passing

AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)"
```

### 6. Verify Merge Success
```powershell
gh pr view <PR_NUMBER> --json state,merged,mergedAt
```

**Expected:**
```json
{
  "state": "MERGED",
  "merged": true,
  "mergedAt": "2025-12-11T..."
}
```

### 7. Verify Branch Deletion
```powershell
git branch -r | Select-String "<PR_BRANCH>"
```

**Expected**: No output (branch deleted)

### 8. Update Local Repository
```powershell
git checkout main
git pull origin main
git remote prune origin  # Clean up deleted remote branches
```

## Automated Workflow Example

```powershell
# Complete merge workflow for approved PR
$PR_NUMBER = 94

# Step 1: Verify approval and CI
$pr_status = gh pr view $PR_NUMBER --json reviewDecision,mergeable,statusCheckRollup | ConvertFrom-Json

if ($pr_status.reviewDecision -ne "APPROVED") {
    Write-Error "PR not approved"
    exit 1
}

if ($pr_status.mergeable -ne "MERGEABLE") {
    Write-Error "PR has merge conflicts"
    exit 1
}

$failed_checks = $pr_status.statusCheckRollup | Where-Object { $_.conclusion -ne "SUCCESS" }
if ($failed_checks) {
    Write-Warning "Some checks failed: $($failed_checks.name -join ', ')"
}

# Step 2: Check main branch CI
$main_ci = gh run list --branch main --limit 1 --json conclusion,status | ConvertFrom-Json
if ($main_ci[0].conclusion -ne "SUCCESS") {
    Write-Warning "Main branch CI not passing: $($main_ci[0].conclusion)"
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y") { exit 1 }
}

# Step 3: Merge
gh pr merge $PR_NUMBER --squash --delete-branch

# Step 4: Update local
git checkout main
git pull origin main
git remote prune origin

Write-Host "✅ PR #$PR_NUMBER merged and branch deleted" -ForegroundColor Green
```

## Edge Cases

### Main Branch CI Failing
**Decision Tree:**
1. Are failures related to PR changes?
   - YES: Don't merge, fix PR first
   - NO: Document in merge commit, merge anyway

2. Are failures in PR branch too?
   - YES: Failures are environmental/flaky, safe to merge
   - NO: Wait for main to be fixed first

### PR Has Conflicts
**Options:**
1. Rebase: `git checkout <branch> && git rebase main`
2. Merge: `git checkout <branch> && git merge main`
3. Ask PR author to resolve

### Multiple Approved PRs
**Strategy:**
1. Check dependency graph (does PR B depend on PR A?)
2. Merge in dependency order
3. For independent PRs, merge oldest-first
4. Watch for conflicts between PRs

### Branch Not Auto-Deleted
**Reasons:**
- Protected branch rules
- Branch has other PRs pointing to it
- GitHub API issue

**Manual cleanup:**
```powershell
git push origin --delete <branch_name>
```

## Notifications

After merge:
1. Check related issues: `gh pr view <PR> --json closingIssuesReferences`
2. Notify stakeholders if needed
3. Update project board if using GitHub Projects
4. Document in CHANGELOG.md if public release

## Related

- `.github/workflows/ci.yml`: CI configuration
- `.github/workflows/ai-pr-review.yml`: Auto-review on PR comments
- `CHANGELOG.md`: Document significant changes
