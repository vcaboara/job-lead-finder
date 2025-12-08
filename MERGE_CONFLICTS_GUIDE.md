# Merge Conflicts Guide: feature/resume-and-workers → main

## Overview
This merge brings the Worker/Resume panel UI modernization from `feature/resume-and-workers` into `main`, which will enable PR #44 (toast notifications) to be rebased properly.

## Conflicts to Resolve (6 files)

### 1. `.github/copilot-instructions.md` (CONFLICT: content)
**Difficulty:** LOW

**Main branch has:**
- Auto-discovery feature documentation
- Testing instructions for automated job discovery
- Git workflow with screenshot requirements

**Feature branch has:**
- UI modernization guidelines
- Component-based development patterns
- lovable.dev design system references

**Resolution Strategy:**
- Keep ALL sections from both branches
- Merge documentation additively
- Auto-discovery docs + UI modernization docs

---

### 2. `src/app/gemini_provider.py` (CONFLICT: content)
**Difficulty:** MEDIUM

**Expected differences:**
- Main: May have logging changes for auto-discovery
- Feature: May have different AI provider integration patterns

**Resolution Strategy:**
- Compare both versions line-by-line
- Prefer feature branch for provider patterns
- Ensure auto-discovery functionality preserved
- Test AI extraction after merge

---

### 3. `src/app/job_finder.py` (CONFLICT: content)
**Difficulty:** MEDIUM

**Expected differences:**
- Main: Auto-discovery integration
- Feature: Different provider orchestration

**Resolution Strategy:**
- Keep auto-discovery methods from main
- Adopt provider patterns from feature branch
- Ensure `discover_jobs_from_resume()` still works
- Test both manual search and auto-discovery

---

### 4. `src/app/ollama_provider.py` (CONFLICT: add/add)
**Difficulty:** LOW-MEDIUM

**Situation:**
- Both branches added this file independently
- Likely similar implementations with minor differences

**Resolution Strategy:**
- Compare implementations
- Choose the more complete version (likely feature branch)
- Ensure it follows same pattern as gemini_provider.py
- Test Ollama integration if enabled

---

### 5. `src/app/templates/index.html` (CONFLICT: content) ⚠️ MAJOR
**Difficulty:** HIGH

**Main branch has:**
- Simpler UI structure
- Basic job list display
- Auto-discovery status/trigger buttons (from recent commits)

**Feature branch has:**
- Modernized UI with lovable.dev design system
- Worker panel (job tracking interface)
- Resume panel (resume upload/management)
- Settings modal
- Enhanced CSS with variables
- Better responsive design

