# GitHub Copilot Work Creation Guide

## Overview

This guide documents the working patterns for creating tasks for GitHub Copilot agents, as discovered through practical testing in the job-lead-finder project (December 2025).

## What Works (Verified)

### 1. Issue-Based Task Creation

**Pattern**: Use `@github-copilot` in issue body or comments

**Example Structure**:
```markdown
## Agent Assignment
@github-copilot

## Goal
[Clear description of what needs to be accomplished]

## Requirements
1. Specific requirement 1
2. Specific requirement 2
3. ...

## Implementation Steps
1. Step 1 with technical details
2. Step 2 with expected outcomes
3. ...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Estimated Effort
X hours, Y tokens
```

**Real Example** (Issue #97):
```markdown
@github-copilot Please implement this framework extraction with vibe-coding integration:

## Phase 1: Create ai-search-match-framework Repo
Estimated time: 3-4 hours
Cost: 1 premium token

### Repository Structure
- Create vcaboara/ai-search-match-framework
- Initialize with 5-stage vibe-coding structure
- Extract core components from job-lead-finder
- Generate AGENTS.md (Stage 4 - currently missing)
- Setup submodule-friendly structure

### Core Components to Extract
1. AI Orchestration (mcp_providers.py, ollama_provider.py)
2. Search Infrastructure (search_engine.py, web_scraper.py)
3. UI Framework (ui_server.py, templates/)
4. Configuration Management (config_manager.py)

### Documentation Requirements
- README with use cases
- API documentation
- Integration guide
- Extension patterns
```

### 2. PR-Based Code Review

**Pattern**: Use `@copilot` in PR comments

**Example**:
```markdown
@copilot please review this PR for:
- Code quality and best practices
- Architecture alignment
- Security considerations
- Documentation completeness
```

**Behavior**:
- Responds in PR comments
- Creates new PRs with proposed changes
- Uses format: PR #99 (response to PR #98)

### 3. Issue Comment Updates

**Pattern**: Use `@copilot` in comments for additional context

**Example**:
```markdown
@copilot Update: After reviewing the architecture, please also:

1. Add support for X feature
2. Ensure compatibility with Y
3. Include tests for Z scenarios
```

## What Doesn't Work

- **Copilot Workspace**: Technical preview ended May 30, 2025
- **Direct repo creation**: Copilot cannot create new repositories directly
- **Cross-repo operations**: Limited to single repository context

## Multi-Model Orchestration Strategy

Based on Ollama/Gemma 3:4b feedback, consider using different models for different task types:

### Model Selection Matrix

| Task Type | Recommended Model | Rationale | Usage Pattern |
|-----------|------------------|-----------|---------------|
| **GitHub Task Creation** | GitHub Copilot | Integrated with GitHub, 1 token per task | Use @copilot for PRs, @github-copilot for issues |
| **Iterative Refinement** | Local Ollama (qwen2.5-coder:32b) | Free, fast, private | Use for code optimization, refactoring |
| **Architecture Design** | Gemini Flash 2.0 | Strong reasoning, diagram generation | Use for system design, component relationships |
| **Code Review** | Local Ollama (deepseek-coder:33b) | Algorithm optimization, pattern detection | Use for detailed code analysis |
| **Rapid Prototyping** | Local Ollama (codellama:34b) | Fast code generation | Use for quick experiments |

### Workflow Integration

```mermaid
flowchart TD
    Start[Task Requirement] --> Decision{Task Complexity}

    Decision -->|New Feature/Repo| Copilot[@github-copilot in Issue]
    Decision -->|Code Review| CopilotPR[@copilot in PR Comment]
    Decision -->|Refinement| Ollama[Local Ollama]
    Decision -->|Architecture| Gemini[Gemini Flash 2.0]

    Copilot --> CopilotPR
    CopilotPR --> Ollama
    Ollama --> Verify{Verification}
    Gemini --> Ollama

    Verify -->|Pass| Complete[Complete]
    Verify -->|Fail| Ollama
```

### Cost Optimization

1. **Use @copilot for creation** (1 token): Initial task setup, repo scaffolding, comprehensive features
2. **Use local Ollama for iteration** (free): Code refinement, bug fixes, optimizations
3. **Use Gemini for analysis** (free tier available): Architecture review, system design validation

### Example Multi-Model Workflow

**Scenario**: Extract ai-search-match-framework from job-lead-finder

**Step 1 - Creation** (GitHub Copilot - 1 token):
```markdown
@github-copilot Create ai-search-match-framework with:
- Vibe-coding 5-stage structure
- Core components extracted from job-lead-finder
- Comprehensive documentation
```

**Step 2 - Refinement** (Local Ollama - free):
```bash
uv run python tools/llm_api.py --provider ollama --model qwen2.5-coder:32b \
  --prompt "Review framework code for optimization opportunities"
```

**Step 3 - Validation** (Gemini - free):
```bash
uv run python tools/llm_api.py --provider gemini \
  --prompt "Analyze framework architecture for scalability and maintainability"
```

## Best Practices

### 1. Clear Task Scoping
- Break large tasks into phases
- Estimate time and token cost
- Provide acceptance criteria

### 2. Context Management
- Reference existing files/PRs
- Include relevant documentation links
- Specify branch names and PR targets

### 3. Iterative Validation
- Review @copilot output before merging
- Use local models for quick iterations
- Cross-validate with different models

### 4. Documentation
- Document @copilot tasks in issues
- Track premium token usage
- Record lessons learned in copilot-instructions.md

## Token Usage Tracking

| Task Type | Estimated Tokens | Model |
|-----------|-----------------|-------|
| New repo creation | 1 | GitHub Copilot |
| Feature implementation | 1 | GitHub Copilot |
| PR review + changes | 1 | GitHub Copilot |
| Code refinement | 0 | Local Ollama |
| Architecture review | 0 | Gemini (free tier) |

## Current Project Usage

- **Issue #97**: Framework extraction (1 token, in progress)
- **PR #98**: MCP services (@copilot responded, created PR #99)
- **PR #99**: Copilot-generated improvements (WIP)

## Future Enhancements

1. **Automated task routing**: Script to determine which model to use based on task type
2. **Cost tracking dashboard**: Monitor premium token usage across issues/PRs
3. **Multi-model validation pipeline**: Automatically validate Copilot output with local models
4. **Template library**: Pre-formatted @copilot prompts for common tasks

## Related Documentation

- `.github/copilot-instructions.md` - AI assistant guidelines
- `docs/FRAMEWORK_EXTRACTION.md` - Framework extraction plan (uses @copilot)
- `memory/docs/architecture.md` - System architecture context
- `tools/llm_api.py` - Local LLM integration

## References

- GitHub Copilot Documentation: https://docs.github.com/en/copilot
- Issue #97: Framework extraction example
- PR #98/#99: PR-based @copilot usage pattern
