# Ollama Quick Start Guide

Get local AI coding assistance running in 5 minutes.

## Prerequisites

- **Hardware**:
  - Minimum: 8GB RAM, 4GB VRAM
  - Recommended: 16GB+ RAM, 8GB+ VRAM
  - Optimal: 32GB+ RAM, 12GB+ VRAM (RTX 4070 Ti or better)
- **OS**: Windows 10/11, Linux, macOS
- **Disk Space**: 20-25GB for models

## Installation Steps

### 1. Install Ollama (2 minutes)

**Windows:**
```powershell
# Option 1: Download installer
# Visit https://ollama.ai/download and run installer

# Option 2: Winget
winget install Ollama.Ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

### 2. Verify Installation

```bash
ollama --version
# Should output: ollama version 0.x.x
```

### 3. Pull Your First Model (3-5 minutes)

**For 12GB VRAM (like RTX 4070 Ti):**
```bash
ollama pull qwen2.5-coder:32b
# Downloads ~21GB, takes 3-5 minutes
```

**For 8GB VRAM:**
```bash
ollama pull qwen2.5-coder:14b
# Downloads ~9GB
```

**For 4GB VRAM:**
```bash
ollama pull qwen2.5-coder:7b
# Downloads ~4.5GB
```

### 4. Test It

```bash
ollama run qwen2.5-coder:32b "Write a Python function to calculate fibonacci"
```

You should see code generated!

## First Real Usage

### Quick Code Review

```bash
# Review a single Python file
python scripts/ollama_code_assistant.py review src/app/job_finder.py

# Output shows bugs, security issues, style problems
```

### Generate Docstrings

```bash
# Add missing docstrings to file
python scripts/ollama_code_assistant.py docstring src/app/job_tracker.py > temp.py

# Review temp.py, then replace original if good
mv temp.py src/app/job_tracker.py
```

### Create Tests

```bash
# Generate pytest tests for module
python scripts/ollama_code_assistant.py test src/app/email_processor.py -o tests/

# New file created: tests/test_email_processor.py
```

## Model Selection Guide

### By Hardware

| VRAM | Recommended Model | Size | Performance |
|------|-------------------|------|-------------|
| 4GB | qwen2.5-coder:7b | 4.5GB | Good for basics |
| 6GB | apriel-1.5-15b-thinker | 9GB | Better reasoning |
| 8GB | qwen2.5-coder:14b | 9GB | Solid mid-tier |
| 12GB+ | **qwen2.5-coder:32b** | 21GB | **Best** |

### By Task

| Task | Best Model | Why |
|------|------------|-----|
| Code review | qwen2.5-coder:32b | Best at finding bugs |
| Code generation | deepseek-coder:33b | Specialized for generation |
| Documentation | codellama:34b | Explains well |
| Visual + code | qwen3-vl-32b-instruct | Can read screenshots |

**Get recommendation:**
```bash
python scripts/ollama_code_assistant.py recommend "code review" --vram 12
```

## Interactive Examples

Run the example integration script:

```bash
python examples/ollama_examples.py
```

Choose from:
1. Resume Analysis (privacy-sensitive)
2. Batch Job Description Analysis
3. Code Generation
4. Email Analysis
5. Pre-Commit Code Review
6. Test Generation

## Common Issues

### "Ollama not installed"

**Windows:**
- Check if service is running: `Get-Service Ollama`
- Restart: `Restart-Service Ollama`
- Or launch from Start menu

**Linux/Mac:**
```bash
# Start Ollama server
ollama serve &
```

### "Model not found"

```bash
# List available models
ollama list

# Pull missing model
ollama pull qwen2.5-coder:32b
```

### Slow Performance

1. **Check VRAM usage:**
   ```bash
   # Windows
   nvidia-smi

   # Should show model loaded in VRAM
   ```

2. **Use smaller model if OOM:**
   ```bash
   ollama pull qwen2.5-coder:14b
   # Use with: -m qwen2.5-coder:14b
   ```

3. **Close GPU-heavy apps:**
   - Close browser with many tabs
   - Close games
   - Close other AI tools

### Out of Memory

```bash
# Switch to smaller quantization
ollama pull qwen2.5-coder:7b

