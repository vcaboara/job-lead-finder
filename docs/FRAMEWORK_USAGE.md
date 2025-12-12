# Using the Framework Submodule

The `framework/` directory is a Git submodule pointing to [ai-search-match-framework](https://github.com/vcaboara/ai-search-match-framework).

## Development Workflow

### Making Changes That Flow Back to Framework

1. **Edit directly in `framework/` submodule:**
   ```bash
   cd framework
   # Make your changes to framework code
   git add .
   git commit -m "[AI] Your change description"
   git push
   ```

2. **Update job-lead-finder to use new framework version:**
   ```bash
   cd ..  # Back to job-lead-finder root
   git add framework
   git commit -m "[AI] Update framework submodule"
   git push
   ```

### Importing from Framework

Framework is installed as an editable package, so imports work directly:

```python
# Old way (deprecated):
from src.app.job_tracker import get_tracker

# New way (imports from framework):
from framework.src.tracker.job_tracker import get_tracker
```

### Keeping Framework Updated

```bash
# Pull latest framework changes
cd framework
git pull origin main

# Update submodule reference in job-lead-finder
cd ..
git add framework
git commit -m "[AI] Update framework to latest"
```

## Architecture

```
job-lead-finder/
├── framework/              # Submodule (ai-search-match-framework)
│   └── src/
│       ├── tracker/        # Core tracking logic
│       ├── providers/      # Base provider classes
│       ├── aggregator/     # Multi-source coordination
│       ├── ai/            # LLM interface
│       └── config/        # Configuration management
│
└── src/app/               # Job-specific implementations
    ├── job_finder.py      # Orchestration using framework
    ├── mcp_providers.py   # Job-specific providers
    └── gemini_provider.py # AI evaluation
```

## Benefits

1. **Shared Foundation**: Core patterns are reusable across projects
2. **Bidirectional Flow**: Improvements in job-lead-finder enhance the framework
3. **Version Control**: Submodule commits track which framework version is used
4. **Independent Development**: Framework can be used by other projects

## Example: Adding a New Tracker Feature

```python
# 1. Edit in framework
# framework/src/tracker/job_tracker.py
def export_markdown(self, output_path: str):
    """Export jobs to markdown format."""
    # Implementation here
    pass

# 2. Commit to framework
cd framework
git commit -am "[AI] Add markdown export to tracker"
git push

# 3. Use in job-lead-finder
from framework.src.tracker.job_tracker import get_tracker

tracker = get_tracker()
tracker.export_markdown("jobs.md")

# 4. Update submodule reference
cd ..
git add framework
git commit -m "[AI] Use framework's markdown export"
```

## Framework Installation

The framework is installed automatically as an editable dependency:

```toml
# pyproject.toml
dependencies = [
    "ai-search-match-framework @ file:///framework"
]
```

After cloning with submodules:
```bash
git clone --recurse-submodules https://github.com/vcaboara/job-lead-finder.git
cd job-lead-finder
uv pip install -e .  # Installs framework automatically
```
