# TODO - Active Development Tasks

## Immediate (Do Now)

- [ ] Merge PR #119 - Version bump fix (ready to merge)
- [ ] Merge PR #120 - Gemini instructions update (needs review)
- [ ] Push PR monitor service (scripts/pr_monitor.py)
- [ ] Set up GitHub PAT for autonomous version bumping
- [ ] Test Cline autonomous task execution

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
