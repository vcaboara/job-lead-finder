# AI Agent Parallel Work Setup

Quick start guide for leveraging multiple AI resources simultaneously for parallel development.

## What You Get

- **GitHub Copilot Pro** (1.5k requests/month) - Complex implementation
- **Gemini API** (20 requests/day) - Documentation & testing
- **Local LLM** (Unlimited) - Code analysis & refactoring
- **AI Resource Monitor** (Port 9000) - Usage dashboard
- **Vibe Check MCP** (Port 3000) - Code review
- **Vibe Kanban** (Port 3001) - Task orchestration

## Prerequisites

- Docker Desktop (running)
- Git
- Python 3.12+
- *Optional:* NVIDIA GPU (8GB+ VRAM) for local LLM

## Quick Start

### 1. Automated Setup (Recommended)

```bash
git clone https://github.com/vcaboara/job-lead-finder.git
cd job-lead-finder

# Run setup script
python scripts/setup_ai_agents.py
```

**The script will:**

- Detect your GPU and recommend models
- Create `.env` from template
- Setup Ollama (if GPU available)
- Start all Docker services
- Verify complete setup

**After setup:** Edit `.env` and add your API keys:

```bash
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_github_token
```

### 2. Manual Setup

```bash
git clone https://github.com/vcaboara/job-lead-finder.git
cd job-lead-finder

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker compose up -d
```

## Access Services

Once running, access:

- **Job Lead Finder UI**: <http://localhost:8000>
- **AI Resource Monitor**: <http://localhost:9000> - Track usage quotas
- **Vibe Check MCP**: <http://localhost:3000> - Code review API
- **Vibe Kanban**: <http://localhost:3001> - Task board

## Detailed Guides

- **[Local LLM Setup](LOCAL_LLM_SETUP.md)** - Ollama/LM Studio installation
- **[Vibe Services](VIBE_SERVICES_SETUP.md)** - MCP and Kanban configuration
- **[AI Monitor Dashboard](AI_MONITOR_DASHBOARD.md)** - Usage tracking
- **[Parallel Work Strategy](../PARALLEL_WORK_STRATEGY.md)** - Execution plan
- **[Setup Scripts](../scripts/README.md)** - Automation utilities

## Quick Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Restart service
docker compose restart ai-monitor

# Check status
docker compose ps
```

## Next Steps

1. **Verify Setup**

   ```bash
   docker compose ps  # All services running?
   curl http://localhost:9000  # AI monitor accessible?
   ```

2. **Optional: Install Local LLM**
   See [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md) for Ollama/LM Studio

3. **Start Working**
   Follow [PARALLEL_WORK_STRATEGY.md](../PARALLEL_WORK_STRATEGY.md) for task execution

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker info

# Restart Docker Desktop
# Then: docker compose up -d
```

### Port Conflicts

```bash
# Find what's using port
netstat -ano | findstr :9000  # Windows
lsof -i :9000  # Linux/Mac

# Change port in docker-compose.yml
```

### Missing API Keys

```bash
# Verify .env file
cat .env | grep API_KEY

# Add missing keys
echo "GEMINI_API_KEY=your_key" >> .env

# Restart services
docker compose restart
```

For more detailed troubleshooting, see the specific service guides linked above.
