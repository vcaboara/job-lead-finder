# TODO - Active Development Tasks

## Immediate (Do Now)

- [x] Merge PR #119 - Version bump fix ✅ MERGED
- [x] Merge PR #120 - Gemini instructions update ✅ MERGED
- [x] Push PR monitor service (scripts/pr_monitor.py) ✅ DEPLOYED
- [x] Set up GitHub PAT for autonomous version bumping ✅ CONFIGURED
- [x] Enable auto-delete branches on merge ✅ CONFIGURED (delete_branch_on_merge: true)
- [x] Fix Vibe Kanban monitoring ✅ FIXED (Kanban is UI route at /visual-kanban on port 8000)
- [x] Verify version bump auto-merge after next merge ✅ PR #130 CREATED
- [ ] Monitor PR monitor service logs for 24h

## High Priority (This Week)

- [ ] Migrate job_tracker to framework fully
  - [ ] Move job_tracker_new.py to framework/tracker/
  - [ ] Update imports across codebase
  - [ ] Remove old job_tracker.py
  - [ ] Update tests

- [ ] Add Slack notifications to PR monitor
  - [ ] Configure Slack webhook URL
  - [ ] Test notification on PR events
  - [ ] Document setup in docs/PR_MONITOR.md

- [ ] Clean up provider architecture
  - [ ] Consolidate ollama_provider.py and gemini_provider.py
  - [ ] Document provider interface in framework
  - [ ] Add provider selection logic to config

## Medium Priority (Next Sprint)

- [ ] Improve UI job tracking
  - [ ] Add bulk actions (mark multiple as applied)
  - [ ] Add filtering by date/status
  - [ ] Export to CSV functionality

- [ ] Enhance discovery system
  - [ ] Add rate limiting per provider
  - [ ] Implement retry logic with exponential backoff
  - [ ] Add discovery result caching

- [ ] Documentation improvements
  - [ ] Update README with new framework structure
  - [ ] Add architecture diagram
  - [ ] Document all environment variables

## Low Priority (Future Enhancements)

- [ ] Cross-platform setup utility (`setup_dev.py`)
- [ ] Resume format support (RTF, ODT, OCR)
- [ ] Security hardening (sandboxed parsing, file limits)

---

## Technical Debt

See `docs/TECHNICAL_DEBT.md` for performance optimizations and code quality notes.
