# Vibe Services Configuration

Detailed setup for Vibe Check MCP and Vibe Kanban services.

## Overview

Two containerized services for AI-powered development:

1. **Vibe Check MCP** (Port 3000) - Code review and architectural validation
2. **Vibe Kanban** (Port 3001) - Multi-agent task orchestration

Both run in Docker and are started with `docker compose up -d`.

## Vibe Check MCP

### Purpose

AI-powered code oversight that validates:
- Code against architectural standards
- Design patterns and best practices
- Security vulnerabilities
- Performance issues

### Configuration

**Location:** `vibe-check-mcp/.env`

```bash
# Choose your AI provider
GEMINI_API_KEY=your_gemini_key_here
# OR
OPENAI_API_KEY=your_openai_key_here

# Optional: Model selection
MODEL=gemini-pro  # or gpt-4
```

### Usage in IDE

**VS Code with MCP Extension:**
1. Install MCP extension
2. Configure server URL: `http://localhost:3000`
3. Enable auto-review on save

**Cline/Cursor:**
1. Settings → MCP Servers
2. Add: `http://localhost:3000`
3. Enable architectural checks

### API Endpoints

```bash
# Health check
curl http://localhost:3000/health

# Code review
curl -X POST http://localhost:3000/review \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello():\n    print(\"world\")", "language": "python"}'

# Architectural validation
curl -X POST http://localhost:3000/validate \
  -H "Content-Type: application/json" \
  -d '{"file": "src/app/main.py", "architecture": "docs/architecture.md"}'
```

## Vibe Kanban

### Purpose

Visual kanban board for coordinating parallel AI work:
- 9 work tracks (P0-P3 priorities)
- Agent assignment
- Progress tracking
- Dependency management

### Access

Open <http://localhost:3001> in your browser

### Features

**Board Columns:**
- Backlog
- In Progress
- Review
- Done

**Work Tracks:**
1. Memory Bank Documentation (P0)
2. Email Server Integration (P1)
3. Provider-Agnostic AI (P1)
4. Learning System (P2)
5. AI Profile System (P2)
6. Small LM Integration (P2)
7. Tech Demo Generator (P3)
8. Testing Suite (P2)
9. Documentation (P1)

### Agent Assignment

**Available Agents:**
- GitHub Copilot Pro (50 req/day)
- Gemini API (20 req/day)
- Local LLM (unlimited)
- Vibe Check MCP (unlimited)

**Assignment Rules:**
- High complexity → Copilot Pro
- Documentation/Tests → Gemini
- Analysis/Refactoring → Local LLM
- Code Review → Vibe Check MCP

### API Endpoints

```bash
# Health check
curl http://localhost:3001/health

# List all tasks
curl http://localhost:3001/api/tasks

# Create task
curl -X POST http://localhost:3001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Implement feature X", "track": 2, "priority": "P1", "agent": "copilot"}'

# Update task status
curl -X PATCH http://localhost:3001/api/tasks/123 \
  -H "Content-Type: application/json" \
  -d '{"status": "in-progress"}'
```

## Docker Configuration

### docker-compose.yml

```yaml
services:
  vibe-check-mcp:
    image: vibe-check-mcp:latest
    ports:
      - "3000:3000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped

  vibe-kanban:
    image: vibe-kanban:latest
    ports:
      - "3001:3001"
    volumes:
      - kanban-data:/app/data
    restart: unless-stopped

volumes:
  kanban-data:
```

### Starting Services

```bash
# Start both services
docker compose up -d vibe-check-mcp vibe-kanban

# Check status
docker compose ps

# View logs
docker compose logs -f vibe-check-mcp
docker compose logs -f vibe-kanban

# Restart individual service
docker compose restart vibe-check-mcp
```

## Troubleshooting

### Port Already in Use

**Check what's using the port:**
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :3001

# Linux/Mac
lsof -i :3000
lsof -i :3001
```

**Change ports in docker-compose.yml:**
```yaml
ports:
  - "3002:3000"  # Change left side only
```

### Service Won't Start

**Check logs:**
```bash
docker compose logs vibe-check-mcp
docker compose logs vibe-kanban
```

**Common issues:**
- Missing API key in `.env`
- Port conflict
- Docker daemon not running

**Solutions:**
```bash
# Verify .env file exists
cat .env

# Restart Docker Desktop
# Windows: Right-click Docker icon → Restart

# Clean restart
docker compose down
docker compose up -d
```

### API Key Issues

**Vibe Check MCP needs an AI provider:**
```bash
# Edit vibe-check-mcp/.env
echo "GEMINI_API_KEY=your_key_here" >> vibe-check-mcp/.env

# Restart service
docker compose restart vibe-check-mcp
```

### Can't Access Web UI

**Check container is running:**
```bash
docker compose ps vibe-kanban
```

**Test from terminal:**
```bash
curl http://localhost:3001/health
```

**Firewall blocking:**
- Windows: Allow Docker in Windows Defender
- Linux: Check `ufw` rules
- Mac: Check System Preferences → Security

## Integration with Parallel Work

### Daily Workflow

**Morning:**
1. Open Vibe Kanban (<http://localhost:3001>)
2. Review task board
3. Assign tasks to AI agents
4. Move tasks to "In Progress"

**During Work:**
1. Vibe Check MCP validates code automatically
2. Update task status in Vibe Kanban
3. Track quota usage per agent

**End of Day:**
1. Move completed tasks to "Done"
2. Review tomorrow's priorities
3. Reassign blocked tasks

### Resource Allocation

Use Vibe Kanban to:
- Track which agent is working on what
- Avoid overusing paid APIs (Copilot, Gemini)
- Balance load across agents
- Identify bottlenecks

## Advanced Configuration

### Custom Review Rules

**vibe-check-mcp/rules.yaml:**
```yaml
rules:
  - name: "No hardcoded secrets"
    pattern: "password|api_key|secret"
    severity: "critical"

  - name: "Use type hints"
    pattern: "def .*\\(.*\\):"
    severity: "warning"
    python_only: true
```

### Webhook Integration

**Notify on task completion:**
```yaml
# vibe-kanban/config.yaml
webhooks:
  - event: "task.done"
    url: "https://slack.com/api/webhook/..."
    method: "POST"
```

## Next Steps

1. Start services: `docker compose up -d`
2. Open Vibe Kanban: <http://localhost:3001>
3. Create first task in board
4. Configure IDE to use Vibe Check MCP
5. Start parallel work following `PARALLEL_WORK_STRATEGY.md`

## References

<!-- Vibe Check MCP and Vibe Kanban repositories are not public yet -->
<!-- Contact project maintainer for access to these custom services -->
- MCP Protocol: <https://modelcontextprotocol.io>
