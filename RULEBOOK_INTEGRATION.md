# Rulebook-AI Integration

This project uses [rulebook-ai](https://github.com/botingw/rulebook-ai) to provide context-aware AI assistant instructions across different development contexts.

## What is Rulebook-AI?

Rulebook-AI is a framework for managing AI assistant rules and context using composable "packs" and "profiles". It generates assistant-specific rule files (like `.github/copilot-instructions.md`) from reusable rule sets, ensuring your AI coding assistants have the right context for each task.

## Project Structure

```
job-lead-finder/
├── .rulebook-ai/          # Framework state (git-ignored)
│   ├── packs/             # Local copies of rule packs
│   ├── selection.json     # Configured packs and profiles
│   └── sync_status.json   # Last sync metadata
├── memory/                # Project context (committed to git)
│   ├── docs/              # Architecture, PRD, technical docs
│   │   ├── product_requirement_docs.md
│   │   ├── architecture.md
│   │   └── technical.md
│   └── tasks/             # Task tracking and active context
│       ├── tasks_plan.md
│       └── active_context.md
├── tools/                 # Project-specific tools (committed to git)
│   ├── llm_api.py        # Multi-provider LLM client
│   ├── search_engine.py  # DuckDuckGo search
│   └── web_scraper.py    # Webpage content extraction
└── .github/               # Generated AI instructions (git-ignored)
    └── copilot-instructions.md  # GitHub Copilot rules
```

## Installed Packs

### light-spec
General-purpose pack providing foundational software engineering principles:
- **Meta-rules** - Mode determination (Planning/Implementation/Debugging)
- **Memory Bank** - Project context management system
- **General Principles** - Code quality, security, testing, documentation
- **Workflows** - Structured approaches for planning, coding, and debugging

## Configured Profiles

Profiles allow switching between specialized contexts for different tasks:

- **frontend** - Web UI development (HTML, CSS, JavaScript, FastAPI templates)
- **backend** - API development (FastAPI, SQLAlchemy, business logic)
- **worker** - Background job processing and async tasks
- **docker** - Containerization and deployment
- **cicd** - GitHub Actions, pre-commit hooks, automation
- **testing** - Test development, mocking, pytest fixtures

## Usage

### Syncing Rules

Generate AI instructions for all assistants:
```bash
python -m rulebook_ai project sync
```

Generate for specific assistant only:
```bash
python -m rulebook_ai project sync --assistant copilot
```

Generate using a specific profile:
```bash
python -m rulebook_ai project sync --profile backend --assistant copilot
```

Generate using ad-hoc pack selection:
```bash
python -m rulebook_ai project sync --pack light-spec --assistant copilot
```

### Managing Profiles

Create a new profile:
```bash
python -m rulebook_ai profiles create <profile-name>
```

Add a pack to a profile:
```bash
python -m rulebook_ai profiles add <pack-name> --to <profile-name>
```

List all profiles:
```bash
python -m rulebook_ai profiles list
```

### Managing Packs

Add a new pack:
```bash
python -m rulebook_ai packs add <pack-name>
```

List available packs:
```bash
python -m rulebook_ai packs list
```

Check current configuration:
```bash
python -m rulebook_ai packs status
```

### Project Status

View last sync information:
```bash
python -m rulebook_ai project status
```

## Memory Bank System

The `memory/` directory contains living documentation that provides context to AI assistants:

### Core Files (Required)

1. **product_requirement_docs.md** - Why this project exists, problems it solves, requirements
2. **architecture.md** - System design, component relationships, data flow
3. **technical.md** - Tech stack, development setup, technical decisions
4. **tasks_plan.md** - Task backlog, progress tracking, known issues
5. **active_context.md** - Current work focus, recent changes, next steps

### Workflow Modes

The rulebook system operates in three modes based on task context:

- **PLANNING Mode** - High-level design, architecture, solution exploration
- **IMPLEMENTATION Mode** - Writing code, implementing features, making changes
- **DEBUGGING Mode** - Fixing errors, diagnosing issues, troubleshooting

Modes are inferred automatically from your request, or you can specify explicitly:
```
FOCUS = PLANNING: Let's design the new caching system
FOCUS = IMPLEMENTATION: Implement the caching layer for job results
FOCUS = DEBUGGING: Fix the memory leak in the job fetcher
```

## Tools Integration

The `tools/` directory contains reusable utilities:

### llm_api.py
Multi-provider LLM client supporting:
- OpenAI (gpt-4o)
- Azure OpenAI
- DeepSeek (deepseek-chat)
- Anthropic (claude-3-sonnet)
- Gemini (gemini-pro)
- Local LLM (Qwen/Qwen2.5-32B-Instruct-AWQ)

Usage:
```bash
python tools/llm_api.py --prompt "Your question" --provider anthropic
```

### search_engine.py
DuckDuckGo search integration:
```bash
python tools/search_engine.py "your search keywords"
```

### web_scraper.py
Concurrent webpage content extraction:
```bash
python tools/web_scraper.py --max-concurrent 3 URL1 URL2 URL3
```

## Customization

### Adding New Memory Files

Create additional context files in `memory/docs/` or `memory/tasks/`:
```bash
memory/docs/deployment_guide.md
memory/docs/security_policy.md
memory/tasks/sprint_2024_12.md
```

These files are automatically included in the AI context during syncs.

### Creating Custom Packs

For project-specific rules that might be reused:

1. Create a local pack directory with required structure:
```
my-custom-pack/
├── manifest.yaml
├── README.md
└── rules/
    └── 01-rules/
        └── 01-custom-rule.md
```

2. Add the local pack:
```bash
python -m rulebook_ai packs add local:../my-custom-pack
```

## Best Practices

### When to Update Memory Files

- **product_requirement_docs.md** - When requirements change or new features are planned
- **architecture.md** - After significant system design changes
- **technical.md** - When adding new dependencies or changing dev setup
- **tasks_plan.md** - Daily/weekly to track progress and priorities
- **active_context.md** - Before starting new work session

### When to Resync

Run `python -m rulebook_ai project sync` after:
- Adding or removing packs
- Updating memory files with significant context changes
- Switching between major work contexts (frontend → backend)
- Adding new assistant support (e.g., adding Cursor alongside Copilot)

### Profile Usage Recommendations

- **Use `--profile frontend`** when working on UI, templates, styling
- **Use `--profile backend`** when working on APIs, database, business logic
- **Use `--profile testing`** when writing or optimizing tests
- **Use `--profile docker`** when working on deployment, containers
- **Use `--profile cicd`** when updating GitHub Actions, pre-commit hooks
- **Use default (all packs)** for general development or refactoring

## Troubleshooting

### "No module named 'rulebook_ai'"
Install rulebook-ai:
```bash
pip install git+https://github.com/botingw/rulebook-ai.git
```

### Copilot instructions not updating
1. Check sync status: `python -m rulebook_ai project status`
2. Resync: `python -m rulebook_ai project sync --assistant copilot`
3. Restart your editor to reload instructions

### Memory files ignored by AI
1. Ensure files exist in `memory/docs/` or `memory/tasks/`
2. Verify sync completed: `python -m rulebook_ai project status`
3. Check file format (markdown with clear structure)

## Contributing

When adding new features or making architectural changes:

1. Update relevant memory files first
2. Resync to update AI instructions
3. Commit both memory files and generated instructions
4. Include memory updates in your PR description

## Resources

- **Rulebook-AI Documentation**: https://github.com/botingw/rulebook-ai
- **Tutorial**: https://github.com/botingw/rulebook-ai/blob/main/memory/docs/user_guide/tutorial.md
- **Community Packs**: https://github.com/botingw/rulebook-ai (see packs directory)
- **Pack Authoring Guide**: `python -m rulebook_ai packs add pack-authoring-guide`

## License

The rulebook-ai integration follows this project's MIT license. Individual packs may have their own licenses (check pack README.md files).
