# Ollama Code Assistant - Quick Reference Card

## Installation (2 minutes)
```bash
# Windows
winget install Ollama.Ollama

# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Pull best model (12GB VRAM)
ollama pull qwen2.5-coder:32b
```

## Common Commands

### Code Review
```bash
# Single file
python scripts/ollama_code_assistant.py review src/app/job_finder.py

# Entire directory (batch)
python scripts/ollama_code_assistant.py review src/app/ --batch --format json

# With specific model
python scripts/ollama_code_assistant.py review src/app/email_processor.py -m deepseek-coder:33b
```

### Generate Docstrings
```bash
# Single file (stdout)
python scripts/ollama_code_assistant.py docstring src/app/job_tracker.py > temp.py

# Batch (creates *_documented.py)
python scripts/ollama_code_assistant.py docstring src/app/ --batch
```

### Generate Tests
```bash
# Generate pytest tests
python scripts/ollama_code_assistant.py test src/app/email_processor.py -o tests/

# Batch test generation
for file in src/app/*.py; do
    python scripts/ollama_code_assistant.py test "$file" -o tests/
done
```

### Refactoring Analysis
```bash
# Analyze code smells
python scripts/ollama_code_assistant.py refactor src/app/ui_server.py --format json

# Save to file
python scripts/ollama_code_assistant.py refactor src/app/ --batch > refactor_report.json
```

### Model Recommendation
```bash
# Get best model for task
python scripts/ollama_code_assistant.py recommend "code review" --vram 12
python scripts/ollama_code_assistant.py recommend "test generation" --vram 8
```

## Model Selection

### By Hardware
| VRAM | Model | Command Flag |
|------|-------|--------------|
| 4GB | qwen2.5-coder:7b | `-m qwen2.5-coder:7b` |
| 8GB | qwen2.5-coder:14b | `-m qwen2.5-coder:14b` |
| 12GB+ | **qwen2.5-coder:32b** | `-m qwen2.5-coder:32b` (default) |

### By Task
| Task | Best Model | Why |
|------|------------|-----|
| Code review | qwen2.5-coder:32b | Best bug detection |
| Code generation | deepseek-coder:33b | Specialized |
| Documentation | codellama:34b | Clear explanations |
| Visual + code | qwen3-vl-32b-instruct | Screenshots/diagrams |

## Integration Examples

### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python scripts/ollama_code_assistant.py review src/ --batch --format json > .review.json

