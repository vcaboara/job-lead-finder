# Job Lead Finder - Project Planning

## Project Overview

**Job Lead Finder** is a FastAPI-based web application that helps users discover job opportunities by:
1. Searching for jobs using AI (Gemini) or real job APIs (JSearch via RapidAPI)
2. Tracking job applications through a kanban-style workflow
3. Discovering companies passively through automated monitoring

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.13)
- **Frontend**: HTML/CSS/JavaScript (vanilla, no framework)
- **AI Provider**: Google Gemini AI
- **Job Discovery**: JSearch API (RapidAPI)
- **Data Storage**: JSON files (jobs), SQLite (discovered companies)
- **Testing**: Pytest

### Project Structure
```
job-lead-finder/
├── src/app/
│   ├── main.py              # CLI entry point
│   ├── ui_server.py         # FastAPI web server
│   ├── job_finder.py        # Job search logic
│   ├── job_tracker.py       # Job tracking & persistence
│   ├── providers/           # Job search providers
│   │   ├── gemini_provider.py
│   │   └── mcp_providers.py
│   ├── discovery/           # Company discovery system
│   │   ├── base_provider.py    # Abstract base class
│   │   ├── company_store.py    # SQLite storage
│   │   ├── config.py           # Configuration
│   │   └── providers/
│   │       └── jsearch_provider.py  # JSearch integration
│   ├── templates/
│   │   └── index.html       # Main UI
│   └── scripts/
│       └── test_jsearch.py  # JSearch testing tool
├── tests/                   # Unit tests (mirrors src/)
├── data/
│   ├── tracked_jobs.json    # Job tracking data
│   └── discovery.db         # Company database
├── docs/
│   └── JSEARCH_PROVIDER.md  # JSearch documentation
├── .env                     # API keys (not committed)
├── pyproject.toml           # Project config
└── README.md
```

## Core Features

### 1. Job Search
- **Gemini Provider**: Uses AI to generate job leads based on resume
- **MCP Providers**: Real job data from LinkedIn, Indeed, WeWorkRemotely
- **JSearch Provider**: Real-time job aggregation from multiple sources
- Search filters: query, count, location, date posted, employment type

### 2. Job Tracking
- **Statuses**: new → applied → interviewing → offer → accepted/rejected
- **Actions**: Track job, update status, add notes, hide job
- **Clear All**: Remove all tracked jobs with confirmation
- **Persistence**: JSON file storage
- **No auto-tracking**: User must explicitly click Track button

### 3. Company Discovery (NEW)
- **Phase 1**: ✅ Infrastructure (base classes, database, config)
- **Phase 2**: ✅ JSearch provider integration
- **Phase 3**: 🔜 UI integration & discovery service
- **Phase 4**: 📋 Background monitoring & notifications

## Design Decisions

### Why JSON for Job Tracking?
- Simple, human-readable
- No need for complex queries
- Easy backup/restore
- Sufficient for single-user application

### Why SQLite for Discovery?
- More structured data with relationships
- Better querying for company filtering
- Supports concurrent access for background jobs
- Standard for this type of data

### Why No Auto-Tracking?
- User should consciously decide which jobs to track
- Prevents cluttered tracking list
- Clear user intent (explicit Track button)
- Fixed in PR #24 (removed auto-tracking bug)

### Why Feature Branches?
- Keep `main` clean and deployable
- Easy to review changes
- Can work on multiple features in parallel
- Standard Git workflow

## Current State (Dec 2025)

### ✅ Completed
- Core job search with Gemini AI
- Job tracking system with JSON persistence
- FastAPI web UI with responsive design
- Track button (manual tracking only)
- Clear All button with confirmation
- MCP provider support (LinkedIn, Indeed, WeWorkRemotely)
- Discovery infrastructure (Phase 1)
- JSearch provider integration (Phase 2)
- Comprehensive test suite (252+ passing tests)

### 🔜 In Progress
- JSearch UI integration
- Discovery service for automated runs
- Background monitoring setup

### 📋 Planned
- Notifications for new discoveries
- Advanced company filtering
- Export/import functionality
- Resume parsing improvements

## Development Workflow

### Starting New Work
1. Check `docs/TASK.md` for current priorities
2. Create feature branch: `git checkout -b feature/description`
3. Read relevant documentation in `docs/`
4. Write tests first (TDD approach)
5. Implement feature
6. Run full test suite: `pytest`
7. Format code: `black . && isort .`
8. Commit with clear message
9. Push and create PR (don't merge to main directly)

### Testing
- Run all tests: `python -m pytest`
- Run specific test: `python -m pytest tests/test_file.py::test_name`
- Run with coverage: `python -m pytest --cov=src`
- Tests must pass before merging

### Code Style
- Black formatter (line-length=120, double quotes)
- isort for imports (black profile)
- Type hints for all functions
- Pydantic models for validation
- Google-style docstrings

## API Keys & Environment

Required in `.env`:
```bash
GEMINI_API_KEY=your_gemini_key        # For AI job search
RAPIDAPI_KEY=your_rapidapi_key        # For JSearch provider
```

Optional:
```bash
LINKEDIN_MCP_URL=...                  # MCP provider URLs
INDEED_MCP_URL=...
```

## Common Tasks

### Run Development Server
```bash
python -m src.app.ui_server
# Visit http://localhost:8000
```

### Test JSearch Provider
```bash
python -m src.app.scripts.test_jsearch \
    --query "python developer" \
    --location "remote" \
    --limit 20
```

### Clear Tracked Jobs
```bash
# Via UI: Click "Clear All" button
# Or manually delete: data/tracked_jobs.json
```

### Run Tests
```bash
# All tests
python -m pytest

# Specific module
python -m pytest tests/test_jsearch_provider.py

# With verbose output
python -m pytest -v
```

## Known Issues & Gotchas

### Git Workflow
- ❌ Don't commit to `main` directly
- ✅ Create feature branches
- ✅ Use descriptive commit messages

### Formatters
- Using Black only (removed autopep8 to avoid conflicts)
- Double quotes configured explicitly
- Run before committing: `black . && isort .`

### Job Tracking
- Track button only shows on `status='new'` jobs
- After tracking, button replaced with status dropdown
- Jobs without links use title+company for ID generation

### Discovery System
- JSearch requires RAPIDAPI_KEY
- Rate limits depend on RapidAPI plan
- Companies deduplicated by name
- Tech stack detection is keyword-based (30+ technologies)

## Resources

- [JSearch Provider Documentation](docs/JSEARCH_PROVIDER.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
