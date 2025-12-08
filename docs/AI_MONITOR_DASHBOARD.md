# AI Resource Monitor

A containerized web dashboard for monitoring AI resource usage across multiple providers.

## Features

- 📊 **Real-time Monitoring**: Track usage across GitHub Copilot Pro, Gemini API, and Local LLM
- 📈 **Visual Charts**: Interactive doughnut and bar charts using Chart.js
- 🎯 **Quota Tracking**: Monitor daily/monthly limits with visual progress indicators
- 🖥️ **GPU Monitoring**: Track GPU utilization and VRAM usage (NVIDIA GPUs)
- 💡 **Smart Recommendations**: Get optimization suggestions based on current usage
- 🔄 **Auto-Refresh**: Dashboard updates every 30 seconds
- 🐳 **Containerized**: Runs in Docker, no manual setup required

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services including AI monitor
docker compose up -d

# Access the dashboard
# Open http://localhost:9000 in your browser
```

The AI monitor service will be available at **http://localhost:9000**

### Manual Usage (Development)

```bash
# Install dependencies
pip install flask

# Run the monitor
python -m app.ai_monitor_ui

# Access at http://localhost:9000
```

## Dashboard Overview

### Metrics Displayed

1. **GitHub Copilot Pro**
   - Daily request count
   - Monthly usage vs 1500/month limit
   - Remaining requests
   - Usage percentage (doughnut chart)

2. **Gemini API**
   - Daily request count vs 20/day limit
   - Remaining requests
   - Usage percentage (doughnut chart)

3. **Local LLM (Ollama)**
   - Server status (running/stopped)
   - Active model count
   - List of loaded models with sizes

4. **GPU Status** (NVIDIA only)
   - GPU name/model
   - Utilization percentage
   - VRAM usage (GB)
   - Visual bar charts for utilization and VRAM

5. **Recommendations**
   - Optimization suggestions based on quota usage
   - Warnings when approaching limits (>80%)
   - Resource allocation tips

## API Endpoints

### `GET /`
Serves the web dashboard HTML

### `GET /api/metrics`
Returns JSON with current metrics:

```json
{
  "copilot": {
    "daily": 45,
    "monthly": 234,
    "monthly_limit": 1500,
    "remaining": 1266,
    "percentage_used": 15.6
  },
  "gemini": {
    "daily": 8,
    "daily_limit": 20,
    "remaining": 12,
    "percentage_used": 40.0
  },
  "ollama": {
    "status": "running",
    "models": [
      {"name": "qwen2.5:32b-q4", "size": "20GB"}
    ],
    "model_count": 1
  },
  "gpu": {
    "name": "NVIDIA GeForce RTX 4070 Ti",
    "gpu_util": 35.0,
    "mem_used_mb": 4096,
    "mem_total_mb": 12288
  },
  "recommendations": [
    "✓ All systems operating within normal parameters"
  ],
  "timestamp": "2025-12-08T14:30:00.123456"
}
```

## Usage Tracking

The monitor reads from `.ai_usage_tracking.json` (created by `scripts/monitor_ai_resources.py`).

To record usage:

```bash
# Record Copilot usage
python scripts/monitor_ai_resources.py --record-copilot 5

# Record Gemini usage
python scripts/monitor_ai_resources.py --record-gemini 3

# View CLI status
python scripts/monitor_ai_resources.py --status
```

## Docker Configuration

From `docker-compose.yml`:

```yaml
ai-monitor:
  extends: app
  build:
    args:
      INSTALL_TEST_DEPS: "false"
  volumes:
    - ./:/app:delegated
    - ai-tracking:/app/.ai_usage_tracking  # Persistent tracking data
  working_dir: /app
  ports:
    - "9000:9000"
  command: python -m app.ai_monitor_ui
  restart: unless-stopped
  depends_on:
    - ui
```

## Architecture

```
┌─────────────────┐
│   Web Browser   │
│  localhost:9000 │
└────────┬────────┘
         │ HTTP
         ├── GET /          → Dashboard HTML
         └── GET /api/metrics → JSON metrics
                 │
         ┌───────▼────────┐
         │ Flask Server   │
         │ (ai_monitor_ui)│
         └───────┬────────┘
                 │
         ┌───────▼────────────────────┐
         │ AIResourceMonitor Class    │
         ├────────────────────────────┤
         │ • Read tracking JSON       │
         │ • Query Ollama (ollama ps) │
         │ • Query GPU (nvidia-smi)   │
         │ • Generate recommendations │
         └────────────────────────────┘
```

## Screenshots

The dashboard displays:
- **Purple gradient background** for modern aesthetics
- **White cards** with rounded corners for each metric section
- **Colorful doughnut charts** for quota visualization
- **Bar charts** for GPU metrics
- **Auto-updating timestamp** showing last refresh time

## Requirements

- **Python 3.12+**
- **Flask 3.0+** (installed via `pip install -e ".[web]"`)
- **Docker** (for containerized deployment)
- **NVIDIA GPU** (optional, for GPU monitoring)
- **Ollama** (optional, for local LLM monitoring)

## Troubleshooting

### Dashboard shows "N/A" for metrics

The monitor reads from `.ai_usage_tracking.json`. If the file doesn't exist:

```bash
# Create initial tracking data
python scripts/monitor_ai_resources.py --status
```

### GPU metrics not showing

Ensure `nvidia-smi` is available:

```bash
# Test nvidia-smi
nvidia-smi
```

If not installed, GPU monitoring will be skipped (no errors).

### Ollama status shows "unknown"

Ensure Ollama is installed and running:

```bash
# Check Ollama
ollama ps
```

### Port 9000 already in use

Change the port in `docker-compose.yml`:

```yaml
ports:
  - "9001:9000"  # Change 9001 to your preferred port
```

## Integration with Parallel Work Strategy

The AI monitor dashboard is designed to support the [Parallel Work Strategy](../PARALLEL_WORK_STRATEGY.md):

1. **Resource Allocation**: See which AI provider has capacity
2. **Quota Management**: Avoid hitting API limits mid-task
3. **Cost Optimization**: Use free resources (Gemini, Ollama) before paid (Copilot)
4. **GPU Efficiency**: Monitor VRAM to optimize model selection

## Related Files

- `app/ai_monitor_ui.py` - Flask web server and monitor logic
- `scripts/monitor_ai_resources.py` - CLI tool for recording usage
- `.ai_usage_tracking.json` - Persistent usage data (created automatically)
- `docker-compose.yml` - Service configuration

## License

Same as parent project (job-lead-finder)
