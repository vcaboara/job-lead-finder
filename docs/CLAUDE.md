# Claude AI Development Guide

This file guides AI assistants (like Claude) working on the Job Lead Finder project.

## 🔄 Project Awareness & Context

- Always read `docs/PLANNING.md` at the start of a new conversation to understand the project's architecture, goals, style, and constraints
- Check `docs/TASK.md` before starting a new task. If the task isn't listed, add it with a brief description and today's date
- Use consistent naming conventions, file structure, and architecture patterns as described in `docs/PLANNING.md`
- Use the virtual environment (`venv/Scripts/python.exe` on Windows) when executing Python commands

## 🧱 Code Structure & Modularity

- Never create a file longer than 500 lines of code. If approaching this limit, refactor into modules
- Organize code into clearly separated modules by feature:
  - `src/app/` - Main application code
  - `src/app/discovery/` - Company discovery system
  - `src/app/providers/` - Job search providers (Gemini, MCP)
  - `tests/` - Mirror the src structure
- Use clear, consistent imports (prefer relative imports within packages)
- Use `python-dotenv` and `load_dotenv()` for environment variables

## 🧪 Testing & Reliability

- Always create Pytest unit tests for new features
- After updating logic, check if existing tests need updates
- Tests should live in `/tests` folder mirroring `src/` structure
- Include at least:
  - 1 test for expected use
  - 1 edge case test
  - 1 failure case test
- Run tests before committing: `python -m pytest`

## ✅ Task Completion

- Mark completed tasks in `docs/TASK.md` immediately after finishing
- Add new sub-tasks or TODOs discovered during development to `docs/TASK.md` under "Discovered During Work"
- Use feature branches for new work, never commit directly to `main`

## 📎 Style & Conventions

- **Language**: Python 3.13
- **Formatting**: Black (line-length=120, double quotes)
- **Import sorting**: isort (black profile)
- **Type hints**: Always use type hints
- **Data validation**: Use Pydantic models
- **API framework**: FastAPI
- **Docstrings**: Google style for all functions:
  ```python
  def example(param1: str) -> dict:
      """Brief summary.

      Args:
          param1: Description.

      Returns:
          Description of return value.
      """
  ```

## 📚 Documentation & Explainability

- Update `README.md` when:
  - New features are added
  - Dependencies change
  - Setup steps are modified
- Document non-obvious code with inline comments
- For complex logic, add `# Reason:` comments explaining why

## 🧠 AI Behavior Rules

- Never assume missing context - ask questions if uncertain
- Never hallucinate libraries - only use verified Python packages
- Always confirm file paths exist before referencing them
- Never delete existing code unless explicitly instructed
- When using Git:
  - Create feature branches for new work
  - Never commit directly to `main`
  - Use descriptive commit messages

## 🎯 Project-Specific Guidelines

### Job Tracking
- Jobs stored in JSON file (`data/tracked_jobs.json`)
- Never auto-track jobs - user must explicitly click Track button
- Job IDs generated from link (or title+company as fallback)

### Discovery System
- Phase 1: Infrastructure (✅ Complete)
- Phase 2: JSearch provider (✅ Complete)
- Phase 3: Integration & UI (🔜 Next)
- Phase 4: Background monitoring (📋 Planned)

### API Keys
- `GEMINI_API_KEY` - For job search via Gemini
- `RAPIDAPI_KEY` - For JSearch provider
- All keys in `.env` file, never committed

### UI Server
- FastAPI backend at `http://localhost:8000`
- Templates in `src/app/templates/`
- No auto-tracking on search results
- Track button shows on `status='new'` jobs only

### Common Patterns
- Use `JobTracker` class for all job tracking operations
- Use `BaseDiscoveryProvider` interface for new providers
- Use Pydantic models for API request/response validation
- Handle errors gracefully with logging
