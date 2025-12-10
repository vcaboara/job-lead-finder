# AI Agent Setup Scripts

Automated utilities for setting up and monitoring parallel AI development environment.

## Overview

This directory contains two complementary tools for AI development:

1. **`setup_ai_agents.py`** - One-time automated setup
2. **`monitor_ai_resources.py`** - CLI tool for tracking usage

For **graphical monitoring**, access the **AI Resource Monitor Dashboard** at <http://localhost:9000> when running `docker compose up -d ai-monitor`.

## Scripts

### 1. `setup_ai_agents.py` - Automated Setup

Automates the complete setup process for parallel AI development.

**Features:**
- ✅ Detects system (Windows/Linux/Mac) and GPU automatically
- ✅ Checks prerequisites (Docker, Git)
- ✅ Sets up `.env` file from template
- ✅ Installs and configures Ollama with GPU-optimized models
- ✅ Starts Docker services (Vibe Check MCP, Vibe Kanban)
- ✅ Verifies complete setup

**Usage:**

```bash
# Full automated setup
python scripts/setup_ai_agents.py

# Skip Docker setup (if already configured)
python scripts/setup_ai_agents.py --skip-docker

# Skip Ollama setup (if using LM Studio or cloud only)
python scripts/setup_ai_agents.py --skip-ollama

# Custom project root
python scripts/setup_ai_agents.py --project-root /path/to/project
```

**What it does:**

1. **System Detection**
   - Detects OS (Windows/Linux/Mac)
   - Detects GPU (NVIDIA) and VRAM
   - Recommends optimal Ollama models

2. **Prerequisites Check**
   - Verifies Docker installed and running
   - Verifies Git installed

3. **Environment Setup**
   - Creates `.env` from `.env.example`
   - Prompts for API key configuration

4. **Ollama Setup** (if not skipped)
   - Checks if Ollama is installed
   - Recommends models based on GPU VRAM:
     - 12GB: `qwen2.5:32b-q4` or `qwen2.5:14b-q4`
     - 8GB: `qwen2.5:14b-q4` or `llama3.2:3b`
     - <8GB: `llama3.2:3b` or `qwen2.5:7b-q4`
   - Optionally pulls recommended model

5. **Docker Services**
   - Starts `vibe-check-mcp` (port 3000)
   - Starts `vibe-kanban` (port 3001)
   - Starts application services

6. **Verification**
   - Confirms all services running
   - Provides next steps

### 2. `monitor_ai_resources.py` - Resource Monitor

Tracks usage of AI resources and provides optimization recommendations.

**Features:**
- 📊 Tracks Copilot Pro usage (daily/monthly limits)
- 📊 Tracks Gemini API usage (daily limits)
- 🔍 Monitors Ollama status and running models
- 🖥️ Monitors GPU utilization and VRAM usage
- 💡 Provides smart recommendations for resource optimization

**Usage:**

```bash
# Show current status (default)
python scripts/monitor_ai_resources.py
python scripts/monitor_ai_resources.py --status

# Record Copilot usage
python scripts/monitor_ai_resources.py --record-copilot 5

# Record Gemini usage
python scripts/monitor_ai_resources.py --record-gemini 3

# Reset tracking data
python scripts/monitor_ai_resources.py --reset
```

**Output Example:**

```
============================================================
AI Resource Usage Monitor
============================================================

GitHub Copilot Pro:
  Today: 12 requests
  This Month: 247/1500 requests
  Remaining: 1253 (83.5%)
  [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 16.5%

Gemini API:
  Today: 8/20 requests
  Remaining: 12 (60.0%)
  [████████████████░░░░░░░░░░░░░░░░░░░░░░░░] 40.0%

Local LLM (Ollama):
  Status: running
  Active Models:
    - qwen2.5:32b-instruct-q4_K_M (20GB)

GPU Status:
  GPU 0:
    Utilization: 85%
    Memory: 10240MB / 12288MB (83%)

Recommendations:
  ✓ Gemini quota fully available (20 requests today)
  ✓ Ollama running with models: qwen2.5:32b-instruct-q4_K_M
```

**Integration with Workflow:**

Add to your daily workflow:

```bash
# Morning - check available quotas
python scripts/monitor_ai_resources.py

# After using Copilot (manually track)
python scripts/monitor_ai_resources.py --record-copilot 25

# After using Gemini
python scripts/monitor_ai_resources.py --record-gemini 10

# End of day - review usage
python scripts/monitor_ai_resources.py
```

## Quick Start

### First Time Setup

```bash
# 1. Run automated setup
python scripts/setup_ai_agents.py

# 2. Edit .env and add your API keys
nano .env  # or your preferred editor

# 3. Restart Docker services to pick up env changes
docker compose restart

# 4. Verify everything is working
python scripts/monitor_ai_resources.py
```

### Daily Usage

```bash
# Morning - check quotas
python scripts/monitor_ai_resources.py

# Work on tasks...

# Evening - track usage and get recommendations
python scripts/monitor_ai_resources.py --record-copilot 30 --record-gemini 15
```

## Configuration

### Resource Limits

Edit `.ai_usage_tracking.json` to customize limits:

```json
{
  "copilot": {
    "monthly_limit": 1500
  },
  "gemini": {
    "daily_limit": 20
  }
}
```

### GPU Detection

Scripts automatically detect NVIDIA GPUs using `nvidia-smi`. For other GPUs, models will default to CPU-compatible options.

## Troubleshooting

### Setup Script Issues

**"Docker daemon is not running"**
- Start Docker Desktop
- On Linux: `sudo systemctl start docker`

**"Ollama is not installed"**
- Windows: Download from https://ollama.ai/download
- Mac: `brew install ollama`
- Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

**"Failed to pull model"**
- Check internet connection
- Verify sufficient disk space (models are 2-20GB)
- Try a smaller model first: `ollama pull llama3.2:3b`

### Monitor Script Issues

**"No GPU detected"**
- Install NVIDIA drivers
- Verify with: `nvidia-smi`
- Script will still work, just won't show GPU stats

**"Ollama offline"**
- Start Ollama: `ollama serve` (Linux)
- On Windows/Mac, Ollama runs as background service

## Advanced Usage

### Automated Daily Monitoring

Add to your shell profile (`.bashrc`, `.zshrc`, or PowerShell profile):

```bash
# Show AI resource status on terminal startup
alias ai-status='python scripts/monitor_ai_resources.py'
```

### CI/CD Integration

Use in CI pipelines to track automated AI usage:

```yaml
- name: Track AI usage
  run: |
    python scripts/monitor_ai_resources.py --record-copilot ${{ env.COPILOT_REQUESTS }}
```

### Custom Tracking

Integrate into your tools:

```python
from scripts.monitor_ai_resources import ResourceMonitor

monitor = ResourceMonitor()
monitor.record_gemini_usage(5)
recommendations = monitor.get_recommendations()
```

## Files Created

- `.ai_usage_tracking.json` - Usage data (git-ignored)
- `.env` - Environment variables (git-ignored)

## See Also

- [Main README](../README.md) - Complete project documentation
- [Ollama Setup Guide](../OLLAMA_SETUP.md) - Local AI model setup
- [Free Hosting Options](../docs/FREE_HOSTING_OPTIONS.md) - Deployment guides
- [TODO & Roadmap](../docs/TODO.md) - Feature roadmap
