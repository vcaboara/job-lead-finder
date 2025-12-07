# GitHub Copilot Instructions for JobFlow

## Project Overview
JobFlow is a job search application that helps users find relevant job postings using AI-powered matching and automated discovery.

## Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLite
- **Frontend**: Vanilla JavaScript, HTML/CSS (dark theme)
- **AI**: Google Gemini API for job matching and ranking
- **Job Sources**: Multiple providers (JSearch, WeWorkRemotely, CompanyJobs, Google Search)
- **Background Processing**: APScheduler for automated link discovery and cleanup
- **Container**: Docker with docker-compose (UI + Worker services)
- **Dependencies**: Managed via `pyproject.toml` with `uv` package manager

## Code Style & Patterns

### General
- **Comments/Documentation**: Keep concise - explain WHY not WHAT
- **PR Requirements**: Include UI screenshots for visual changes
- **Testing**: Use screenshots to verify no regressions before committing

### Python
- Use type hints for all function parameters and return types
- Follow PEP 8 naming conventions (snake_case for functions/variables)
- Prefer async/await for I/O operations
- Use dataclasses or Pydantic models for structured data
- Docstrings: Brief one-liner if obvious, detailed only when complex
- Use logging module (logger.debug/info/error), never print()
- Use proper exception handling with specific error messages
- Keep functions focused (single responsibility)

### JavaScript
- Use modern ES6+ syntax (const/let, arrow functions, async/await)
- Prefer fetch API for HTTP requests
- Use descriptive variable names (camelCase)
- Keep functions pure when possible
- Comments only for non-obvious logic

### CSS
- Use CSS variables for theming (defined in `:root`)
- Follow BEM-like naming for clarity
- Dark theme: navy backgrounds (#0f172a, #1e293b, #334155), teal/blue accents (#3b82f6, #06b6d4)
- Mobile-first responsive design
- Use flexbox/grid for layouts

## Architecture Patterns

### Service Separation
- **UI Server** (`ui_server.py`): FastAPI app serving web interface and API endpoints
- **Worker** (`worker.py`): Background scheduler for automated tasks (runs separately)
- **Shared Storage**: SQLite database and logs via Docker volumes

### Job Providers
- All providers implement `BaseDiscoveryProvider` interface
- Each provider has its own file in `src/app/`
- Use `mcp_providers.py` for MCP-based providers
- Fallback mechanism: primary → secondary providers

### Configuration
- Use `config_manager.py` for loading/saving user configs
- Store in `~/.config/job-lead-finder/config.json`
- Environment variables for API keys (`.env` file)

### Testing
- Use pytest for all tests
- Place tests in `tests/` directory matching source structure
- Mock external API calls
- Aim for >80% coverage on new code
- Test files follow `test_<module>.py` naming

## Common Tasks

### Adding a New Job Provider
1. Create `src/app/<provider_name>_provider.py`
2. Implement `BaseDiscoveryProvider` interface
3. Add tests in `tests/test_<provider_name>_provider.py`
4. Register in `job_finder.py` or `mcp_providers.py`
5. Update README with provider details

### Adding API Endpoints
1. Add route to `ui_server.py` with proper HTTP method
2. Use FastAPI dependency injection for common logic
3. Return JSON responses with proper status codes
4. Add error handling for expected failures
5. Update frontend JavaScript to call new endpoint

### Database Changes
1. Modify `job_tracker.py` for schema changes
2. Add migration logic if needed (check existing jobs)
3. Update tests to reflect new fields
4. Document breaking changes in PR

### Background Tasks
1. Add task function to `background_scheduler.py`
2. Schedule with `IntervalTrigger` in `start()` method
3. Use proper async/await patterns
4. Add rate limiting for external API calls
5. Log progress and errors appropriately

## Important Files
- `src/app/main.py`: CLI entry point
- `src/app/ui_server.py`: Web server and API
- `src/app/worker.py`: Background job processor
- `src/app/job_finder.py`: Main search orchestration
- `src/app/job_tracker.py`: Job persistence (SQLite)
- `src/app/gemini_provider.py`: AI-powered job matching
- `src/app/link_finder.py`: Direct link discovery from aggregators
- `src/app/background_scheduler.py`: Periodic task scheduling
- `src/app/templates/index.html`: Main UI (single-page app)

## Dependencies
- Add to `pyproject.toml` under appropriate section
- Use `uv pip install <package>` or `uv pip sync` in container
- Rebuild Docker image after pyproject.toml changes
- Pin versions for stability (e.g., `>=3.11.0`)

## Git Workflow
- Feature branches: `feature/<description>`
- Fix branches: `fix/<description>`
- Commits: Use conventional commits (feat:, fix:, chore:, docs:, refactor:)
- PRs:
  * Merge to `main` via pull request
  * **Include screenshots for any UI changes**
  * Verify no visual regressions with before/after screenshots
- Tags: Semantic versioning (v0.X.0 for features, v0.X.Y for fixes)

## What NOT to Do
- ❌ Don't use `from module import *`
- ❌ Don't ignore exceptions silently
- ❌ Don't hardcode API keys (use environment variables)
- ❌ Don't use `print()` for logging (use `logging` module)
- ❌ Don't mix tabs and spaces (use 4 spaces)
- ❌ Don't commit secrets or API keys
- ❌ Don't use `autopep8` (conflicts with project style)

## Debugging Tips
- Check logs: `docker compose logs ui --tail 50` or `docker compose logs worker --tail 50`
- Interactive shell: `docker compose exec ui /bin/bash`
- Run tests: `docker compose run app pytest`
- Check worker status: Verify it's processing jobs in logs

## Current Focus
- Dark theme UI with tab-based navigation (Search, Tracker, Resume)
- Background worker for automated link discovery
- Direct company application links from aggregator jobs
- Resume-based job matching and ranking
