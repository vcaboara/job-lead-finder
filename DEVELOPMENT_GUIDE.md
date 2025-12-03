# Modern Development Workflow Guide (2025)

This guide teaches you the **current best practices** for software development, using job-lead-finder as a real example.

## Table of Contents
1. [Development Philosophy](#development-philosophy)
2. [The Feature Development Cycle](#the-feature-development-cycle)
3. [Tools & Automation](#tools--automation)
4. [Testing Strategy](#testing-strategy)
5. [Code Review Process](#code-review-process)
6. [Deployment & Monitoring](#deployment--monitoring)

---

## Development Philosophy

### 2025 Best Practices

**1. Small, Incremental Changes**
- PRs should be 200-400 lines max
- One feature = one PR
- Easy to review, fast to merge

**2. Test Everything**
- Write tests BEFORE code (TDD)
- Aim for 80%+ coverage
- Tests are documentation

**3. Automation First**
- Use AI tools (Copilot, ChatGPT) for boilerplate
- Automate repetitive tasks (scripts, aliases)
- Let machines do machine work

**4. Documentation as Code**
- README explains how to run
- CHANGELOG tracks what changed
- Code comments explain WHY, not WHAT

---

## The Feature Development Cycle

### Phase 1: Planning (5-10 min)

**What you're doing:** Understanding the problem before writing code

**Example: Format-specific file size limits**
```powershell
# 1. Check the TODO list
Get-Content TODO.md

# 2. Pick something small with high value
# - Risk: Low (just validation)
# - Reward: High (security + UX)
# - Scope: 1 file, ~30 lines

# 3. Break it down into steps
# Step 1: Add size constants
# Step 2: Update validation logic  
# Step 3: Add tests (5 new tests)
# Step 4: Update docs
```

**Modern tools:**
- Use Copilot Chat: "Analyze TODO.md and suggest next task"
- AI can help prioritize and break down work

### Phase 2: Setup (1-2 min)

**What you're doing:** Creating isolated workspace for your feature

```powershell
# Create feature branch from current branch
gcb feature/format-size-limits

# Or from main
gco main
gpl  # Pull latest
gcb feature/format-size-limits
```

**Why branches:**
- Isolates your work from others
- Easy to throw away if wrong direction
- Clean history when merged

### Phase 3: Development (20-60 min)

**What you're doing:** Write code + tests together

**Modern workflow (TDD - Test Driven Development):**

```powershell
# 1. Write the test FIRST
# File: tests/test_upload_resume.py
```

```python
def test_upload_pdf_too_large():
    """Test uploading a PDF file larger than 2MB limit."""
    # This test will FAIL initially - that's good!
    client = TestClient(app)
    large_pdf = create_fake_pdf(size_mb=3)  
    
    resp = client.post("/api/upload/resume", files=...)
    assert resp.status_code == 400
    assert "PDF" in resp.json()["detail"]
    assert "2MB" in resp.json()["detail"]
```

```powershell
# 2. Run the test - it SHOULD fail
jl-test tests/test_upload_resume.py::test_upload_pdf_too_large

# 3. NOW write the code to make it pass
# File: src/app/ui_server.py
```

```python
MAX_PDF_SIZE = 2 * 1024 * 1024  # 2MB

if file.filename.endswith(".pdf") and len(content) > MAX_PDF_SIZE:
    raise HTTPException(
        status_code=400,
        detail=f"PDF file too large (max 2MB, got {len(content)/1024/1024:.1f}MB)"
    )
```

```powershell
# 4. Run test again - it should PASS
jl-test tests/test_upload_resume.py::test_upload_pdf_too_large

# 5. Run ALL tests to make sure nothing broke
jl-test
```

**Why TDD:**
- Prevents over-engineering
- Ensures code is testable
- Tests become your safety net

### Phase 4: Local Testing (5-10 min)

**What you're doing:** Manual verification before committing

```powershell
# 1. Reload the UI to see changes
jl-reload -Logs

# 2. Test manually
jl-upload large-file.pdf
# Should see: "PDF file too large (max 2MB, got 2.3MB)"

# 3. Test happy path
jl-upload normal-resume.pdf
# Should work fine

# 4. Check for errors
jl-logs
```

**Modern approach:**
- Automated tests catch bugs
- Manual testing verifies UX
- Both are important!

### Phase 5: Commit & Push (2-3 min)

**What you're doing:** Saving your work with clear history

```powershell
# 1. Check what changed
gs
gd

# 2. Stage everything
gaa

# 3. Commit with conventional commit message
gcm "feat: add format-specific file size limits

- Text files: 1MB limit
- PDF files: 2MB limit  
- DOCX files: 1MB limit
- Better error messages with file type
- 5 new tests, all passing"

# 4. Push to GitHub
gpu
```

**Conventional commits format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding tests
- `refactor:` - Code restructure, no functionality change
- `chore:` - Build/tooling changes

**Why this matters:**
- Clear history
- Auto-generate CHANGELOG
- Tools can parse commits (semantic versioning)

### Phase 6: Pull Request (5 min)

**What you're doing:** Requesting code review

```powershell
# Create PR (base branch is where you want to merge TO)
ghpr feature/enhanced-resume-upload "feat: Format-specific file size limits" "Implements format-specific limits: 1MB (txt/md), 2MB (PDF), 1MB (DOCX). Improves security and UX. 5 new tests passing."
```

**PR best practices 2025:**
- Small PRs (< 400 lines)
- Descriptive title following conventional commits
- Include: what changed, why, how to test
- Link to issues/TODOs if applicable

**What happens next:**
1. CI/CD runs automated tests
2. AI reviewer (Copilot) analyzes code
3. Human reviewers provide feedback
4. You address feedback (new commits to same branch)
5. Merge when approved!

### Phase 7: Code Review Response (varies)

**What you're doing:** Addressing feedback professionally

**Example workflow:**
```powershell
# Copilot left 3 comments on your PR

# Read comments on GitHub
ghprv 27

# Make fixes on same branch
# Edit files...

# Commit fixes
gcm "fix: address code review feedback

- Optimize DOCX reading (single pass)
- Add XSS pattern detection
- Fix typo in error message"

# Push - PR updates automatically!
gp
```

**Modern code review:**
- AI catches obvious issues (linting, patterns)
- Humans review logic, architecture, UX
- Be open to feedback - it makes code better!

---

## Tools & Automation

### Essential Tools (2025 Stack)

**Version Control:**
- Git - Track changes
- GitHub - Collaboration platform
- GitHub CLI (`gh`) - Create PRs from terminal

**Development Environment:**
- VS Code - Modern IDE
- GitHub Copilot - AI pair programmer
- Docker - Consistent environments

**Python Ecosystem:**
- `uv` - Fast package manager (replaces pip)
- `pytest` - Testing framework
- `ruff` - Fast linter/formatter

**Automation:**
- PowerShell aliases - Reduce typing
- Custom scripts - Common workflows
- Docker Compose - Multi-container apps

### Your New Workflow

**Instead of this:**
```powershell
# Old way - lots of typing
git checkout -b feature/new-thing
# ... make changes ...
git add -A
git commit -m "add new thing"
git push -u origin feature/new-thing
cd "C:\Program Files\GitHub CLI"
.\gh.exe pr create --base main --title "New thing" --body "Adds a new thing"
```

**Do this:**
```powershell
# New way - with aliases!
gcb feature/new-thing
# ... make changes ...
gaa
gcm "feat: add new thing"
gpu
ghpr main "feat: New thing" "Adds a new thing"
```

**Saved:** 5 minutes per feature × 50 features/month = 4+ hours/month!

---

## Testing Strategy

### The Testing Pyramid (2025 Edition)

```
        /\
       /E2E\       10% - End-to-end (slow, fragile)
      /------\
     /Integr.\    20% - Integration (medium speed)
    /----------\
   /Unit Tests \  70% - Unit tests (fast, reliable)
  /--------------\
```

**Unit Tests:** Test individual functions
```python
def test_check_file_size():
    assert check_file_size(1024, MAX_SIZE=2048) == True
    assert check_file_size(3000, MAX_SIZE=2048) == False
```

**Integration Tests:** Test components working together
```python
@pytest.mark.integration  
def test_upload_pdf_extracts_text():
    # Tests: file upload + PDF parsing + text extraction
    resp = client.post("/api/upload/resume", files=pdf_file)
    assert "Python Developer" in resp.json()["resume"]
```

**E2E Tests:** Test full user workflows
```python
def test_complete_job_search_workflow():
    # 1. Upload resume
    # 2. Search for jobs
    # 3. Save leads
    # 4. Verify results
```

### When to Write Tests

**ALWAYS:**
- New features (test before code - TDD)
- Bug fixes (test reproduces bug, then fix it)
- Public APIs (these are contracts)

**SOMETIMES:**
- Refactoring (if coverage is low)
- Edge cases (as you discover them)

**NEVER:**
- Private implementation details
- Third-party code
- Trivial getters/setters

### Running Tests Efficiently

```powershell
# Run specific test
jl-test tests/test_upload_resume.py::test_upload_pdf_too_large

# Run all tests in a file
jl-test tests/test_upload_resume.py

# Run tests matching a pattern
jl-test -k "upload"

# Run with coverage
jl-cov

# Run only fast tests (skip integration)
jl-test -m "not integration"
```

---

## Code Review Process

### What Reviewers Look For

**1. Functionality**
- Does it work?
- Are there edge cases missed?
- Is error handling complete?

**2. Tests**
- Do tests cover new code?
- Are tests meaningful (not just for coverage)?
- Do all tests pass?

**3. Code Quality**
- Is it readable?
- Is it maintainable?
- Is it consistent with existing code?

**4. Performance**
- Are there obvious bottlenecks?
- Does it scale reasonably?

**5. Security**
- Input validation?
- Injection vulnerabilities?
- Authentication/authorization?

### Responding to Feedback

**Good responses:**
```
"Good catch! Fixed in abc123."
"Interesting point. I chose X because Y. Thoughts?"
"Not sure I understand - could you clarify?"
```

**Bad responses:**
```
"This works fine, no changes needed."
"That's not my job."
"Whatever, I'll change it."
```

**Remember:** Code review makes EVERYONE better, including reviewers!

---

## Deployment & Monitoring

### Local Development

```powershell
# Start services
jl-up

# Check logs
jl-logs

# Reload after changes
jl-reload

# Stop everything
jl-down
```

### Production Deployment (Typical 2025 Stack)

**1. CI/CD Pipeline (GitHub Actions)**
```yaml
# .github/workflows/deploy.yml
on: [push]
jobs:
  test:
    - Run linter
    - Run tests  
    - Check coverage
  
  deploy:
    - Build Docker image
    - Push to registry
    - Deploy to cloud
```

**2. Container Orchestration (Docker/Kubernetes)**
```bash
# Deploy new version
kubectl apply -f deployment.yaml
kubectl rollout status deployment/job-finder

# Rollback if needed
kubectl rollout undo deployment/job-finder
```

**3. Monitoring**
- Logs: Datadog, CloudWatch, ELK Stack
- Metrics: Prometheus, Grafana
- Errors: Sentry, Rollbar
- Uptime: Pingdom, UptimeRobot

---

## Quick Reference: Complete Feature Workflow

```powershell
# 1. Plan
# Read TODO.md, pick a task

# 2. Create branch
gcb feature/my-feature

# 3. TDD - Write test first
# Edit: tests/test_my_feature.py
jl-test tests/test_my_feature.py  # Should fail

# 4. Write code to pass test
# Edit: src/app/my_feature.py
jl-test tests/test_my_feature.py  # Should pass

# 5. Run all tests
jl-test  # Everything should pass

# 6. Test manually
jl-reload
# Try it in the UI

# 7. Commit & push
gaa
gcm "feat: add my feature

- Details about what changed
- Why it's needed
- Test coverage added"
gpu

# 8. Create PR
ghpr main "feat: My feature" "Description of changes"

# 9. Address review feedback
# Make changes...
gaa
gcm "fix: address review feedback"
gp

# 10. Merge!
# After approval, merge on GitHub
```

---

## Learning Resources

**Modern Dev Practices:**
- [12 Factor App](https://12factor.net/) - Principles for web apps
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message standard
- [TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html) - Test Driven Development

**Python Specific:**
- [Real Python](https://realpython.com/) - Tutorials
- [Effective Python](https://effectivepython.com/) - Best practices book
- [Python Speed](https://pythonspeed.com/) - Performance tips

**Tools:**
- [GitHub Skills](https://skills.github.com/) - Interactive tutorials
- [Docker Tutorial](https://docker-curriculum.com/) - Container basics
- [VS Code Tips](https://code.visualstudio.com/docs) - Official docs

---

## Your Next Steps

1. **Practice the workflow** - Try creating a small feature end-to-end
2. **Use the aliases** - They'll become muscle memory
3. **Read code daily** - Best way to learn patterns
4. **Ask questions** - Use Copilot Chat for quick answers
5. **Ship small, ship often** - Better than one big perfect thing

**Remember:** Modern development is about **speed** + **quality** through **automation** + **collaboration**.

You're not writing code alone anymore - you have:
- AI assistants (Copilot)
- Automation scripts (aliases, Docker)
- Version control (Git)
- Team collaboration (GitHub)
- Automated testing (pytest)

Use all the tools. Ship great things. Have fun! 🚀