**Resolution Strategy:**
1. **Use feature branch as base** (it's the target UI)
2. **Add back auto-discovery UI elements from main:**
   - Auto-discovery status display
   - Manual trigger button
   - Last run timestamp
   - Job count from auto-discovery
3. **Preserve new panels:**
   - Worker panel structure
   - Resume panel structure
   - Settings modal
4. **Ensure JavaScript compatibility:**
   - Check HTMX attributes still work
   - Verify API endpoint calls match ui_server.py
5. **Test thoroughly:**
   - All panels render correctly
   - Auto-discovery UI displays status
   - Manual trigger works
   - Resume upload works
   - Worker tracking displays

**Critical sections to merge:**
```html
<!-- From main: Add to appropriate location -->
<div class="auto-discovery-status">
    <button hx-post="/api/auto-discover/trigger">Trigger Discovery</button>
    <div hx-get="/api/auto-discover/status" hx-trigger="every 30s">
        Status: <span id="auto-discover-status">...</span>
    </div>
</div>

<!-- From feature: Keep entire modernized structure -->
<div class="worker-panel">...</div>
<div class="resume-panel">...</div>
<div class="settings-modal">...</div>
```

---

### 6. `src/app/ui_server.py` (CONFLICT: content)
**Difficulty:** MEDIUM-HIGH

**Main branch has:**
- `/api/auto-discover/trigger` POST endpoint
- `/api/auto-discover/status` GET endpoint
- Auto-discovery background integration

**Feature branch has:**
- Worker panel endpoints
- Resume upload/management endpoints
- Settings endpoints
- Enhanced UI serving

**Resolution Strategy:**
1. **Keep ALL endpoints** from both branches
2. **Merge route definitions:**
   ```python
   # From main - keep these
   @app.post("/api/auto-discover/trigger")
   async def trigger_auto_discover(): ...

   @app.get("/api/auto-discover/status")
   async def auto_discover_status(): ...

   # From feature - keep these
   @app.post("/api/worker/...")
   @app.get("/api/resume/...")
   @app.post("/api/settings/...")
   ```
3. **Preserve background scheduler integration** from both
4. **Ensure template rendering** uses feature branch version (with panels)
5. **Test all endpoints** after merge

**Import statements:**
- Merge all imports from both versions
- Remove duplicates
- Ensure background_scheduler imported correctly

---

## Merge Procedure

### Step 1: Create merge branch
```bash
git checkout -b merge/resume-workers-to-main main
git merge origin/feature/resume-and-workers --no-commit
```

### Step 2: Resolve conflicts in order
1. `.github/copilot-instructions.md` (easiest)
2. `src/app/ollama_provider.py` (pick best version)
3. `src/app/gemini_provider.py` (merge carefully)
4. `src/app/job_finder.py` (preserve auto-discovery)
5. `src/app/ui_server.py` (merge all endpoints)
6. `src/app/templates/index.html` (most complex - take your time)

### Step 3: For each conflict
```bash
# Check conflict markers
git diff --name-only --diff-filter=U

# Edit file to resolve
# Remove <<<<<<< HEAD, =======, >>>>>>> markers
# Test your changes

# Mark as resolved
git add <file>
```

### Step 4: Verify resolution
```bash
# Check no conflicts remain
git status

# Run tests
pytest tests/ -v

# Test UI locally
docker compose up ui
# Visit http://localhost:8000
# Check all panels render
# Test auto-discovery trigger
# Test resume upload
# Test worker panel
```

### Step 5: Complete merge
```bash
git commit  # Will use auto-generated merge commit message
git push origin merge/resume-workers-to-main
```

### Step 6: Create GitHub PR
- Base: `main`
- Compare: `merge/resume-workers-to-main`
- Title: "Merge Worker/Resume UI panels and auto-discovery features"
- Description:
  ```
  This PR merges the Worker/Resume panel UI modernization from
  `feature/resume-and-workers` into `main`, which includes:

  **From feature/resume-and-workers:**
  - Worker panel for job tracking
  - Resume panel for resume management
  - Settings modal
  - UI modernization with lovable.dev design system
  - Enhanced CSS with variables
  - Better responsive design

  **From main (preserved):**
  - Automated job discovery feature
  - Auto-discovery API endpoints
  - Background scheduler integration
  - Resume-based search query extraction

  **Why this PR:**
  This enables PR #44 (toast notifications + CSS fixes) to be rebased
  properly, as it depends on the Worker/Resume panel structure.

  **Testing:**
  - [x] All 308 tests pass
  - [x] UI renders all panels correctly
  - [x] Auto-discovery works
  - [x] Resume upload works
  - [x] Worker tracking displays
  - [x] Manual discovery trigger works

  **Related:**
  - Closes #[issue number if applicable]
  - Enables PR #44 to be rebased
  ```

## Post-Merge Steps

After this PR is merged into main:

1. **Rebase PR #44:**
   ```bash
   git checkout copilot/fix-css-variables-add-toast-html
   git rebase main
   # Should apply cleanly now
   git push --force-with-lease
   ```

2. **Update PR #44 target:**
   - Change base from `fix/panel-css-variables` to `main`
   - PR should now show clean diff with just toast changes

3. **Test toast notifications:**
   - Worker panel should display toasts
   - Auto-discovery should trigger toasts
   - CSS variables should work correctly

## Estimated Time
- Conflict resolution: 30-45 minutes
- Testing: 15-20 minutes
- PR creation: 5 minutes
- **Total: ~1 hour**

## Need Help?
If stuck on a particular conflict:
1. Check `git diff <file>` to see both versions
2. Consult file history: `git log --oneline --graph --all <file>`
3. Test intermediate states frequently
4. Ask for review before final commit

## Automation Support
Consider creating a script to help with repetitive merges:
```bash
# merge_helper.sh
for file in $(git diff --name-only --diff-filter=U); do
    echo "Conflict in: $file"
    git diff $file | head -50
    read -p "Press enter to edit..."
    code $file
done
```
