# Pull Request Review Strategy

## The Problem: Unreviewable PRs

**PRs over 1,000 lines are effectively unreviewable.**

A developer can realistically review 200-500 lines of code thoroughly in a single sitting (20-30 minutes). Large PRs lead to:

- Superficial reviews ("LGTM" without deep analysis)
- Review fatigue (giving up halfway)
- Delayed feedback (putting off the review)
- Missed bugs and security issues

## The Solution: Split and Prioritize

### 1. Split Large PRs by Type

When creating a feature with >1,000 lines:

**Create separate PRs:**

- **PR 1: Core Logic (300-900 lines)** - Ready for review
- **PR 2: Documentation (any size)** - Draft or merge after core
- **PR 3: Examples/Tests (any size)** - Optional, merge after core

**Example from this project:**

- PR #92: 3,193 lines (too large) → Split into:
  - PR #93: 899 lines core tool ✅ Ready for review
  - PR #92: Draft with full docs (merge after #93)

### 2. Add Review Guidance to Every Large PR

**For PRs >500 lines, add a comment:**

```markdown
## Review Guidance: Focus on [Core Feature]

**This PR is X lines** - but most are [tests/docs/boilerplate].

### What to Review (Priority)

**Core Logic (~300 lines):**
- file1.py (~150 lines) - Main feature
- file2.py (~100 lines) - Integration
- file3.py (~50 lines) - API endpoint

**Review for:**
- [Key design decision 1]
- [Key design decision 2]
- Security considerations
- Error handling

### What to Skim

**Tests (~X lines):**
- Just verify they exist and pass
- Check test names make sense

**Documentation (~X lines):**
- Skim for completeness
- Don't read line-by-line

### Recommendation

**Focus your 15-20 minutes on:**
1. [Most critical file]
2. [Second most critical aspect]
3. [Security/error handling]
```

### 3. Review Core Logic Only

**As a reviewer, focus on:**

- **Architecture**: Does it fit the system design?
- **Security**: Input validation, authentication, authorization?
- **Error handling**: What happens when things fail?
- **Integration**: How does it connect to existing code?
- **Maintainability**: Can someone else understand this in 6 months?

**Don't focus on:**

- **Tests**: Verify they exist and pass (CI), but don't review assertions line-by-line
- **Documentation**: Skim for completeness, reference later when using the feature
- **Examples**: Glance to confirm they work, don't analyze deeply
- **Boilerplate**: Config files, type hints, standard patterns

## Real-World Examples from This Project

### PR #89: Email Webhook Implementation (4,250 lines)

**Breakdown:**

- Core logic: ~500 lines (email_webhook.py, email_parser.py)
- Tests: ~1,500 lines
- Documentation: ~200 lines
- Fixtures: ~2,000 lines (test data)

**Review guidance:**

- Focus 15-20 minutes on webhook manager and email parser
- Skim tests (18 tests exist, they pass)
- Skip documentation (reference material)

### PR #90: Email Integration (@copilot) (1,489 lines)

**Breakdown:**

- Core logic: ~300 lines (email_processor.py)
- Tests: ~600 lines (35 tests)
- Fixtures: ~400 lines (5 .eml files)
- Documentation: ~200 lines

**Review guidance:**

- Focus 15-20 minutes on EmailProcessor integration
- Skim tests (check they pass)
- Glance at one fixture to understand format
- Skim docs for completeness

### PR #93: Ollama Code Assistant Core (899 lines)

**Breakdown:**

- Core script: 580 lines (ollama_code_assistant.py)
- Quick reference: 317 lines (command cheat sheet)
- README: 2 lines (links)

**Review guidance:**

- Focus 20 minutes on OllamaAssistant class and main features
- Skim quick reference for command coverage
- Verify README links work

**PR #92 (draft):** Full documentation (2,294 lines) - merge after #93 approved, no line-by-line review needed.

## Guidelines for Future Work

### When Creating PRs

1. **Keep core PRs under 1,000 lines** (ideally 300-700)
2. **Separate docs/examples** into follow-up PRs or mark as draft
3. **Always add review guidance** for PRs >500 lines
4. **Highlight key decisions** in PR description

### When Reviewing PRs

1. **Read the guidance comment first** (if it exists)
2. **Focus on core logic files** (usually 2-5 files)
3. **Verify tests pass** (don't review line-by-line)
4. **Skim documentation** (reference material)
5. **Budget 20-30 minutes max** per PR

### When a PR is Too Large

**As author:**

1. Create a new branch from main
2. Cherry-pick only core files
3. Create "core-only" PR
4. Mark original PR as draft
5. Add note directing to core PR

**As reviewer:**

1. Request PR split if >1,500 lines
2. Ask for review guidance if missing
3. Focus on core logic only
4. Note: "Tests look good (verified they pass)" rather than reviewing assertions

## Success Metrics

**Before this strategy:**

- PR #92: 3,193 lines → "Am I really expected to review this?"
- Review time: Hours (or never)
- Review quality: Superficial or incomplete

**After this strategy:**

- PR #93: 899 lines core → 20 minutes focused review
- PR #89: 500 lines core logic (guidance provided) → 15 minutes
- PR #90: 300 lines core logic (guidance provided) → 15 minutes
- Total review time: 50 minutes for 3 focused reviews
- Review quality: Deep analysis of critical code

## Benefits

1. **Faster reviews**: 15-20 minutes instead of hours
2. **Better quality**: Focus on what matters
3. **Less fatigue**: Bite-sized chunks
4. **Clearer feedback**: Targeted to core logic
5. **Easier merges**: Smaller diffs = fewer conflicts

## References

- Google Engineering Practices: ["Small CLs"](https://google.github.io/eng-practices/review/developer/small-cls.html)
- Microsoft Code Review Best Practices: "Limit review size to 200-400 lines"
- Atlassian: "Best Pull Request Size: 250 lines or less"

---

**Last Updated**: 2025-06-11
**Based on**: PRs #89, #90, #92, #93 review experience