high_severity=$(python -c "
import json
with open('.review.json') as f:
    data = json.load(f)
    print(sum(1 for file in data.values() if file.get('severity') == 'high'))
")

if [ "$high_severity" -gt 0 ]; then
    echo "❌ Found $high_severity high severity issues"
    exit 1
fi
```

### Python Integration
```python
from scripts.ollama_code_assistant import OllamaAssistant

# Initialize
assistant = OllamaAssistant("qwen2.5-coder:32b")

# Query
result = assistant.query(
    "Your prompt here",
    system_prompt="Optional system context"
)
print(result)
```

### Resume Analysis (Privacy)
```python
from scripts.ollama_code_assistant import OllamaAssistant

assistant = OllamaAssistant("qwen2.5-coder:32b")

with open("data/resume.txt") as f:
    resume = f.read()

skills = assistant.query(
    f"Extract technical skills: {resume}",
    system_prompt="List as comma-separated values"
)
```

## Troubleshooting

### "Ollama not installed"
```bash
# Check status
Get-Service Ollama  # Windows
ollama list         # Linux/Mac

# Start service
Start-Service Ollama  # Windows
ollama serve &        # Linux/Mac
```

### "Model not found"
```bash
# List models
ollama list

# Pull model
ollama pull qwen2.5-coder:32b
```

### Out of Memory
```bash
# Use smaller model
ollama pull qwen2.5-coder:7b
python scripts/ollama_code_assistant.py review file.py -m qwen2.5-coder:7b

# Or CPU inference (slower)
OLLAMA_DEVICE=cpu ollama run qwen2.5-coder:32b
```

### Slow Performance
```bash
# Check GPU usage
nvidia-smi  # Should show model loaded

# Close GPU-heavy apps
# Use batch mode for multiple files
python scripts/ollama_code_assistant.py review src/app/ --batch
```

## Performance Tips

### Batch Processing
```bash
# ❌ Inefficient (loads model each time)
for file in *.py; do python scripts/ollama_code_assistant.py review "$file"; done

# ✅ Efficient (loads model once)
python scripts/ollama_code_assistant.py review src/app/ --batch
```

### Speed Comparison
- **Cold start** (first query): ~30 seconds
- **Warm queries** (subsequent): ~10-20 seconds
- **Batch mode** (10 files): ~2-3 minutes total

### Context Limits
| Model | Context | Max File Lines |
|-------|---------|----------------|
| qwen2.5-coder:32b | 32k tokens | ~2000 lines |
| deepseek-coder:33b | 16k tokens | ~1000 lines |
| codellama:34b | 16k tokens | ~1000 lines |

## Workflow Examples

### Daily Development
```bash
# Morning: Review yesterday's changes
git diff main --name-only | grep '\.py$' | xargs python scripts/ollama_code_assistant.py review

# During: Generate tests for new code
python scripts/ollama_code_assistant.py test src/app/new_feature.py -o tests/

# Evening: Update docs
python scripts/ollama_code_assistant.py docstring src/app/ --batch
```

### Code Review Session
```bash
# 1. Review all changes
python scripts/ollama_code_assistant.py review src/ --batch --format json > review.json

# 2. Check refactoring opportunities
python scripts/ollama_code_assistant.py refactor src/app/ui_server.py --format json

# 3. Generate missing tests
python scripts/ollama_code_assistant.py test src/app/email_processor.py -o tests/
```

### Privacy-Sensitive Operations
```bash
# Resume analysis (local only)
python -c "
from scripts.ollama_code_assistant import OllamaAssistant
assistant = OllamaAssistant('qwen2.5-coder:32b')
with open('data/resume.txt') as f:
    print(assistant.query(f'Extract skills: {f.read()}'))
"

# Email classification
python examples/ollama_examples.py  # Choose option 4
```

## Quick Links

- **Full Documentation**: [docs/OLLAMA_CODE_ASSISTANT.md](OLLAMA_CODE_ASSISTANT.md)
- **Quick Start Guide**: [docs/OLLAMA_QUICKSTART.md](OLLAMA_QUICKSTART.md)
- **Examples**: [examples/ollama_examples.py](../examples/ollama_examples.py)
- **Implementation Summary**: [docs/OLLAMA_IMPLEMENTATION_SUMMARY.md](OLLAMA_IMPLEMENTATION_SUMMARY.md)

## Best Practices

### ✅ Do
- Use batch mode for multiple files
- Start with qwen2.5-coder:32b (best overall)
- Use JSON format for programmatic parsing
- Keep files under context limit (~2000 lines)
- Close GPU-heavy apps during inference

### ❌ Don't
- Process files sequentially (use batch)
- Use models larger than your VRAM
- Forget to pull models before use
- Send very large files (>5000 lines)
- Run multiple models concurrently

## Keyboard Shortcuts (Interactive Mode)

```bash
# Run examples interactively
python examples/ollama_examples.py

# Options:
1 - Resume Analysis
2 - Batch Job Analysis
3 - Code Generation
4 - Email Analysis
5 - Code Review
6 - Test Generation
all - Run all examples
```

## Resource Monitor

### Check Usage
```bash
# GPU memory
nvidia-smi

# Disk space (models)
ollama list

# Process status
Get-Process ollama  # Windows
ps aux | grep ollama  # Linux/Mac
```

### Clean Up
```bash
# Remove unused models
ollama rm old-model:version

# Free disk space
docker system prune -a  # If using Docker
```

## Support

### Get Help
1. Check logs: Script outputs detailed info
2. Run examples: `python examples/ollama_examples.py`
3. Test Ollama: `ollama run qwen2.5-coder:32b "test"`
4. Check VRAM: `nvidia-smi`
5. Verify model: `ollama list`

### Report Issues
- Check [docs/OLLAMA_CODE_ASSISTANT.md](OLLAMA_CODE_ASSISTANT.md) troubleshooting section
- Verify Ollama version: `ollama --version`
- Check Python version: `python --version` (3.8+ required)

---

**Remember:** Local LLMs excel at privacy-sensitive operations, batch processing, and offline work. Use cloud LLMs (GitHub Copilot) for autonomous workflows and complex reasoning. Best practice: use both strategically! 🚀
