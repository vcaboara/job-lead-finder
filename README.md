# Job Lead Finder

AI-powered job search tool with MCP integration, Gemini fallback, link validation, and FastAPI dashboard.

## Features

- **Multiple Data Sources**: LinkedIn, Indeed, GitHub jobs via Model Context Protocol (MCP)
- **CLI**: Find and evaluate job leads from the command line
- **Web UI**: FastAPI dashboard at http://localhost:8000
- **AI Evaluation**: Gemini-powered job matching with fallback when tools unavailable
- **Link Validation**: Verify job application URLs (detect 404s, 403s, redirects)
- **Docker**: Fully containerized with compose setup
- **CI**: Automated testing with GitHub Actions

## Quick Start

### Option 1: MCP Setup (Recommended)

Use MCP servers for LinkedIn, Indeed, and GitHub job searches:

1. **Configure MCP credentials**:
   ```powershell
   Copy-Item .env.mcp.example .env.mcp
   # Edit .env.mcp with your LinkedIn/Indeed/GitHub credentials
   ```

2. **Start MCP servers**:
   ```powershell
   docker-compose -f docker-compose.mcp.yml up -d
   ```

3. **Verify MCPs are running**:
   ```powershell
   docker-compose -f docker-compose.mcp.yml ps
   curl http://localhost:3000/health  # LinkedIn
   curl http://localhost:3001/health  # Indeed
   curl http://localhost:3002/health  # GitHub
   ```

See **[MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)** for detailed instructions.

### Option 2: Gemini Fallback Setup

1. **Clone and install**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -e .[gemini]
   ```

2. **Configure API key** (create `.env` file):
   ```
   GEMINI_API_KEY=your-key-here
   GOOGLE_API_KEY=your-key-here
   ```

3. **Get your API key**: https://aistudio.google.com/app/apikey

**Note**: Gemini free tier has a 250 requests/day limit. MCP approach is more reliable for production use.

### CLI Usage

**Find jobs**:
```powershell
python -m app.main find -q "remote python developer" --resume "Senior Python dev, Django, FastAPI" -n 5
```

**With link validation and evaluation**:
```powershell
python -m app.main find -q "remote python" --resume "Your resume" -n 3 --validate-links --evaluate --verbose
```

**Health check**:
```powershell
python -m app.main health
```

### Web UI

**Start the UI**:
```powershell
docker compose up ui
```

Open http://localhost:8000 in your browser.

## Docker Usage

**CLI in Docker**:
```powershell
docker compose run --rm app python -m app.main find -q "python" --resume "Your resume" -n 3
```

**Run tests**:
```powershell
docker compose run --rm app python -m pytest -v
```

**Build and run UI**:
```powershell
docker compose up ui -d
```

## Development

**Format code**:
```powershell
python -m black src/ tests/ --line-length 120
python -m isort src/ tests/
```

**Install pre-commit hooks**:
```powershell
pre-commit install
```

**Run all tests**:
```powershell
pytest -v
```

## Project Structure

```
src/app/
├── main.py              # CLI entry point
├── job_finder.py        # Orchestration logic
├── gemini_provider.py   # AI provider with fallback
├── link_validator.py    # URL validation
└── ui_server.py         # FastAPI dashboard

tests/
├── test_job_finder.py
├── test_provider_fallback.py
└── ...
```

## Configuration

- **`.env`**: API keys (gitignored)
- **`pyproject.toml`**: Dependencies and tool config
- **`docker-compose.yml`**: Service definitions
- **`CODEOWNERS`**: Code review assignments

## License

MIT
