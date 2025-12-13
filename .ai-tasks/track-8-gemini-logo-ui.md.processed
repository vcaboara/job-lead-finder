# Task: Add Company Logo Placeholders to Job Search Results

## Assigned Agent: GEMINI

## Priority: P2 (UI Enhancement)

## Context:
This task improves the job-lead-finder UI by adding visual company logo placeholders. This prepares for future integration with lovable.dev for real company logos.

**📌 Reminder for @vcaboara**: Try using lovable.dev to design actual company logos.

## Task Requirements:

### 1. Implementation
Add circular logo placeholders next to each job listing in the search results.

**Files to modify:**
- `src/app/templates/index.html` - Add logo HTML structure
- Inline CSS or `<style>` block for logo styling

**Technical specs:**
- 48x48px circular placeholder
- Display company's first letter or initials
- Generate deterministic background color from company name (hash-based)
- Pure CSS/HTML (no external libs)
- Maintain responsive design

**Example output:**
```html
<div class="job-logo" style="background-color: #3498db;">
  <span>A</span> <!-- For "Acme Corp" -->
</div>
```

### 2. Token Compression (REQUIRED)
Follow `docs/AI_Coding_Style_Guide_prompts.toml` **level-2** guidelines:
- Concise variable names (e.g., `cLogo` not `companyLogoPlaceholder`)
- Minimal comments (code should be self-documenting)
- Document token savings in PR

### 3. Testing Requirements (MUST DO)
- [ ] **BEFORE screenshot**: Current UI without logos
- [ ] **AFTER screenshot**: New UI with logo placeholders
- [ ] Visual smoke test: `docker compose up -d; Start-Process 'http://localhost:8000'`
- [ ] Test various company names (short/long/special chars)
- [ ] Verify responsive on mobile/desktop
- [ ] Check browser DevTools console for errors

### 4. Documentation
- [ ] Update `CHANGELOG.md` under `[Unreleased] - Added`
- [ ] Add code comment: `// TODO: Replace with real logos from lovable.dev`
- [ ] PR description MUST include:
  - Before/after screenshots
  - Token count (before: X tokens, after: Y tokens, saved: Z%)
  - Browser tested (Chrome/Firefox/Safari)

## Success Criteria:
✅ Visual improvement verified with screenshots
✅ Token compression applied (level-2)
✅ All existing tests pass
✅ No console errors
✅ Approved by: Ollama → Copilot → Human

## Workflow:
```bash
# 1. Take BEFORE screenshot
Start-Process "http://localhost:8000"  # Screenshot this

# 2. Implement changes
# Edit src/app/templates/index.html

# 3. Test locally
docker compose up --build -d
Start-Process "http://localhost:8000"  # Screenshot this

# 4. Create branch and commit
git checkout -b auto/ui-company-logo-placeholders
git add src/app/templates/index.html CHANGELOG.md
git commit -m "feat: Add company logo placeholders to job listings

- Added 48px circular placeholders with company initials
- Deterministic colors based on company name hash
- Follows token compression guidelines (level-2)
- Includes before/after screenshots"

# 5. Push and create PR
git push -u origin auto/ui-company-logo-placeholders
```

## Review Process:
1. **Ollama** (local code review) - Check code quality and standards
2. **Copilot** (AI PR Review) - Verify contributor guidelines compliance
3. **Human** (@vcaboara) - Final approval and merge

## Reference Files:
- Contributor guidelines: `.github/CONTRIBUTING.md`
- Token compression: `docs/AI_Coding_Style_Guide_prompts.toml`
- Current UI template: `src/app/templates/index.html`

---
**Quick Start:**
Read CONTRIBUTING.md → Take screenshots → Code → Test → Commit → PR with images