# Or use CPU (slower but works)
OLLAMA_DEVICE=cpu ollama run qwen2.5-coder:32b
```

## Next Steps

### 1. Integrate with Workflow

**Pre-commit hook:**
```bash
# .git/hooks/pre-commit
python scripts/ollama_code_assistant.py review src/ --batch --format json > .review.json
```

**CI/CD:**
```yaml
# .github/workflows/code-quality.yml
- name: Ollama Code Review
  run: python scripts/ollama_code_assistant.py review src/ --batch
```

### 2. Try More Models

```bash
# Multimodal (code + screenshots)
ollama pull qwen3-vl-32b-instruct

# Fast reasoning
ollama pull gpt-oss-20b

# Best for documentation
ollama pull codellama:34b
```

### 3. Batch Operations

```bash
# Review entire codebase
python scripts/ollama_code_assistant.py review src/ --batch --format json > quality_report.json

# Generate all missing docstrings
python scripts/ollama_code_assistant.py docstring src/app/ --batch

# Create tests for all modules
for file in src/app/*.py; do
    python scripts/ollama_code_assistant.py test "$file" -o tests/
done
```

### 4. Privacy-Sensitive Operations

```python
# Resume analysis (stays local)
from scripts.ollama_code_assistant import OllamaAssistant

assistant = OllamaAssistant("qwen2.5-coder:32b")

with open("data/resume.txt") as f:
    resume = f.read()

skills = assistant.query(
    f"Extract technical skills from: {resume}",
    system_prompt="List skills as comma-separated values"
)
print(skills)
```

## Performance Benchmarks

**On RTX 4070 Ti (12GB VRAM):**

| Task | Model | Time | Quality |
|------|-------|------|---------|
| Review 300-line file | qwen2.5-coder:32b | ~15s | Excellent |
| Generate docstrings | qwen2.5-coder:32b | ~20s | Very good |
| Create unit tests | deepseek-coder:33b | ~30s | Good |
| Refactoring analysis | qwen2.5-coder:32b | ~25s | Excellent |

**Batch processing (10 files):**
- Cold start (first file): ~30s
- Subsequent files: ~10s each
- Total for 10 files: ~2-3 minutes

## Resources

- **Full documentation**: [docs/OLLAMA_CODE_ASSISTANT.md](OLLAMA_CODE_ASSISTANT.md)
- **Example integrations**: [examples/ollama_examples.py](../examples/ollama_examples.py)
- **Ollama docs**: https://ollama.ai/docs
- **Model recommendations**: Based on KDNuggets Dec 2025 article

## Get Help

1. **Check logs**: Script outputs detailed logs
2. **Run examples**: `python examples/ollama_examples.py`
3. **Test Ollama directly**: `ollama run qwen2.5-coder:32b "test"`
4. **Check VRAM**: `nvidia-smi` (Windows/Linux)
5. **Verify model**: `ollama list`

## Summary

**5-Minute Setup:**
1. ✅ Install Ollama (2 min)
2. ✅ Pull qwen2.5-coder:32b (3 min)
3. ✅ Test with `ollama run ...`
4. ✅ Run first review: `python scripts/ollama_code_assistant.py review <file>`

**You now have:**
- Private, local AI coding assistant
- Unlimited queries (no API costs)
- Offline capability
- Batch processing for entire codebase
- Integration with job-lead-finder workflows

**Use for:**
- Code reviews (bug detection, security)
- Docstring generation
- Test creation
- Refactoring analysis
- Resume analysis (privacy)
- Email classification (privacy)
- Batch job description analysis

Enjoy your local AI coding assistant! 🚀
