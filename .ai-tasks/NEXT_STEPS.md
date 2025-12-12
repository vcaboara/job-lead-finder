# Next Steps - PR Management

**Last Updated**: 2025-12-11 16:23
**Current Branch**: copilot/sub-pr-89-again (PR #94)

## ✅ Completed

- Updated PR #94 description to include documentation cleanup commits
- Created Ollama task file (`.ai-tasks/track-ollama-pr90-fix.md`) for PR #90 test fixes
- Moved 3 markdown files from root to `docs/` directory
- Fixed inclusive language (denylist terminology updates)

## 📋 Current PR Status

### PR #94 - Security Hardening + Doc Cleanup (CURRENT BRANCH)
- **Branch**: copilot/sub-pr-89-again → main
- **Status**: Open, AI review workflow failed (non-blocking)
- **Content**:
  - ✅ Security fixes (path traversal, DoS, ReDoS, HTML injection, weak entropy)
  - ✅ 21 security tests added
  - ✅ `docs/EMAIL_WEBHOOK_SECURITY.md` documentation
  - ✅ 3 markdown files moved to docs/
  - ✅ Ollama task file for PR #90
- **CI Status**: ai-pr-review failed (run 20151417402) - check if this is blocking
- **Next Action**: Review AI review failure, merge if security changes are good

### PR #90 - Email Webhook Integration (TEST FAILURES)
- **Branch**: copilot/sub-pr-89 → main
- **Status**: Open, CI failing (2 test failures)
- **Failures**:
  - `test_email_processor.py::test_match_job_by_company_and_title` - Job ID mismatch
  - `test_gemini_cli.py::test_cli_exits_if_no_sdk_installed` - Import error
- **Recent Runs**:
  - CI run 20151346194 (2025-12-11 23:57) - FAILED
  - CI run 20151165395 (2025-12-11 23:47) - FAILED
- **Delegated To**: Ollama agent (see `.ai-tasks/track-ollama-pr90-fix.md`)
- **Next Action**: Wait for Ollama to fix tests, then merge

### PR #98 - MCP Services
- **Branch**: feature/mcp-services → main
- **Status**: Open, checks passing
- **Content**: Brave Search and Fetch MCP services
- **Dependencies**: Has sub-PR #99 (copilot/sub-pr-98 → feature/mcp-services)
- **Next Action**: Review and merge after PR #94

### PR #99 - MCP Config Fix
- **Branch**: copilot/sub-pr-98 → feature/mcp-services
- **Status**: Open (sub-PR of #98)
- **Content**: Fix MCP server configuration (stdio vs HTTP)
- **Next Action**: Review as part of PR #98 chain

## 🎯 Recommended Merge Order

1. **PR #94** (Security + Docs) - Review AI review failure, merge if acceptable
2. **PR #98/#99** (MCP Services) - Merge after #94
3. **PR #90** (Email Webhook) - Merge after Ollama fixes tests

## 🔍 Immediate Actions Needed

### For PR #94 (You're here)
```powershell
# Check AI review failure details
gh run view 20151417402 --log

# If AI review is non-critical, can merge with:
# gh pr merge 94 --squash --delete-branch
```

### For PR #90 (Delegated to Ollama)
```powershell
# Ollama should follow .ai-tasks/track-ollama-pr90-fix.md:
# 1. Get CI logs: gh run view 20151346194 --log-failed
# 2. Fix test isolation issues
# 3. Commit with [AI] tag
# 4. Push to copilot/sub-pr-89
# 5. Verify CI passes
```

### For PR #98/99 (Ready to review)
```powershell
# Review MCP configuration changes
gh pr view 98
gh pr view 99

# Merge when ready (after #94)
```

## 📊 Branch Relationship

```
main
├── copilot/sub-pr-89-again (PR #94) ← YOU ARE HERE
│   └── Security + Docs
├── copilot/sub-pr-89 (PR #90)
│   └── Email Webhook (needs test fixes)
└── feature/mcp-services (PR #98)
    └── copilot/sub-pr-98 (PR #99)
        └── MCP config fix
```

## 🤖 AI Agent Assignments

- **PR #94**: Manual review (human decision on AI review failure)
- **PR #90**: Ollama (test fixes delegated via task file)
- **PR #98/99**: Ready for human review
- **Issue #82**: @github-copilot (Memory Bank documentation)

## 💡 Notes

- **PR #94** combines security work (main content) with doc cleanup (bonus) - acceptable
- **PR #90** test failures are isolated test issues, not production bugs
- **AI review failure** on PR #94 may be due to diff size (security PR is large)
- **Ollama task** has detailed instructions for fixing PR #90

## 🚀 After All PRs Merged

1. Pull latest main: `git checkout main; git pull`
2. Review Issue #82 progress (@github-copilot working on Memory Bank)
3. Consider framework extraction for ESG discovery project
4. Monitor Ollama agent for PR #90 fix completion
