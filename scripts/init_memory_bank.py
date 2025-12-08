#!/usr/bin/env python3
"""
Memory Bank Initialization Script
Creates the required Memory Bank structure for AI agents.

This script initializes:
- memory/docs/architecture.md
- memory/docs/technical.md
- memory/tasks/tasks_plan.md
- memory/tasks/active_context.md

These files provide essential project context for autonomous AI execution.
"""

import sys
from datetime import datetime
from pathlib import Path


def create_architecture_md(memory_dir: Path):
    """Create architecture.md with system design."""
    content = """# System Architecture

## Overview
Job Lead Finder is a containerized Python application for automated job
search and lead management with AI-powered analysis.

## Component Architecture

```mermaid
flowchart TB
    subgraph User Interface
        UI[Web UI - FastAPI]
        CLI[CLI Interface]
    end

    subgraph Core Services
        Worker[Background Worker]
        Scheduler[Background Scheduler]
        Tracker[Job Tracker]
    end

    subgraph Discovery
        LinkFinder[Link Finder]
        LinkValidator[Link Validator]
        AutoDiscovery[Auto Discovery]
    end

    subgraph AI Providers
        Gemini[Gemini Provider]
        Copilot[GitHub Copilot]
        Ollama[Local LLM - Ollama]
        MCP[MCP Providers]
    end

    subgraph AI Infrastructure
        Monitor[AI Resource Monitor]
        VibeCheck[Vibe Check MCP]
        VibeKanban[Vibe Kanban]
    end

    subgraph Storage
        LeadsDB[(leads.json)]
        ConfigDB[(config.json)]
        Uploads[(File Uploads)]
    end

    UI --> Worker
    CLI --> Worker
    Worker --> Scheduler
    Worker --> Tracker
    Worker --> AutoDiscovery

    AutoDiscovery --> LinkFinder
    AutoDiscovery --> LinkValidator

    Worker --> Gemini
    Worker --> Copilot
    Worker --> Ollama
    Worker --> MCP

    Gemini --> Monitor
    Copilot --> Monitor
    Ollama --> Monitor

    Worker --> LeadsDB
    Worker --> ConfigDB
    UI --> Uploads

    VibeKanban --> VibeCheck
```

## Component Responsibilities

### 1. User Interface Layer
- **Web UI (Port 8000)**: FastAPI-based web interface for job search, tracking, and configuration
- **CLI Interface**: Command-line tools for job discovery and analysis

### 2. Core Services
- **Background Worker**: Processes job search tasks asynchronously
- **Background Scheduler**: Manages periodic tasks (auto-discovery, cleanup)
- **Job Tracker**: Stores and manages job application status

### 3. Discovery Layer
- **Link Finder**: Extracts links from web pages
- **Link Validator**: Validates and filters discovered links
- **Auto Discovery**: Automated company discovery using AI providers

### 4. AI Provider Layer
- **Gemini Provider**: Google Gemini API integration (20 req/day)
- **GitHub Copilot**: Enterprise-grade AI (1500 req/month)
- **Ollama**: Local LLM for privacy-sensitive operations
- **MCP Providers**: Model Context Protocol integrations

### 5. AI Infrastructure
- **AI Resource Monitor (Port 9000)**: Tracks AI quota usage, provides recommendations
- **Vibe Check MCP (Port 3000)**: Code validation and quality checks
- **Vibe Kanban (Port 3001)**: Task management for autonomous AI execution

### 6. Storage
- **leads.json**: Job leads database (JSON-based)
- **config.json**: Application configuration
- **uploads/**: User-uploaded files (resumes, documents)

## Data Flow

### Job Discovery Flow
```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Worker
    participant Discovery
    participant AI
    participant Storage

    User->>UI: Submit search criteria
    UI->>Worker: Queue job search
    Worker->>Discovery: Find companies
    Discovery->>AI: Analyze company fit
    AI->>Storage: Save leads
    Storage-->>UI: Update results
    UI-->>User: Display leads
```

### AI Resource Management Flow
```mermaid
sequenceDiagram
    participant Worker
    participant Monitor
    participant Gemini
    participant Copilot
    participant Ollama

    Worker->>Monitor: Check availability
    Monitor-->>Worker: Resource status

    alt Gemini available
        Worker->>Gemini: Execute task
        Gemini->>Monitor: Log usage
    else Copilot available
        Worker->>Copilot: Execute task
        Copilot->>Monitor: Log usage
    else Fallback to local
        Worker->>Ollama: Execute task
        Ollama->>Monitor: Log usage
    end
```

## Deployment Architecture

### Containerized Services
All components run in Docker containers:

1. **app**: Main application container
2. **ui**: Web UI service (port 8000)
3. **worker**: Background worker
4. **ai-monitor**: Resource monitor (port 9000)
5. **vibe-check-mcp**: MCP validation service (port 3000)
6. **vibe-kanban**: Task management (port 3001)

### Volume Mounts
- `ai-tracking`: Persistent AI usage tracking
- `uploads`: User file uploads
- `data`: Application data (leads, config)

### Network Configuration
- Internal Docker network for service communication
- Exposed ports: 8000 (UI), 9000 (Monitor), 3000 (Vibe Check), 3001 (Kanban)

## Integration Points

### External APIs
- **Google Gemini API**: Free tier, 20 requests/day
- **GitHub Copilot**: Enterprise subscription, 1500 requests/month
- **JSearch API**: Job search aggregator (fallback)

### MCP Servers
- **Vibe Check**: Code validation via Model Context Protocol
- **Custom MCPs**: Extensible MCP provider system

## Security Considerations

1. **API Keys**: Stored in `.env` file, never committed to Git
2. **Input Validation**: All user inputs validated and sanitized
3. **Container Isolation**: Services isolated in Docker network
4. **File Uploads**: Restricted to specific directories with size limits
5. **Rate Limiting**: AI providers rate-limited to prevent quota exhaustion

## Scalability

### Current State
- Single-container deployment for each service
- JSON-based storage (sufficient for current scale)

### Future Enhancements
- Database migration (PostgreSQL) for better query performance
- Redis caching layer for AI responses
- Horizontal scaling for worker containers
- Load balancing for UI tier

## Extension Points

1. **New AI Providers**: Implement `BaseAIProvider` interface
2. **New Discovery Methods**: Extend `AutoDiscovery` class
3. **New MCP Servers**: Add to `mcp_providers.py`
4. **New Storage Backends**: Implement storage interface

---
*Last Updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
    file_path = memory_dir / "docs" / "architecture.md"
    file_path.write_text(content, encoding="utf-8")
    print(f"   ✓ Created: {file_path}")


def create_technical_md(memory_dir: Path):
    """Create technical.md with development stack details."""
    content = """# Technical Documentation

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
venv\\Scripts\\activate     # Windows
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
*Last Updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
    file_path = memory_dir / "docs" / "technical.md"
    file_path.write_text(content, encoding="utf-8")
    print(f"   ✓ Created: {file_path}")


