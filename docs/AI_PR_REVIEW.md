# AI-Powered Pull Request Review

Automated code review using vibe-check-mcp integrated with GitHub Actions.

## Overview

Every pull request to `main` automatically triggers an AI-powered code review that:
- Analyzes changed files for code quality, best practices, and potential issues
- Applies comprehensive review criteria from `.github/copilot-instructions.md`
- Posts detailed feedback as PR comments
- Helps maintain code quality before human review

## How It Works

1. **Trigger**: PR opened/updated targeting `main` branch
2. **Analysis**: GitHub Actions workflow:
   - Fetches PR diff
   - Filters for reviewable files (`.py`, `.js`, `.ts`, etc.)
   - Calls vibe-check-mcp with review criteria
3. **Review**: vibe-check-mcp (using GPT-4o):
   - Analyzes code against quality standards
   - Identifies issues and suggests improvements
   - Generates structured review feedback
4. **Feedback**: Review posted as PR comment

## Review Criteria

The AI reviewer checks for:

### Code Structure
- Complex conditionals that could be simplified
- Deeply nested blocks
- Function size and single responsibility
- Control flow improvements

### Code Quality
- Simplicity and conciseness
- DRY principle adherence
- Modularity and clear boundaries
- Self-documenting code

### Best Practices
- Proper logging (not `print()`)
- Robust error handling
- Type hints and docstrings
- Resource management (context managers)

### Python-Specific
- Pythonic patterns (comprehensions, generators)
- Standard library usage
- Performance anti-patterns

### Architecture
- Separation of concerns
- Dependency management
- Scalability
- Testability

### Testing
- Coverage of critical paths
- Test quality and organization
- Proper mocking

## Configuration

### Required Secrets
- `OPENAI_API_KEY`: OpenAI API key for vibe-check-mcp

### Workflow File
`.github/workflows/ai-pr-review.yml`

### Review Criteria Source
`.github/copilot-instructions.md` (Rule: 02-pr-review-criteria.md section)

## Interpreting Reviews

AI reviews provide:

**Summary**: High-level assessment of changes

**Issues Found**: Specific problems with file/line references
- **File:Line** - Issue description and suggested fix

**Suggestions**: Optional improvements for code quality

**Approval Status**: Recommendation
- ✅ Approved: No critical issues
- 🔄 Changes Requested: Issues must be addressed
- 💬 Comment: Optional improvements suggested

## Limitations

- **Diff Size**: Reviews truncated at 50KB to avoid API limits
- **File Types**: Only reviews code files (`.py`, `.js`, `.ts`, etc.)
- **Context**: AI has limited understanding of full codebase context
- **False Positives**: May flag valid patterns; use human judgment

## Best Practices

1. **Review AI feedback**: Don't blindly accept/reject suggestions
2. **Verify context**: AI may miss project-specific requirements
3. **Use as first pass**: Human review still required
4. **Learn from patterns**: Recurring AI feedback indicates areas to improve

## Workflow Integration

The AI review complements (not replaces) human review:

1. **PR Created** → AI review runs automatically
2. **AI Posts Feedback** → Author reviews suggestions
3. **Author Updates PR** → AI re-reviews changes
4. **Human Reviewer** → Final approval with AI insights

## Troubleshooting

### Review Not Posted
- Check GitHub Actions logs for errors
- Verify `OPENAI_API_KEY` secret is set
- Ensure PR has changed files in supported types

### Review Seems Wrong
- Check if diff was truncated (>50KB)
- Verify review criteria in copilot-instructions.md
- Consider project-specific context AI may lack

### Performance Issues
- Large PRs (>50KB diff) are auto-truncated
- Consider breaking large changes into smaller PRs

## Future Enhancements

- [ ] Support for custom review criteria per PR label
- [ ] Integration with local vibe-check-mcp instance
- [ ] Review caching for unchanged files
- [ ] Inline code comments at specific lines
- [ ] Auto-fix suggestions via PR commits
- [ ] Integration with other LLM providers (Anthropic, Gemini)
