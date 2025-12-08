# AI Agent Parallel Work Setup Guide

## Overview

This guide shows how to leverage multiple AI resources simultaneously for parallel development:
- **GitHub Copilot Pro** (1.5k requests/month)
- **Gemini API** (20 requests/day free tier)
- **Local LLM** (Ollama/LM Studio on GPU)
- **Vibe Check MCP** (AI code oversight)
- **Vibe Kanban** (Multi-agent orchestration)

## Prerequisites

### Required
- Docker Desktop installed and running
- Git installed
- Node.js 18+ (for Vibe services)
- Python 3.12+

### Optional (for Local LLM)
- NVIDIA GPU with 8GB+ VRAM
- Ollama OR LM Studio installed

## Quick Start

### 1. Clone and Setup Repository

```bash
git clone https://github.com/vcaboara/job-lead-finder.git
cd job-lead-finder

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# GEMINI_API_KEY=your_key_here
# GITHUB_TOKEN=your_github_token (for Copilot)
```

### 2. Start Core Services (Docker)

```bash
# Start all services including vibe-check-mcp and vibe-kanban
docker compose up -d

# Verify services are running
docker compose ps
```

Expected services:
- `job-lead-finder-ui-1` - Port 8000 (Web UI)
- `job-lead-finder-worker-1` - Background worker
- `job-lead-finder-vibe-check-mcp-1` - Port 3000 (AI oversight)
- `job-lead-finder-vibe-kanban-1` - Port 3001 (Orchestration)

### 3. Access AI Services

**Vibe Check MCP** (Code Review & Oversight)
- URL: http://localhost:3000
- Purpose: AI-powered code review, architectural validation
- Usage: Point your IDE or tools to this MCP server

**Vibe Kanban** (Multi-Agent Orchestration)
- URL: http://localhost:3001
- Purpose: Coordinate multiple AI agents on parallel tasks
- Usage: Web interface for task assignment and progress tracking

## Local LLM Setup (Optional but Recommended)

### Option A: Ollama (Recommended - Easier)

```bash
# Install Ollama
# Windows: Download from https://ollama.ai/download
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# Mac: brew install ollama

# Pull a model (choose based on your GPU)
ollama pull qwen2.5:32b-instruct-q4_K_M  # ~20GB, needs 16GB+ VRAM
ollama pull qwen2.5:14b-instruct-q4_K_M  # ~9GB, needs 8GB+ VRAM
ollama pull llama3.2:3b                  # ~2GB, works on 4GB VRAM

# Verify it's running
ollama list
curl http://localhost:11434/api/tags
```

**No NVIDIA Docker needed** - Ollama handles GPU access natively on the host.

### Option B: LM Studio (GUI Alternative)

1. Download from https://lmstudio.ai/
2. Install and launch
3. Download a model from the UI (e.g., Qwen2.5, Llama 3.2)
4. Start the local server (default port 1234)
5. Configure job-lead-finder to use `http://localhost:1234`

**No Docker needed** - LM Studio runs as a native app with GPU access.

### GPU Requirements

| GPU VRAM | Recommended Model | Performance |
|----------|-------------------|-------------|
| 4-6 GB   | llama3.2:3b or qwen2.5:7b-q4 | Basic tasks |
| 8-12 GB  | qwen2.5:14b-q4 or llama3.1:8b | Good for most tasks |
| 16-24 GB | qwen2.5:32b-q4 or llama3.1:70b-q4 | Best quality |

**Note:** Your laptop's 4070 (8GB) is perfect for qwen2.5:14b-q4 or llama3.2:3b.

## Configuration for Local LLM

### Update `.env` file

```bash
# For Ollama (default port 11434)
OLLAMA_BASE_URL=http://localhost:11434

# For LM Studio (default port 1234)
# OLLAMA_BASE_URL=http://localhost:1234
```

### Test Local LLM

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\Activate.ps1  # Windows

# Test with the tools/llm_api.py
python tools/llm_api.py --prompt "What is the capital of France?" --provider local
```

## Parallel Work Execution

### Daily Workflow

See `PARALLEL_WORK_STRATEGY.md` for the complete execution plan.

**Morning (9 AM - 12 PM):**
```bash
# 1. Check Vibe Kanban dashboard
open http://localhost:3001

# 2. Use Gemini for documentation (10/20 requests)
python tools/llm_api.py --prompt "Document the architecture..." --provider gemini

