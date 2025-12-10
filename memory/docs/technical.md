# Technical Documentation

## Technology Stack

### Core Platform
- **Language**: Python 3.12.10
- **Framework**: FastAPI 0.115.5
- **ASGI Server**: Uvicorn 0.32.1
- **Async Runtime**: asyncio (native)

### Web Technologies
- **Frontend**: HTML, JavaScript, Chart.js 4.4.1
- **Styling**: Custom CSS
- **HTTP Client**: httpx 0.28.0
- **Template Engine**: Jinja2 (via FastAPI)

### AI/ML Stack
- **Google Gemini**: google-generativeai 0.8.3
- **Local LLM**: Ollama (optional, via CLI)
- **GitHub Copilot**: Via VS Code extension
- **MCP Protocol**: Model Context Protocol integrations

### Data & Storage
- **Format**: JSON (file-based)
- **Configuration**: TOML (pyproject.toml)
- **File Handling**: Python pathlib, aiofiles

### Testing & Quality
- **Test Framework**: pytest 8.3.4
- **Parallel Testing**: pytest-xdist
- **Async Testing**: pytest-asyncio 0.24.0
- **Coverage**: pytest-cov
- **Linting**: flake8, black, isort
- **Type Checking**: mypy (optional)

### Containerization
- **Platform**: Docker 24.0+
- **Orchestration**: Docker Compose v2
- **Base Images**: python:3.12-slim
- **Networking**: Docker bridge network

### Development Tools
- **Package Manager**: pip
- **Build System**: setuptools
- **Virtual Environments**: venv / conda
- **Version Control**: Git + GitHub
- **CI/CD**: GitHub Actions

## Development Environment Setup

### Prerequisites
```bash
# Required
- Python 3.12.10
- Docker Desktop 24.0+
- Git

# Optional
- NVIDIA GPU (for local LLM)
- CUDA Toolkit 12.0+ (for GPU acceleration)
- Conda (alternative to venv)
```

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/vcabo/job-lead-finder.git
cd job-lead-finder
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -e ".[dev,test,web]"
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with API keys
```

5. **Build Containers**
```bash
docker compose build
docker compose up -d
```

## Project Structure

```
job-lead-finder/
├── src/
│   └── app/                    # Main application code
│       ├── main.py             # FastAPI entry point
│       ├── ui_server.py        # Web UI server
│       ├── worker.py           # Background worker
│       ├── background_scheduler.py
│       ├── job_tracker.py      # Job tracking logic
│       ├── gemini_provider.py  # AI provider
│       ├── ollama_provider.py
│       ├── mcp_providers.py
│       ├── ai_monitor_ui.py    # Resource monitor
│       ├── discovery/          # Auto-discovery
│       │   ├── base_provider.py
│       │   └── company_discovery.py
│       ├── providers/          # Job search providers
│       └── templates/          # HTML templates
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
│   ├── autonomous_task_executor.py
│   └── init_memory_bank.py
├── tools/                      # External tools
│   ├── llm_api.py
│   ├── web_scraper.py
│   └── screenshot_utils.py
├── memory/                     # Memory Bank
│   ├── docs/                   # Documentation
│   │   ├── architecture.md
│   │   ├── technical.md
│   │   └── product_requirement_docs.md
│   └── tasks/                  # Task tracking
│       ├── tasks_plan.md
│       └── active_context.md
├── data/                       # Application data
│   ├── leads.json
│   └── config.json
├── uploads/                    # File uploads
├── logs/                       # Application logs
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml              # Project metadata
└── pytest.ini                  # Test configuration
```

## Configuration Management

### Environment Variables (.env)
```bash
# AI Providers
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here

# Optional
JSEARCH_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
```

### Application Config (config.json)
```json
{
  "ai_provider": "gemini",
  "fallback_provider": "ollama",
  "discovery": {
    "enabled": true,
    "max_concurrent": 3
  },
  "blocked_entities": [],
  "system_instructions": "..."
}
```

## Code Style & Standards

### Python Style
- **Formatter**: black (line length 88)
- **Import Sorting**: isort
- **Linting**: flake8
- **Docstrings**: Google style

### Naming Conventions
- **Classes**: PascalCase (e.g., `JobTracker`)
- **Functions**: snake_case (e.g., `find_companies`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)
- **Private**: _leading_underscore (e.g., `_internal_method`)

### Async Patterns
```python
# Prefer async/await for I/O operations
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3)
)
```

## Testing Strategy

### Test Organization
```
tests/
├── test_job_finder.py          # Unit tests
├── test_gemini_provider.py     # Provider tests
├── test_ui_server.py           # API tests
└── test_discovery/             # Discovery tests
    ├── test_base_provider.py
    └── test_company_discovery.py
```

### Running Tests
```bash
# All tests
pytest

# Parallel execution
pytest -n auto

# With coverage
pytest --cov=src/app --cov-report=html

# Specific test
pytest tests/test_job_finder.py -v
```

### Test Markers
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_api_key
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev,test]"
      - run: pytest -n auto -m ""
```

## Performance Considerations

### AI Provider Selection
1. **Gemini**: Fast, free tier (20 req/day) - Use for documentation
2. **Copilot**: Premium, 1500 req/month - Use for critical tasks
3. **Ollama**: Unlimited, slower - Use for privacy-sensitive operations

### Resource Limits
- **Container Memory**: 512MB default, 1GB for worker
- **AI Monitor Polling**: Every 30 seconds
- **Worker Concurrency**: 3 parallel tasks

### Optimization Tips
- Cache AI responses when possible
- Use async I/O for external API calls
- Batch operations when feasible
- Monitor quota usage via AI Resource Monitor

## Debugging

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Container Logs
```bash
# View logs
docker compose logs -f ai-monitor
docker compose logs -f worker

# Debug container
docker compose exec app bash
```

### Common Issues
1. **Import errors**: Check virtual environment activation
2. **API errors**: Verify .env file and API keys
3. **Container errors**: Check `docker compose logs`
4. **Port conflicts**: Ensure 8000, 9000, 3000, 3001 are available

---
*Last Updated: 2025-01-08*