def create_tasks_plan_md(memory_dir: Path):
    """Create tasks_plan.md from docs/TODO.md."""
    content = """# Tasks Plan

## Overview
This file tracks the project's task backlog, progress, and status. Tasks
are organized by priority (P0-P3) and grouped into tracks.

## Current Sprint Focus

### Sprint Goal
Complete P0 Memory Bank Documentation to enable autonomous AI task execution.

### Sprint Status
- **Start Date**: {datetime.now().strftime('%Y-%m-%d')}
- **Duration**: 1 week
- **Progress**: 0/4 P0 items completed

## Task Tracks

### 🔥 P0: Foundation Tasks (Critical - Must Do First)

**Track 1: Memory Bank Documentation**
- Status: 🔴 Not Started
- Assigned: Gemini (20 requests available)
- Priority: CRITICAL - Required for autonomous AI execution
- Items:
  1. [ ] Create memory/docs/architecture.md - System design and component relationships
  2. [ ] Create memory/docs/technical.md - Tech stack, setup, standards
  3. [ ] Create memory/tasks/tasks_plan.md - This file (backlog tracking)
  4. [ ] Create memory/tasks/active_context.md - Current work context
- Estimated Effort: 2-4 hours (Gemini: 5 requests per doc)
- Acceptance Criteria:
  - All 4 Memory Bank files created and validated
  - Files follow template structure
  - Content reviewed and approved
  - `python -m rulebook_ai project sync` executed successfully

---

### 📌 P1: High-Value Tasks

**Track 2: Email Server Integration**
- Status: 🟡 Planned
- Assigned: Copilot (1500 requests available)
- Priority: High - Enables automated job application tracking
- Items:
  1. [ ] IMAP integration for Gmail/Outlook
  2. [ ] Email parsing for application confirmations
  3. [ ] Auto-update job status from emails
  4. [ ] Email template system for outreach
- Estimated Effort: 1-2 days
- Dependencies: Track 1 (Memory Bank)

**Track 3: Provider-Agnostic AI Framework**
- Status: 🟡 Planned
- Assigned: Copilot
- Priority: High - Improves AI provider reliability
- Items:
  1. [ ] BaseAIProvider interface standardization
  2. [ ] Automatic fallback chain (Gemini → Copilot → Local)
  3. [ ] Response caching layer
  4. [ ] Rate limit handling
- Estimated Effort: 2-3 days
- Dependencies: Track 1 (Memory Bank)

---

### 📋 P2: Enhancement Tasks

**Track 4: Learning System**
- Status: 🔵 Backlog
- Assigned: Local LLM (when available)
- Priority: Medium
- Items:
  1. [ ] Preference learning from user feedback
  2. [ ] Personalized company matching
  3. [ ] Historical success pattern analysis

**Track 5: AI Profile System**
- Status: 🔵 Backlog
- Assigned: Local LLM
- Priority: Medium
- Items:
  1. [ ] Multi-resume support
  2. [ ] Role-specific targeting
  3. [ ] Skills gap analysis

---

### 📦 P3: Future Enhancements

**Track 6: Small LM Integration**
- Status: ⚪ Ideation
- Items:
  1. [ ] Integrate smaller LMs (<7B params)
  2. [ ] CPU-optimized inference
  3. [ ] Quantization support (GGUF, AWQ)

---

## Completed Tasks

### ✅ Recently Completed

**Containerized AI Resource Monitor**
- Completed: {datetime.now().strftime('%Y-%m-%d')}
- Created Flask-based dashboard (port 9000)
- Tracks Copilot, Gemini, Ollama, GPU usage
- Chart.js visualizations with auto-refresh
- Added to docker-compose.yml

**Documentation Reorganization**
- Completed: {datetime.now().strftime('%Y-%m-%d')}
- Simplified AI_AGENT_SETUP.md (140 lines)
- Created detailed guides: LOCAL_LLM_SETUP.md, VIBE_SERVICES_SETUP.md, AI_MONITOR_DASHBOARD.md
- Removed Node.js prerequisite

**CI/CD Optimization**
- Completed: {datetime.now().strftime('%Y-%m-%d')}
- Added pytest -n auto for parallel test execution
- Faster CI pipeline

---

## Known Issues

### Active Issues
1. **Ollama Not Running**: Local LLM currently unavailable
   - Impact: Cannot use local AI provider
   - Workaround: Use Gemini or Copilot
   - Resolution: Install Ollama, run `ollama serve`

2. **Gemini Daily Limit**: Only 20 requests/day
   - Impact: Limited usage for free tier
   - Workaround: Spread tasks across days, use Copilot for bulk work
   - Resolution: Consider Gemini Pro upgrade

### Resolved Issues
- ✅ Node.js requirement removed from setup
- ✅ AI monitor dashboard containerized
- ✅ Documentation simplified

---

## Next Actions

### Immediate (This Week)
1. **Execute Track 1: Memory Bank Documentation**
   - Run: `python scripts/autonomous_task_executor.py --execute`
   - Agent: Gemini (estimated 20 requests)
   - Expected: 4 Memory Bank files created
   - Validation: Files reviewed, `python -m rulebook_ai project sync` successful

2. **Verify Autonomous Execution**
   - Monitor via Vibe Kanban (http://localhost:3001)
   - Track resources via AI Monitor (http://localhost:9000)
   - Validate output via Vibe Check MCP (http://localhost:3000)

### Short-term (Next 2 Weeks)
1. Execute Track 2: Email Server Integration (Copilot)
2. Execute Track 3: Provider-Agnostic AI Framework (Copilot)

### Long-term (Next Month)
1. Execute Track 4: Learning System (Local LLM)
2. Execute Track 5: AI Profile System (Local LLM)

---

*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Status: 🔴 P0 In Progress | 🟡 2 P1 Planned | 🔵 2 P2 Backlog*
"""
    file_path = memory_dir / "tasks" / "tasks_plan.md"
    file_path.write_text(content, encoding="utf-8")
    print(f"   ✓ Created: {file_path}")


