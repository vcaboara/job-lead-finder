## Task Type
**Priority**: P2 (Enhancement - Evaluation Task)
**Agent**: TBD (Copilot vs Ollama comparison)
**Estimated Effort**: 2-3 hours
**Branch**: feature/kanban-board

## Context

The autonomous task executor references a Vibe Kanban board at http://localhost:3001, but this service doesn't exist yet. This is an **evaluation task** to compare:
- **GitHub Copilot** (premium tokens) for P0/P1 work
- **Ollama Local** (free, unlimited) for P2/P3 work

## Objective

Build a minimal task board service that integrates with `scripts/autonomous_task_executor.py`.

## Requirements

### 1. Backend Service (Node.js/Express or Python/FastAPI)

**REST API Endpoints**:
```
POST   /api/tasks          - Create new task
GET    /api/tasks          - List all tasks
GET    /api/tasks/:id      - Get task details
PATCH  /api/tasks/:id      - Update task status
DELETE /api/tasks/:id      - Delete task
```

**Task Schema**:
```json
{
  "id": 1,
  "title": "Email Server Integration",
  "track": 2,
  "priority": "P1",
  "agent": "copilot",
  "status": "backlog|in-progress|review|done",
  "items": [{"description": "...", "completed": false}],
  "created_at": "2025-12-09T19:00:00Z",
  "updated_at": "2025-12-09T19:30:00Z"
}
```

**Storage**: SQLite or JSON file (simple persistence)

### 2. Frontend UI (Optional but Nice)

**Tech**: Plain HTML/CSS/JS or React (keep it simple)

**Views**:
- Kanban board with columns: Backlog | In Progress | Review | Done
- Drag-and-drop between columns
- Filter by priority (P0/P1/P2/P3)
- Filter by agent (copilot/gemini/local)
- Real-time updates (WebSocket or polling)

### 3. Docker Integration

**Add to docker-compose.yml**:
```yaml
  vibe-kanban:
    build:
      context: ./kanban-service
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
    depends_on:
      - app
```

### 4. Integration with Task Executor

The existing `scripts/autonomous_task_executor.py` already has:
```python
def create_kanban_task(self, track: Dict, agent: str) -> Optional[int]:
    response = httpx.post(
        f"{self.kanban_url}/api/tasks",
        json={...},
        timeout=5,
    )
```

Ensure this works without modification.

## Acceptance Criteria

- [ ] Service runs on port 3001
- [ ] All REST API endpoints work
- [ ] Tasks persist across restarts
- [ ] `autonomous_task_executor.py --execute` creates tasks successfully
- [ ] Basic UI shows task list (bonus: Kanban view)
- [ ] Docker container runs via docker-compose
- [ ] README.md updated with Kanban service info
- [ ] Tests for API endpoints

## Tech Stack Suggestions

**Option A** (Python - matches project):
- FastAPI + SQLite
- Jinja2 templates or static HTML
- uvicorn server

**Option B** (Node.js - typical for Kanban):
- Express.js + SQLite/JSON
- Static HTML/CSS/JS frontend
- Optional: Socket.io for real-time

**Choose based on**: Fastest to implement, easiest to maintain

## Evaluation Criteria

This task will help evaluate:
1. **Code Quality**: Copilot vs Ollama output
2. **Speed**: Time to complete
3. **Iteration**: How many rounds needed
4. **Completeness**: Does it work on first try?

## Related

- `scripts/autonomous_task_executor.py` (integration point)
- `docker-compose.yml` (add service here)
- docs/VIBE_SERVICES_SETUP.md (document here)

---
AI-Task-Assignment: TBD (Evaluation Task)
Priority: P2
Estimated-Tokens: 2-3 premium requests (Copilot) OR unlimited (Ollama)
