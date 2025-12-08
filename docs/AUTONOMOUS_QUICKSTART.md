# Autonomous AI Execution System - Quick Start

## 🎯 What This Does

Enables AI agents (Gemini, Copilot, Local LLM) to autonomously work through your TODO list with minimal human interaction. The system:

1. **Reads TODOs** from `docs/TODO.md`
2. **Assigns tasks** to optimal AI agent based on priority and quota
3. **Executes work** on feature branches
4. **Validates code** via Vibe Check MCP
5. **Creates PRs** for human review

## 🚀 Quick Start

### 1. Initialize Memory Bank (One-time setup)

```bash
python scripts/init_memory_bank.py
```

This creates the Memory Bank files that AI agents read for context:
- `memory/docs/architecture.md` - System design
- `memory/docs/technical.md` - Tech stack and standards
- `memory/tasks/tasks_plan.md` - Task backlog
- `memory/tasks/active_context.md` - Current work state

### 2. Review the Execution Plan (Dry Run)

```bash
python scripts/autonomous_task_executor.py
```

**What this does:**
- Parses tasks from `docs/TODO.md`
- Checks AI resource availability (Copilot, Gemini, Ollama)
- Assigns optimal agent to each task
- Generates execution plan
- Creates AI guidance files in `.ai-tasks/`

**Output:**
```
📊 Available Resources:
   Copilot Pro: 1500/1500 requests
   Gemini API:  20/20 requests (today)
   Local LLM:   unknown

📝 Task Assignments:
   Track 2: Email Server Integration (P1)
      → Agent: COPILOT
      → Progress: 0/5 items completed

   Track 3: Learning from Job Suggestions (P1)
      → Agent: COPILOT
      → Progress: 0/4 items completed
```

### 3. Execute Tasks Autonomously (Live Mode)

```bash
python scripts/autonomous_task_executor.py --execute
```