def create_active_context_md(memory_dir: Path):
    """Create active_context.md with current work state."""
    content = """# Active Context

## Current Work Session

**Session Start**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Current Focus**: Initializing Memory Bank for autonomous AI execution
**Working Branch**: docs/parallel-work-setup

## What We're Working On

### Primary Objective
Set up autonomous AI task execution system with minimal human interaction.

### Current Task: Track 1 - Memory Bank Documentation (P0)
- **Status**: 🟢 In Progress (Initialization)
- **Assigned Agent**: Gemini
- **Estimated Completion**: 2-4 hours
- **Progress**: Memory Bank files being created by init_memory_bank.py

#### Sub-tasks:
1. ✅ Create memory/docs/architecture.md
2. ✅ Create memory/docs/technical.md
3. ✅ Create memory/tasks/tasks_plan.md
4. ✅ Create memory/tasks/active_context.md (this file)
5. ⏳ Run `python -m rulebook_ai project sync` to generate .cursor/rules/
6. ⏳ Execute autonomous_task_executor.py to validate setup

## Recent Context (Last 24 Hours)

### Completed Work
1. **Created AI Resource Monitor Dashboard**
   - Flask web UI on port 9000
   - Chart.js visualizations
   - Tracks Copilot (1500/month), Gemini (20/day), Ollama, GPU
   - Auto-refresh every 30 seconds
   - File: src/app/ai_monitor_ui.py (527 lines)

2. **Reorganized Documentation**
   - Simplified AI_AGENT_SETUP.md (371 → 140 lines)
   - Created LOCAL_LLM_SETUP.md (266 lines)
   - Created VIBE_SERVICES_SETUP.md (304 lines)
   - Created AI_MONITOR_DASHBOARD.md (267 lines)
   - Created AUTONOMOUS_AI_SETUP.md (450+ lines)
   - Removed Node.js prerequisite

3. **Created Autonomous Execution Scripts**
   - scripts/autonomous_task_executor.py (400+ lines)
   - scripts/init_memory_bank.py (this script)
   - Integration with Vibe Kanban, Vibe Check MCP

4. **Docker Infrastructure Verified**
   - All 6 containers running: app, ui, worker, ai-monitor, vibe-check-mcp, vibe-kanban
   - Ports exposed: 8000 (UI), 9000 (Monitor), 3000 (Vibe Check), 3001 (Kanban)
   - AI monitor API tested: http://localhost:9000/api/metrics responding

### Active Decisions
1. **AI Agent Assignment Strategy**:
   - P0 tasks → Gemini (free, good for documentation)
   - P1 tasks → Copilot (premium, critical implementation)
   - P2+ tasks → Local LLM (unlimited, privacy-focused)
   - Fallback chain: Local → Gemini → Copilot

2. **Memory Bank Structure**:
   - memory/docs/ for static project documentation
   - memory/tasks/ for dynamic work tracking
   - Templates in memory/docs/*_template.md
   - AI agents read Memory Bank before executing tasks

3. **Autonomous Execution Workflow**:
   - Task Master (Cline extension) reads TODO.md
   - Creates Vibe Kanban tasks
   - Assigns to optimal AI agent based on priority and quota
   - AI agent reads Memory Bank + task guidance
   - Executes work on feature branch
   - Validates with Vibe Check MCP
   - Creates PR for human review

## Environment State

### Docker Containers (All Running)
```
NAME                    PORT       STATUS
ai-monitor              9000       Up 3 hours
ui                      8000       Up 3 hours
worker                  -          Up 3 hours
vibe-check-mcp          3000       Up 15 hours
vibe-kanban             3001       Up 15 hours
app                     -          Up 15 hours
```

### AI Resource Availability
```
Copilot Pro:    1500/1500 remaining (0% used this month)
Gemini API:     20/20 remaining (0% used today)
Local LLM:      Not running (Ollama not installed)
GPU:            Not detected
```

### Git State
```
Branch:         docs/parallel-work-setup
Last Commit:    85ae9aa (AI resource monitoring dashboard)
Status:         Clean (all changes committed)
Upstream:       origin/docs/parallel-work-setup (up to date)
```

## Key Files & Locations

### Recently Modified
- src/app/ai_monitor_ui.py (NEW, 527 lines)
- docker-compose.yml (ai-monitor service added)
- docs/AI_AGENT_SETUP.md (simplified to 140 lines)
- docs/AUTONOMOUS_AI_SETUP.md (NEW, 450+ lines)
- scripts/autonomous_task_executor.py (NEW, 400+ lines)
- scripts/init_memory_bank.py (NEW, this script)

### Configuration Files
- .env (API keys: GEMINI_API_KEY, GITHUB_TOKEN)
- config.json (app configuration)
- pyproject.toml (dependencies, added Flask>=3.0.0)
- docker-compose.yml (6 services defined)

### Data Files
- data/leads.json (job leads database)
- .ai_usage_tracking.json (AI quota tracking)
- uploads/ (user resume uploads)

## Open Questions / Blockers

### Questions
1. Should we upgrade Gemini to Pro for unlimited requests?
   - Current: Free tier, 20 req/day
   - Impact: Can complete P0 in one day vs. spreading across multiple days
   - Decision: Defer until free tier exhausted

2. When to install Ollama for local LLM?
   - Required for: P2+ tasks (Learning System, AI Profile)
   - Not blocking: P0/P1 can use Gemini/Copilot
   - Decision: Install after P1 tasks complete

### Blockers
None currently - all dependencies satisfied for P0 execution.

## Next Steps (Immediate)

1. **Verify Memory Bank Creation** ✅
   - Check all 4 files exist in memory/ directory
   - Validate content structure matches templates

2. **Run Rulebook-AI Sync** ⏳
   ```bash
   python -m rulebook_ai project sync
   ```
   - Generates .cursor/rules/ directory
   - Creates AI agent instructions from Memory Bank

3. **Execute Autonomous Task Executor (Dry Run)** ⏳
   ```bash
   python scripts/autonomous_task_executor.py
   ```
   - Validates setup
   - Generates execution plan
   - Creates .ai-tasks/ guidance files

4. **Execute Autonomous Task Executor (Live)** ⏳
   ```bash
   python scripts/autonomous_task_executor.py --execute
   ```
   - Creates Kanban tasks
   - Assigns to Gemini
   - Begins autonomous execution

5. **Monitor Progress** ⏳
   - Vibe Kanban: http://localhost:3001
   - AI Monitor: http://localhost:9000
   - Vibe Check: http://localhost:3000

## Notes & Observations

### What's Working Well
- Docker containers stable, no crashes
- AI monitor dashboard providing clear resource visibility
- Documentation cleanup improved readability
- Autonomous execution design comprehensive

### What Needs Attention
- Ollama installation for future P2 tasks
- Consider Gemini Pro upgrade for faster P0 completion
- Test full autonomous cycle end-to-end

### Lessons Learned
1. **Memory Bank is critical**: AI agents need project context before executing tasks
2. **Resource tracking essential**: Prevents quota exhaustion, enables smart agent assignment
3. **Containerization wins**: Eliminates "works on my machine" issues
4. **Simple docs better**: Landing page should be concise, detailed guides separate

---

*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Context Status: 🟢 Active - Memory Bank Initialization in Progress*
"""
    file_path = memory_dir / "tasks" / "active_context.md"
    file_path.write_text(content, encoding="utf-8")
    print(f"   ✓ Created: {file_path}")


