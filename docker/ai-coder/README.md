# AI Coder - Autonomous Development Container

Containerized AI development system using Aider + Ollama for fully autonomous code generation.

## Overview

AI Coder watches `.ai-tasks/*.md` files and autonomously implements requested changes using Aider with Ollama LLM.

### Key Features

- **Zero Manual Intervention**: Runs autonomously, no UI required
- **Task-Based**: Reads task files, executes, marks complete/failed
- **Git Integration**: Commits changes with `[AI]` attribution
- **Optimized**: Uses `uv` for 10-100x faster Python installs

## Architecture

```
Auto-Dev Service (PowerShell)
      ↓ creates task files
.ai-tasks/task_TIMESTAMP.md
      ↓ watched by container
AI Coder Container (Docker)
      ↓ executes with Aider
Git Repository (auto-commit)
```

## Setup

### 1. Start Ollama

```powershell
ollama serve
ollama pull qwen2.5-coder:32b
```

### 2. Build Container

```powershell
docker compose build ai-coder
```

### 3. Start Services

```powershell
# Start AI Coder container
docker compose up -d ai-coder

# Start auto-dev service (creates tasks from TODO.md)
.\scripts\start_autodev_service.ps1
```

## Usage

### Manual Task Creation

Create a task file in `.ai-tasks/`:

```markdown
# Task: Add unit tests for email parser

Create comprehensive unit tests for src/app/email_parser.py covering:
- Email type detection
- Company extraction
- URL parsing
- Edge cases

Use pytest with fixtures. Follow existing test patterns.
```

AI Coder will:
1. Detect the .md file
2. Execute with Aider + Ollama
3. Commit changes with `[AI]` tag
4. Mark file as `.processed` or `.failed`

### Auto-Dev Service

The service watches `docs/TODO.md` and auto-creates tasks:

```powershell
# Start service
.\scripts\start_autodev_service.ps1

# Check status
.\scripts\monitor_autodev.ps1
```

## Configuration

Environment variables (in `docker-compose.yml`):

- `OLLAMA_BASE_URL`: Ollama API endpoint (default: `http://host.docker.internal:11434`)
- `OLLAMA_MODEL`: Model to use (default: `qwen2.5-coder:32b`)
- `CHECK_INTERVAL`: Seconds between task checks (default: `30`)

## Troubleshooting

### Container not processing tasks

```powershell
# Check container logs
docker compose logs ai-coder

# Verify Ollama is accessible
docker compose exec ai-coder curl http://host.docker.internal:11434/api/version
```

### Tasks marked as .failed

Check container logs for Aider errors:
```powershell
docker compose logs ai-coder | Select-String "ERROR"
```

### Git permission issues

The container runs git commits inside the mounted workspace. Ensure git is configured:

```powershell
git config user.name
git config user.email
```

## Comparison: AI Coder vs Cline

| Feature | AI Coder | Cline |
|---------|----------|-------|
| **Automation** | Fully autonomous | Requires manual click |
| **Setup** | Docker container | VS Code extension |
| **Trigger** | File watcher | Manual "Start New Task" |
| **24/7 Operation** | Yes | No (VS Code must be open) |
| **Host Changes** | None | VS Code + extensions |

## Architecture Details

### Task Processor Loop

```python
while True:
    task = find_pending_task()
    if task:
        execute_with_aider(task)
        commit_changes()
        mark_processed()
    sleep(30)
```

### File States

- `.ai-tasks/task.md` - Pending
- `.ai-tasks/task.md.processed` - Completed successfully
- `.ai-tasks/task.md.failed` - Execution failed

### Git Attribution

All commits include:
```
[AI] feat: description

---
AI-Generated-By: Aider (qwen2.5-coder:32b via Ollama)
```

## Performance

- **Dockerfile**: Optimized with `uv` (10-100x faster than pip)
- **Container**: Single-stage, minimal layers
- **Startup**: < 10 seconds
- **Task Check**: Every 30 seconds (configurable)

## Security

- **No API Keys**: Uses local Ollama (no cloud)
- **Git Signing**: All commits attributed to AI Coder
- **Workspace Mount**: Read/write access to project
- **Network**: Only connects to host Ollama

## Monitoring

```powershell
# Watch task processing
Get-ChildItem .ai-tasks/*.processed | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Check failures
Get-ChildItem .ai-tasks/*.failed
```

## Stopping

```powershell
# Stop container
docker compose stop ai-coder

# Stop auto-dev service
Stop-Job -Name AICoderAutoDev
```