**What this does:**
- Creates tasks in Vibe Kanban (http://localhost:3001)
- Generates AI guidance files with full context
- (Future) Triggers AI agent execution via Cline extension

## 📊 Monitoring Progress

### Three Dashboards:

1. **Vibe Kanban** (http://localhost:3001)
   - Task status and progress
   - Track assignments
   - Blockers and completions

2. **AI Resource Monitor** (http://localhost:9000)
   - Real-time quota usage
   - Copilot: 1500 requests/month
   - Gemini: 20 requests/day
   - Ollama: Status and models

3. **Vibe Check MCP** (http://localhost:3000)
   - Code validation results
   - Quality checks
   - Pre-commit validation

## 🤖 How It Works

### Agent Assignment Strategy

```
P0 (Foundation)  → Gemini    (Free, excellent for documentation)
P1 (High-Value)  → Copilot   (Premium, critical implementation)
P2+ (Lower)      → Local LLM (Unlimited, privacy-focused)

Fallback Chain: Local LLM → Gemini → Copilot
```

### Workflow Per Task

1. **Pre-Task**:
   - Read Memory Bank files (architecture, technical, etc.)
   - Check AI resource availability
   - Create feature branch: `auto/track-{id}-{name}`

2. **During Task**:
   - Follow code style from `memory/docs/technical.md`
   - Write tests for new code
   - Run `pytest` before committing
   - Update `memory/tasks/active_context.md` with progress

3. **Post-Task**:
   - Validate code with Vibe Check MCP
   - Run full test suite: `pytest -n auto`
   - Update `memory/tasks/tasks_plan.md` (mark completed)
   - Create PR with checklist
   - Update Vibe Kanban task status

## 📁 Key Files

### Created by Init Script
- `.ai-tasks/*.md` - AI guidance files (one per track)
- `memory/docs/architecture.md` - System architecture
- `memory/docs/technical.md` - Tech stack and standards
- `memory/tasks/tasks_plan.md` - Task backlog
- `memory/tasks/active_context.md` - Current work state

### Configuration
- `.claude/settings.json` - Claude Task Master configuration
- `.vscode/settings.json` - VS Code Cline MCP integration

### Scripts
- `scripts/autonomous_task_executor.py` - Main orchestrator
- `scripts/init_memory_bank.py` - One-time setup

## 🔧 Current Status

### ✅ What's Working

- ✅ Memory Bank initialization
- ✅ TODO parsing from `docs/TODO.md`
- ✅ AI resource monitoring (Copilot, Gemini, Ollama)
- ✅ Agent assignment based on priority and quota
- ✅ Execution plan generation
- ✅ AI guidance file creation
- ✅ Vibe Kanban task creation
- ✅ All 6 Docker containers running

### ⏳ What's Next

1. **Install Cline Extension** (VS Code)
   - Extension ID: `saoudrizwan.claude-dev`
   - Enables Claude Task Master integration
   - Reads `.claude/settings.json` for autonomous mode

2. **Run Rulebook-AI Sync** (Optional)
   ```bash
   python -m rulebook_ai project sync
   ```
   - Generates `.cursor/rules/` from Memory Bank
   - Improves GitHub Copilot context

3. **Execute First Track** (Manual for now)
   - Review guidance file in `.ai-tasks/track-2-copilot.md`
   - Feed to Claude/Copilot for execution
   - Validate with Vibe Check MCP

4. **Future: Full Automation**
   - Cline extension will auto-execute tasks from Kanban
   - Human intervention only for PR approval

## 📝 Example: Execute Track 2 (Email Server)

### 1. Review the guidance:
```bash
cat .ai-tasks/track-2-copilot.md
```

### 2. Feed to AI agent:
- **Option A** (Copilot Chat): Paste the guidance file
- **Option B** (Claude/Cline): Extension auto-reads from Kanban
- **Option C** (Manual): Implement following the checklist

### 3. Monitor progress:
- Vibe Kanban: http://localhost:3001
- AI Monitor: http://localhost:9000

### 4. Validate before PR:
```bash
# Run tests
pytest -n auto -m ""

# Validate with Vibe Check (manual for now)
curl -X POST http://localhost:3000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"files": ["src/app/email_server.py"]}'
```

## 🎯 Success Criteria

### For Each Track:
- ✅ All objectives from guidance file completed
- ✅ Tests passing (`pytest -n auto`)
- ✅ Code passes linting (`black`, `flake8`, `isort`)
- ✅ Documentation updated
- ✅ PR created with checklist
- ✅ Vibe Check validation passed

## 🔍 Troubleshooting

### "No tasks found" error
**Cause:** TODO.md structure changed
**Fix:** Update parser in `autonomous_task_executor.py` line 58-95

### Vibe Kanban not accessible
**Cause:** Container not running
**Fix:**
```bash
docker compose ps  # Check status
docker compose up -d vibe-kanban  # Restart if needed
```

### AI quota exhausted
**Cause:** Gemini daily limit (20) or Copilot monthly limit (1500)
**Fix:**
- Check: http://localhost:9000/api/metrics
- Fallback: Use Local LLM (install Ollama)
- Wait: Gemini resets daily, Copilot resets monthly

### Ollama "unknown" status
**Cause:** Ollama not installed or not running
**Fix:**
```bash
# Install Ollama
# Windows: Download from https://ollama.com
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Verify
ollama ps
```

## 📚 Additional Resources

- **Setup Guides**:
  - `docs/AI_AGENT_SETUP.md` - Main setup guide
  - `docs/LOCAL_LLM_SETUP.md` - Ollama installation
  - `docs/VIBE_SERVICES_SETUP.md` - Kanban/MCP setup
  - `docs/AUTONOMOUS_AI_SETUP.md` - Detailed architecture

- **Monitoring**:
  - AI Resource Monitor: http://localhost:9000
  - Vibe Kanban: http://localhost:3001
  - Vibe Check MCP: http://localhost:3000

- **Documentation**:
  - Memory Bank: `memory/` directory
  - Architecture: `memory/docs/architecture.md`
  - Tech Stack: `memory/docs/technical.md`

---

**Last Updated**: 2025-12-08
**Status**: 🟢 System initialized and validated - Ready for autonomous execution
