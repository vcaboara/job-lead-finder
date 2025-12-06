# Job Lead Finder

AI-powered job search tool aggregating jobs from multiple providers including WeWorkRemotely, RemoteOK, Remotive, and direct company career pages.

## Features

- **Job Aggregation**: WeWorkRemotely + RemoteOK + Remotive + CompanyJobs (Gemini-powered company career page search)
  - Round-robin distribution ensures diversity across all providers
- **Company Discovery**: Passive job discovery via JSearch API (RapidAPI)
  - Real-time job aggregation from Indeed, LinkedIn, Glassdoor, etc.
  - Automated company extraction and tech stack detection
  - SQLite database for discovered companies
- **Job Tracking**: Track application status (new, applied, interviewing, rejected, offer, hidden)
- **Web UI**: FastAPI dashboard at http://localhost:8000 with search, upload, configuration
- **Enhanced Resume Upload**: Upload resumes in multiple formats (.txt, .md, .pdf, .docx)
  - 5MB file size limit with clear error messages
  - Comprehensive security scanning (script detection, macro detection, malicious content filtering)
  - PDF text extraction with pypdf
  - DOCX text extraction with python-docx (includes table content)
- **AI Features**: Job evaluation, custom cover letter generation
- **Link Discovery**: Find direct company career pages from aggregator listings
- **Industry Profiles**: Tech, Finance, Healthcare, Gaming, Ecommerce, Automotive, Aerospace, ESG
- **Link Validation**: Detect 404s, soft-404s, and invalid URLs
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

See [PERSONAL_CONFIG_GUIDE.md](PERSONAL_CONFIG_GUIDE.md) for details.

## License

MIT