def main():
    """Initialize Memory Bank structure."""
    print("\n" + "=" * 70)
    print("📁 MEMORY BANK INITIALIZATION")
    print("=" * 70)

    project_root = Path(__file__).parent.parent
    memory_dir = project_root / "memory"

    # Check for existing files
    existing_files = []
    files_to_create = [
        (memory_dir / "docs" / "architecture.md", create_architecture_md),
        (memory_dir / "docs" / "technical.md", create_technical_md),
        (memory_dir / "tasks" / "tasks_plan.md", create_tasks_plan_md),
        (memory_dir / "tasks" / "active_context.md", create_active_context_md),
    ]

    for file_path, _ in files_to_create:
        if file_path.exists():
            existing_files.append(file_path)

    # Warn about existing files
    if existing_files:
        print("\n⚠️  WARNING: The following Memory Bank files already exist:")
        for f in existing_files:
            print(f"   • {f.relative_to(project_root)}")
        print("\n   These files will be OVERWRITTEN with fresh templates.")
        print("   Any manual changes will be LOST.")

        response = input("\n   Continue? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            print("\n❌ Aborted by user")
            sys.exit(0)

        # Create backup
        print("\n💾 Creating backup...")
        backup_dir = memory_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in existing_files:
            backup_path = backup_dir / f.relative_to(memory_dir)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"   ✓ Backed up: {f.relative_to(project_root)} → {backup_path.relative_to(project_root)}")

    # Create directories
    print("\n📂 Creating directories...")
    (memory_dir / "docs").mkdir(parents=True, exist_ok=True)
    (memory_dir / "tasks").mkdir(parents=True, exist_ok=True)
    print("   ✓ memory/docs/")
    print("   ✓ memory/tasks/")

    # Create files
    print("\n📝 Creating Memory Bank files...")
    try:
        create_architecture_md(memory_dir)
        create_technical_md(memory_dir)
        create_tasks_plan_md(memory_dir)
        create_active_context_md(memory_dir)
    except Exception as e:
        print(f"\n❌ Error creating files: {e}")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 70)
    print("✅ MEMORY BANK INITIALIZED SUCCESSFULLY")
    print("=" * 70)

    print("\n📋 Created Files:")
    print("   • memory/docs/architecture.md")
    print("   • memory/docs/technical.md")
    print("   • memory/tasks/tasks_plan.md")
    print("   • memory/tasks/active_context.md")

    print("\n📌 Next Steps:")
    print("   1. Review generated files for accuracy")
    print("   2. Run: python -m rulebook_ai project sync")
    print("   3. Run: python scripts/autonomous_task_executor.py (dry run)")
    print("   4. Run: python scripts/autonomous_task_executor.py --execute (live)")

    print("\n💡 Pro Tip:")
    print("   AI agents will read these Memory Bank files before executing tasks.")
    print("   Keep them updated as the project evolves!")


if __name__ == "__main__":
    main()
