# Job Lead Finder

AI-powered job search tool aggregating jobs from multiple providers including WeWorkRemotely, RemoteOK, Remotive, and direct company career pages.

## Features

- **Job Aggregation**: WeWorkRemotely + RemoteOK + Remotive + CompanyJobs (Gemini-powered company career page search)
  - Round-robin distribution ensures diversity across all providers
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

### CLI Usage

```powershell
# With uv (recommended - faster, better dependency management)
uv run python -m app.main find -q "remote python developer" --resume "Your resume" -n 10
uv run python -m app.main health

# Traditional installation
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[web,gemini]
python -m app.main find -q "remote python developer" --resume "Your resume" -n 10
```

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
├── main.py              # CLI entry point
├── ui_server.py         # FastAPI REST API + web UI
├── job_finder.py        # Job search orchestration
├── job_tracker.py       # Track applications and status
├── mcp_providers.py     # WeWorkRemotely, RemoteOK, Remotive, CompanyJobs
├── gemini_provider.py   # AI provider (evaluation, cover letters)
├── link_validator.py    # URL validation
├── industry_profiles.py # 8 industry-specific company lists
├── config_manager.py    # Configuration management
└── templates/           # HTML templates

tests/                   # 164 passing tests
```

## Configuration

- **Web UI**: 5-tab config interface (Industry, Providers, Location, Search, Blocked)
- **API**: `GET /api/job-config`, `POST /api/job-config/search`
- **File**: `config.json` (auto-created, gitignored)

See [PERSONAL_CONFIG_GUIDE.md](PERSONAL_CONFIG_GUIDE.md) for details.

## License

MIT
