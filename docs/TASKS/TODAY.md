# TODAY's Plan - December 9, 2025

**Focus:** Local AI resources + Token compression for cost reduction
**Status:** All PRs merged (#67, #68, #69) - Ready to build!

---

## 🎯 High-Priority Goals

### 1. Local AI Resource Integration (PRIORITY 1)
**Why:** Reduce API costs, unlimited usage, faster iteration
**Time:** 2-3 hours

**Tasks:**
- [ ] **vibe-check-mcp integration test**
  - Start service: `docker compose up -d vibe-check-mcp`
  - Test code review endpoint
  - Document usage in VS Code/Cursor
  - Create sample workflow

- [ ] **Ollama local LLM verification**
  - Verify Ollama running (port 11434)
  - Test with current `ollama_provider.py`
  - Benchmark vs Gemini API (quality + speed)
  - Document when to use local vs cloud

- [ ] **Create AI resource selector**
  - Script: `tools/select_ai_provider.py`
  - Logic: complexity → provider mapping
  - Integration with existing code

**Deliverables:**
- `docs/LOCAL_AI_SETUP.md` - Setup guide
- `tools/select_ai_provider.py` - Provider selector
- Updated `docker-compose.yml` tested

---

### 2. Token Compression Implementation (PRIORITY 2)
**Why:** Reduce API costs by 40-60% per copilot-instructions.md
**Time:** 1-2 hours

**Tasks:**
- [ ] **Apply level-2 compression to copilot-instructions.md**
  - Current: References `docs/AI_Coding_Style_Guide_prompts.toml` level-2
  - Action: Actually implement compression in instructions
  - Verify no functionality lost

- [ ] **Create compression metrics tracking**
  - Before: Current token count of copilot-instructions.md
  - After: Compressed version token count
  - Script: `tools/measure_token_usage.py`

- [ ] **Update AI agent configs with compression**
  - Ensure all AI agents follow compressed style
  - Add to lessons-learned.md

**Deliverables:**
- Compressed `.github/copilot-instructions.md`
- `tools/measure_token_usage.py` - Token counter
- Documented savings in `memory/docs/lessons-learned.md`

---

### 3. PR Review Automation Setup (PRIORITY 3)
**Why:** From TOMORROW plan - automated AI code review
**Time:** 1-2 hours

**Tasks:**
- [ ] **Create PR review workflow**
  - File: `.github/workflows/ai-pr-review.yml`
  - Trigger: On PR creation/update
  - Use: vibe-check-mcp for local review

- [ ] **Configure review criteria**
  - Use existing `docs/pr-review-criteria.md` (from copilot-instructions)
  - Create structured output format
  - Add auto-comment on PRs

- [ ] **Test with sample PR**
  - Create test branch
  - Submit PR
  - Verify review posted

**Deliverables:**
- `.github/workflows/ai-pr-review.yml`
- `docs/AI_PR_REVIEW.md` - Documentation
- Working demo on test PR

---

## 📦 Secondary Goals (If Time Permits)

### 4. Container Optimization Prep
**From:** TOMORROW Session 1.1
**Time:** 30-60 min

**Quick wins:**
- [ ] Create `.dockerignore` (aggressive)
- [ ] Document current image sizes
- [ ] Research Alpine + distroless patterns

**Deliverables:**
- `.dockerignore` committed
- `docs/CONTAINER_OPTIMIZATION.md` started

---

### 5. Branch Development Workflow
**Why:** Support parallel AI agent work
**Time:** 30-45 min

**Tasks:**
- [ ] Document current branch strategy
- [ ] Create branch naming conventions
- [ ] Update git-aliases.ps1 with branch helpers

**Deliverables:**
- `docs/BRANCH_STRATEGY.md`
- Updated `tools/git-aliases.ps1`

---

## 🎯 Success Criteria

**By End of Day:**
- ✅ vibe-check-mcp actively used for code review
- ✅ Token compression reducing costs by 30%+
- ✅ PR review automation working on test PR
- ✅ 3+ PRs created with [AI] attribution
- ✅ <2 hours manual typing

**Stretch:**
- ✅ Ollama integrated for simple tasks
- ✅ Container optimization started
- ✅ Branch workflow documented

---

## 📊 Cost Tracking

**API Usage Goals:**
- **Gemini calls:** <20 today (use local when possible)
- **Copilot requests:** Track via AI metrics
- **Token savings:** Document compression impact

**Log in:** `memory/docs/ai-metrics-tracking.md`

---

## 🚀 Getting Started

**Right now:**
1. ✅ Read this plan
2. ⬜ Start vibe-check-mcp: `docker compose up -d vibe-check-mcp`
3. ⬜ Create branch: `git checkout -b feat/local-ai-integration`
4. ⬜ Begin Task 1: vibe-check-mcp integration

**Branch strategy for today:**
- `feat/local-ai-integration` - Tasks 1 & 2
- `feat/pr-review-automation` - Task 3
- `chore/container-prep` - Task 4 (if time)

---

## 💡 Notes

**Context from yesterday:**
- PR #67: Fixed test isolation (xdist_group markers)
- PR #68: Added git-aliases.ps1 (PowerShell helpers)
- PR #69: AI attribution standard ([AI] prefix)

**Lessons applied:**
- ✅ MANDATORY VERIFICATION before pushing
- ✅ [AI] attribution in all commits
- ✅ Use feature branches (no direct main pushes)

**Resources available:**
- vibe-check-mcp service (port 3000)
- Ollama (port 11434)
- AI monitor UI (port 9000)
- Main UI (port 8000)

---

**Let's build! 🚀**

*Estimated AI acceleration: 6.6x*
*Token savings target: 40%+*
