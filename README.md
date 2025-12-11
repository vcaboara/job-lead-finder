# Job Lead Finder

AI-powered job search tool aggregating jobs from multiple providers including WeWorkRemotely, RemoteOK, Remotive, and direct company career pages.

## Quick Links

📚 **Getting Started**
- [Navigation Dashboard](http://localhost:8000/nav) - Main navigation to all services (when running)
- [Personal Configuration Guide](docs/PERSONAL_CONFIG_GUIDE.md) - API keys and environment setup
- [Ollama Setup Guide](OLLAMA_SETUP.md) - Local AI setup for unlimited job evaluations and code reviews
- [Free Hosting Guide](docs/FREE_HOSTING_OPTIONS.md) - Deploy to Railway.app ($5/month)

🤖 **AI Development System**
- [AI Resource Monitor](http://localhost:9000) - Track Copilot, Gemini, Ollama, GPU usage (when running)
- [Visual Kanban](http://localhost:8000/visual-kanban) - Monitor autonomous AI task progress
- [Vibe Check MCP](http://localhost:3000) - Model Context Protocol server for AI integration

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
- [**Ollama Code Assistant**](docs/OLLAMA_CODE_ASSISTANT.md) - **NEW!** Local LLM tool for privacy-sensitive operations
- [Ollama Quick Start](docs/OLLAMA_QUICKSTART.md) - Get local AI running in 5 minutes (12GB VRAM recommended)
- [Token Optimization Guide](docs/TOKEN_OPTIMIZATION.md) - **CRITICAL!** Save 50% on Copilot quota
- [Local Coding Assistant](docs/CODING_ASSISTANT.md) - Free local code generation with Ollama
- [Ollama Tunnel Setup](docs/OLLAMA_TUNNEL_SETUP.md) - Free AI PR reviews with local models
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

### Job Search & Tracking
- **Job Aggregation**: WeWorkRemotely + RemoteOK + Remotive + CompanyJobs (Gemini-powered company career page search)
- **Company Discovery**: Passive job discovery via JSearch API (RapidAPI)
- **Job Tracking**: Track application status through the entire hiring funnel
- **Enhanced Resume Upload**: Multi-format support (.txt, .md, .pdf, .docx) with security scanning
- **AI Job Evaluation**: Score jobs against your resume with custom cover letter generation

### Autonomous AI Development System (LeadForge)
- **AI PR Reviews**: Automated code review on every pull request using Ollama (local GPU) → OpenAI fallback
- **AI Task Dispatcher**: Creates PRs from GitHub issues labeled `ai-task` with full implementation
- **Resource Monitoring**: Real-time dashboard tracking GitHub Copilot, Gemini API, Ollama, and GPU usage
- **Visual Kanban**: Monitor AI task progress (Backlog → In Progress → Review → Done)
- **Free Local AI**: Ollama integration (qwen2.5-coder:14b, deepseek-r1:14b) for unlimited AI operations
- **MCP Integration**: Vibe Check MCP server for AI context and resource management

### Infrastructure
- **Web UI**: Modern lovable.dev dark theme with navigation dashboard
- **Docker**: Fully containerized (5 services: ui, worker, ai-monitor, vibe-check-mcp, app)
- **Deployment**: Railway.app ready with railway.toml configuration

## Quick Start

### Web UI (Recommended)

1. **Start all services**:
   ```powershell
   # All services (job search + AI development system)
   docker compose up -d

   # Or individually:
   docker compose up -d ui           # Job search UI (port 8000)
   docker compose up -d worker       # Background job discovery
   docker compose up -d ai-monitor   # AI resource tracking (port 9000)
   docker compose up -d vibe-check-mcp # MCP server (port 3000)
   ```

2. **Open navigation dashboard**: http://localhost:8000/nav
   - 🔍 Job Search (main app)
   - 📊 Dashboard (service overview)
   - 🤖 AI Resource Monitor (port 9000)
   - 📋 Visual Kanban (AI tasks)
   - 🔌 Vibe Check MCP (port 3000)
   - 💚 Health Check (API endpoint)

3. **Configure** (optional but recommended):
   - `GEMINI_API_KEY` - AI job evaluation, cover letters, CompanyJobs search ([Get key](https://aistudio.google.com/app/apikey))
   - `RAPIDAPI_KEY` - Company discovery via JSearch ([Get key](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch))
   - `GITHUB_TOKEN` - GitHub API access for autonomous AI features ([Get token](https://github.com/settings/tokens))
   - `OPENAI_API_KEY` - Fallback for AI PR reviews ([Get key](https://platform.openai.com/api-keys))
   - `OLLAMA_BASE_URL` - Local Ollama server (default: http://host.docker.internal:11434)

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
# Job Search & AI Evaluation
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=${GEMINI_API_KEY}  # Alias for Gemini
RAPIDAPI_KEY=your_rapidapi_key_here

# Autonomous AI Development System
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_key_here  # Fallback for AI reviews
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Optional: OpenRouter (alternative to OpenAI)
OPENROUTER_API_KEY=your_openrouter_key_here

# Background Worker Settings
AUTO_DISCOVERY_INTERVAL_HOURS=6
LINK_DISCOVERY_INTERVAL_MINUTES=60
CLEANUP_INTERVAL_HOURS=24
```

**Get API Keys**:
- Gemini: https://aistudio.google.com/app/apikey (Free tier: 15 RPM)
- RapidAPI (JSearch): https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- GitHub Token: https://github.com/settings/tokens (Scopes: repo, workflow)
- OpenAI: https://platform.openai.com/api-keys
- Ollama: Local install - see [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

## Ollama Setup (Free Local AI)

For unlimited AI operations using your GPU:

```powershell
# 1. Install Ollama
winget install Ollama.Ollama

# 2. Pull models for code generation and review
ollama pull qwen2.5-coder:14b    # 9GB - Primary code model
ollama pull deepseek-r1:14b      # 9GB - Complex reasoning

# 3. Verify models
ollama list

# 4. Test local AI
ollama run qwen2.5-coder:14b "Write a Python function to validate email"
```

**AI Workflows** (priority order):
1. **Ollama** (local GPU) - Free, unlimited, fast
2. **Anthropic** - High quality, paid
3. **OpenAI** - Fallback, paid

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed setup and model selection.

## Deployment to Railway.app

```powershell
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and initialize
railway login
railway init

# 3. Deploy
railway up

# 4. Set environment variables in Railway dashboard
# Add: GEMINI_API_KEY, RAPIDAPI_KEY, GITHUB_TOKEN, etc.
```

**Cost**: ~$5/month on Railway's Hobby plan with persistent volumes.

See [docs/FREE_HOSTING_OPTIONS.md](docs/FREE_HOSTING_OPTIONS.md) for alternatives (Fly.io, Render.com).

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
├── ai_monitor_ui.py     # AI resource monitoring dashboard (port 9000)
├── worker.py            # Background worker (auto-discovery, link validation)
├── background_scheduler.py  # Task scheduling
├── job_finder.py        # Job search orchestration
├── job_tracker.py       # Track applications and status
├── mcp_providers.py     # WeWorkRemotely, RemoteOK, Remotive, CompanyJobs
├── gemini_provider.py   # AI provider (evaluation, cover letters)
├── gemini_cli.py        # Gemini CLI interface
├── ollama_provider.py   # Ollama local AI provider
├── link_validator.py    # URL validation
├── link_finder.py       # Find job links in aggregators
├── industry_profiles.py # 8 industry-specific company lists
├── config_manager.py    # Configuration management
├── discovery/           # Company discovery system
│   ├── base_provider.py    # Abstract provider interface
│   ├── company_store.py    # SQLite database for companies
│   ├── config.py           # Discovery configuration
│   └── providers/
│       └── jsearch_provider.py  # JSearch API integration
└── templates/           # HTML templates
    ├── nav.html         # Navigation dashboard
    ├── index.html       # Main job search UI
    ├── dashboard.html   # Service overview
    └── __init__.py

.github/workflows/       # Autonomous AI system
├── ai-pr-review.yml     # Automated PR code reviews
└── ai-task-dispatcher.yml # Auto-implement features from issues

vibe-check-mcp/         # MCP server (port 3000)
tests/                  # 259+ passing tests
data/
├── tracked_jobs.json   # Job tracking persistence
└── discovery.db        # Discovered companies database

railway.toml            # Railway.app deployment config
```

## Configuration

- **Web UI**: 5-tab config interface (Industry, Providers, Location, Search, Blocked)
- **API**: `GET /api/job-config`, `POST /api/job-config/search`
- **File**: `config.json` (auto-created, gitignored)

See [PERSONAL_CONFIG_GUIDE.md](docs/PERSONAL_CONFIG_GUIDE.md) for details.

## Using the Autonomous AI System

### AI-Powered PR Reviews

Every pull request automatically gets reviewed by AI:

1. **Ollama** (local GPU) tries first - free, unlimited
2. **OpenAI** fallback if Ollama unavailable
3. Review posted as PR comment with:
   - Code quality analysis
   - Security concerns
   - Performance suggestions
   - Best practice recommendations

### AI Task Dispatcher

Create features automatically from GitHub issues:

```bash
# 1. Create an issue with label 'ai-task'
# 2. AI dispatcher will:
#    - Analyze the request
#    - Generate implementation
#    - Create a pull request
#    - Request review
```

**Priority**: Ollama (local) → Anthropic → OpenAI

### Monitor AI Resources

Visit http://localhost:9000 to track:
- GitHub Copilot usage (monthly limit: 1500 requests)
- Gemini API usage (daily limit: 20 requests)
- Ollama status and active models
- GPU utilization and VRAM usage
- Real-time charts and recommendations

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