# 3. Start local LLM background tasks
python tools/llm_api.py --prompt "Analyze codebase for TODOs..." --provider local
```

**Afternoon (1 PM - 5 PM):**
```bash
# 4. Use Copilot Pro for heavy implementation (25 requests)
# Work directly in VS Code with GitHub Copilot

# 5. Use Gemini for code review (10/20 requests)
python tools/llm_api.py --prompt "Review this code..." --provider gemini

# 6. Vibe Check MCP validates work
# Automatically checks code against architectural standards
```

### Resource Allocation

| AI Resource | Daily Budget | Best For |
|-------------|--------------|----------|
| GitHub Copilot Pro | ~50 requests | Complex implementation, refactoring |
| Gemini API | 20 requests | Documentation, simple code gen, testing |
| Local LLM (Ollama) | Unlimited | Code analysis, pattern detection, repetitive tasks |
| Vibe Check MCP | Unlimited | Code review, architectural validation |
| Vibe Kanban | Unlimited | Task coordination, progress tracking |

## Vibe Services Configuration

### Vibe Check MCP (Port 3000)

**Purpose:** AI-powered code oversight and review

**Configuration:** `vibe-check-mcp/.env`
```bash
# Uses your Gemini or OpenAI key for AI analysis
GEMINI_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here
```

**Usage:**
- Point your IDE's MCP client to `http://localhost:3000`
- Automatically validates code against project standards
- Provides real-time feedback on architectural decisions

### Vibe Kanban (Port 3001)

**Purpose:** Multi-agent task orchestration

**Features:**
- Visual kanban board for 9 parallel work tracks
- Agent assignment and coordination
- Progress tracking across all AI resources
- Dependency management between tasks

**Access:** Open http://localhost:3001 in your browser

## Troubleshooting

### Vibe Services Won't Start

```bash
# Check if ports are already in use
netstat -an | grep 3000
netstat -an | grep 3001

# Restart Docker services
docker compose down
docker compose up -d
```

### Local LLM Not Responding

```bash
# For Ollama
ollama ps  # Check running models
ollama serve  # Restart Ollama service

# For LM Studio
# Restart the app and ensure "Start Server" is enabled
```

### GPU Not Detected

```bash
# Check NVIDIA GPU
nvidia-smi

# For Ollama - it auto-detects GPU, no Docker needed
# For LM Studio - check GPU settings in preferences
```

### Gemini API Rate Limited

```bash
# Check quota usage (20 requests/day on free tier)
# Wait for quota reset (24 hours)
# Or upgrade to paid tier for more requests

# Fall back to local LLM temporarily
python tools/llm_api.py --prompt "Your task..." --provider local
```

## Architecture: Why No NVIDIA Docker?

**Ollama/LM Studio runs natively on the host**, not in Docker:
- ✅ Direct GPU access (faster, simpler)
- ✅ No NVIDIA Container Toolkit needed
- ✅ Works on Windows, Linux, Mac
- ✅ Easier to manage and update models

**Job-lead-finder services** run in Docker:
- ✅ Consistent environment
- ✅ Easy deployment
- ✅ Access local LLM via network (`host.docker.internal:11434`)

This hybrid approach gives you:
- **Simplicity**: No complex GPU passthrough setup
- **Performance**: Native GPU access for LLM
- **Portability**: Docker for application services

## Next Steps

1. **Verify Setup**
   ```bash
   # All services running?
   docker compose ps

   # Local LLM working?
   curl http://localhost:11434/api/tags

   # Vibe services accessible?
   curl http://localhost:3000/health
   curl http://localhost:3001/health
   ```

2. **Start First Task**
   - Open `PARALLEL_WORK_STRATEGY.md`
   - Follow P0 Track 1: Memory Bank Documentation
   - Use Gemini API for initial documentation

3. **Monitor Resources**
   - Track Copilot usage (manual spreadsheet)
   - Check Gemini quota daily
   - Monitor GPU usage with `nvidia-smi` or Task Manager

## Reference Documents

- `PARALLEL_WORK_STRATEGY.md` - Complete 4-week execution plan
- `docs/TODO.md` - All planned enhancements
- `memory/docs/` - Project documentation (to be completed in P0)

## Quick Command Reference

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f vibe-check-mcp
docker compose logs -f vibe-kanban

# Restart a service
docker compose restart vibe-check-mcp

# Check local LLM
ollama list
ollama ps

# Test LLM API
python tools/llm_api.py --prompt "Hello" --provider local
python tools/llm_api.py --prompt "Hello" --provider gemini
```

---

**Last Updated:** 2025-12-08
**Status:** Production Ready
