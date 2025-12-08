# Job Lead Finder

AI-powered job search tool aggregating jobs from multiple providers including WeWorkRemotely, RemoteOK, Remotive, and direct company career pages.

## Quick Links

📚 **Getting Started**
- [Personal Configuration Guide](docs/PERSONAL_CONFIG_GUIDE.md) - API keys and environment setup
- [Ollama Setup Guide](docs/OLLAMA_SETUP.md) - Local AI setup for unlimited job evaluations

🏗️ **Architecture & Planning**
- [Project Planning](docs/PLANNING.md) - Project overview, architecture, and structure
- [Provider Architecture](docs/PROVIDERS.md) - How job providers work
- [Strategic Analysis](docs/STRATEGY.md) - Technical decisions and architecture analysis
- [Company Discovery Plan](docs/COMPANY_DISCOVERY_PLAN.md) - Feature implementation details

🔧 **Technical Documentation**
- [JSearch Provider](docs/JSEARCH_PROVIDER.md) - Company discovery implementation
- [Discovery CLI](docs/DISCOVERY_CLI.md) - Command-line interface for company discovery
- [Company Discovery Guide](docs/AGGREGATOR_TO_COMPANY_GUIDE.md) - Using the JSearch integration

🤖 **AI & Development**
- [Claude AI Guide](docs/CLAUDE.md) - Guidelines for AI assistants working on this project
- [Rulebook-AI Integration](docs/RULEBOOK_INTEGRATION.md) - AI assistant context management
- [GitHub Integration](docs/GITHUB_RULEBOOK_INTEGRATION.md) - GitHub Actions and Copilot setup
- [Versioning Workflow](docs/VERSIONING.md) - Automated semantic versioning with GitHub Actions

📋 **Planning & Roadmap**
- [Task Tracker](docs/TASK.md) - Current development tasks and sprint planning
- [TODO & Technical Debt](docs/TODO.md) - Known issues and improvements
- [UI Improvements](docs/UI_IMPROVEMENTS_TODO.md) - UI/UX enhancement roadmap
- [Future Enhancements](docs/FUTURE_ENHANCEMENTS.md) - Long-term feature ideas
- [Changelog](CHANGELOG.md) - Version history and release notes

## Features

- **Job Aggregation**: WeWorkRemotely + RemoteOK + Remotive + CompanyJobs (Gemini-powered company career page search)
- **Company Discovery**: Passive job discovery via JSearch API (RapidAPI)
- **Job Tracking**: Track application status through the entire hiring funnel
- **Web UI**: FastAPI dashboard at http://localhost:8000
- **Enhanced Resume Upload**: Multi-format support (.txt, .md, .pdf, .docx) with security scanning
- **AI Features**: Job evaluation, custom cover letter generation
- **Docker**: Fully containerized

## Quick Start

### Web UI (Recommended)

1. **Start the server**:
   ```powershell
   docker compose up ui
   ```

2. **Open browser**: http://localhost:8000

3. **Configure** (optional):
   - Set `GEMINI_API_KEY` for AI features (cover letters, CompanyJobs search)
   - Get key: https://aistudio.google.com/app/apikey
   - Set `RAPIDAPI_KEY` for company discovery via JSearch
   - Get key: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

### CLI Usage

```powershell
# Job search
uv run python -m app.main find -q "remote python developer" --resume "Your resume" -n 10

# Company discovery (requires RAPIDAPI_KEY in .env)
uv run python -m app.main discover -q "Python developer" -l "San Francisco" -n 10
uv run python -m app.main discover -q "DevOps engineer" -l "Remote" --save  # Save to DB
uv run python -m app.main discover -q "ML engineer" --tech-stack Python TensorFlow -n 20

# Health check
uv run python -m app.main health

# Traditional installation
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[web,gemini]

# Job search
python -m app.main find -q "remote python developer" --resume "Your resume" -n 10

# Company discovery
python -m app.main discover -q "Python developer" -l "Remote" -n 10 --save
```

## Environment Setup

Create a `.env` file in the project root:

```bash
# Optional: For AI-powered job evaluation and cover letters
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For company discovery via JSearch
RAPIDAPI_KEY=your_rapidapi_key_here
```

**Get API Keys**:
- Gemini: https://aistudio.google.com/app/apikey
- RapidAPI (JSearch): https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

## Development

**Setup with uv** (recommended):
```powershell
# Install uv: https://github.com/astral-sh/uv
winget install --id=astral-sh.uv -e

# Sync all dependencies (creates .venv automatically)
uv sync --all-extras

# Run tests (no venv activation needed)
uv run pytest -v -m "not slow"  # Fast tests (~8s)
uv run pytest -v               # All tests

# Add new dependencies
uv add package-name
uv add --dev package-name  # dev dependencies
```

**Traditional setup**:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[web,gemini,dev,test]
pytest -v -m "not slow"  # Fast tests (~8s)
pytest -v               # All tests including slow ones
```

**Pre-commit hooks**:
```powershell
pre-commit install
```

## Project Structure

```
src/app/
├── main.py              # CLI entry point (find, discover, probe, health)
├── ui_server.py         # FastAPI REST API + web UI
├── job_finder.py        # Job search orchestration
├── job_tracker.py       # Track applications and status
├── mcp_providers.py     # WeWorkRemotely, RemoteOK, Remotive, CompanyJobs
├── gemini_provider.py   # AI provider (evaluation, cover letters)
├── link_validator.py    # URL validation
├── industry_profiles.py # 8 industry-specific company lists
├── config_manager.py    # Configuration management
├── discovery/           # Company discovery system
│   ├── base_provider.py    # Abstract provider interface
│   ├── company_store.py    # SQLite database for companies
│   ├── config.py           # Discovery configuration
│   └── providers/
│       └── jsearch_provider.py  # JSearch API integration
└── templates/           # HTML templates

tests/                   # 259 passing tests (13 for JSearch)
data/
├── tracked_jobs.json    # Job tracking persistence
└── discovery.db         # Discovered companies database
```

## Configuration

- **Web UI**: 5-tab config interface (Industry, Providers, Location, Search, Blocked)
- **API**: `GET /api/job-config`, `POST /api/job-config/search`
- **File**: `config.json` (auto-created, gitignored)

See [PERSONAL_CONFIG_GUIDE.md](docs/PERSONAL_CONFIG_GUIDE.md) for details.

## Testing Automated Job Discovery

The background worker can automatically discover jobs based on your resume:

**Manual test** (immediate):
```powershell
# 1. Start UI server
docker compose up ui

# 2. Upload resume via UI (http://localhost:8000) or API:
curl -X POST http://localhost:8000/api/upload/resume -F "file=@your_resume.txt"

# 3. Run test script
python test_auto_discovery.py
```

The test script will:
- Upload a sample resume
- Trigger auto-discovery manually
- Show discovered jobs with scores ≥ 60

**Automatic mode** (background worker):
```powershell
# Start worker (runs discovery every 6 hours)
docker compose up worker

# Check status via API
curl http://localhost:8000/api/auto-discover/status

# Trigger immediately (don't wait 6 hours)
curl -X POST http://localhost:8000/api/auto-discover/trigger
```

**Environment variables**:
```env
AUTO_DISCOVERY_INTERVAL_HOURS=6  # How often to search
LINK_DISCOVERY_INTERVAL_MINUTES=60
CLEANUP_INTERVAL_HOURS=24
```

## License

MIT
