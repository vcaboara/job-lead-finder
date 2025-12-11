# Ollama Code Assistant

Local LLM-powered development tool leveraging Ollama for privacy-sensitive and batch operations.

## Why Local LLMs?

**Best Use Cases for Local Ollama:**
- **Privacy-sensitive operations**: Resume analysis, proprietary code review
- **Batch processing**: Analyze entire codebase without API rate limits
- **High-volume tasks**: Unlimited queries without burning API credits
- **Offline work**: No internet dependency
- **Experimentation**: Test prompts and workflows without costs

**Cloud LLMs remain better for:**
- Autonomous workflows (GitHub integration like @copilot)
- Complex multi-step reasoning
- Latest knowledge and models
- Large context windows (>128k tokens)

## Recommended Models

Based on KDNuggets "Top 5 Small AI Coding Models That You Can Run Locally" (Dec 2025):

### For 12GB VRAM (RTX 4070 Ti)

| Model | Size | Best For | Context |
|-------|------|----------|---------|
| **qwen2.5-coder:32b** | 21GB (Q4) | Code review, refactoring, bug detection | 32k |
| **deepseek-coder:33b** | 20GB (Q4) | Code generation, completion, boilerplate | 16k |
| **codellama:34b** | 21GB (Q4) | Explanation, documentation, teaching | 16k |

### Alternative Models

| Model | Size | Best For | VRAM |
|-------|------|----------|------|
| **gpt-oss-20b** | 12GB (Q4) | Fast local coding + reasoning | 8GB |
| **qwen3-vl-32b-instruct** | 22GB (Q4) | Coding + visual understanding (screenshots, diagrams) | 12GB |
| **apriel-1.5-15b-thinker** | 9GB (Q4) | Think-then-code workflows | 6GB |
| **seed-oss-36b-instruct** | 23GB (Q4) | High-accuracy repo-level coding | 14GB |

## Installation

### 1. Install Ollama

**Windows:**
```powershell
# Download from https://ollama.ai/download
winget install Ollama.Ollama
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Pull Recommended Models

```bash
# Best overall (recommended)
ollama pull qwen2.5-coder:32b

# Code generation specialist
ollama pull deepseek-coder:33b

# Documentation/explanation
ollama pull codellama:34b
```

### 3. Verify Installation

```bash
ollama list
# Should show downloaded models
```

## Usage

### Model Recommendation

```bash
# Get model recommendation for your hardware and task
python scripts/ollama_code_assistant.py recommend "code review" --vram 12
# Output: Recommended model: qwen2.5-coder:32b
```

### Code Review

**Single file:**
```bash
python scripts/ollama_code_assistant.py review src/app/job_finder.py
```

**Batch review (entire directory):**
```bash
python scripts/ollama_code_assistant.py review src/app/ --batch --format json > code_review.json
```

**With specific model:**
```bash
python scripts/ollama_code_assistant.py review src/app/email_processor.py -m deepseek-coder:33b
```

### Generate Docstrings

**Single file (print to stdout):**
```bash
python scripts/ollama_code_assistant.py docstring src/app/job_tracker.py > src/app/job_tracker_documented.py
```

**Batch generation (creates *_documented.py files):**
```bash
python scripts/ollama_code_assistant.py docstring src/app/ --batch
```

### Generate Tests

**Generate pytest tests for module:**
```bash
python scripts/ollama_code_assistant.py test src/app/email_processor.py -o tests/
# Creates: tests/test_email_processor.py
```

**Specify model:**
```bash
python scripts/ollama_code_assistant.py test src/app/job_finder.py -o tests/ -m qwen2.5-coder:32b
```

### Refactoring Analysis

**Analyze code smells and refactoring opportunities:**
```bash
python scripts/ollama_code_assistant.py refactor src/app/ui_server.py --format json
```

**Output includes:**
- Code smells (long methods, complex conditionals, duplication)
- Refactoring suggestions (extract method, introduce parameter object)
- Design pattern recommendations
- Effort estimates (low/medium/high)

## Example Workflows

### 1. New Feature Development

```bash
# 1. Generate tests for new module
python scripts/ollama_code_assistant.py test src/app/new_feature.py -o tests/

# 2. Review implementation
python scripts/ollama_code_assistant.py review src/app/new_feature.py --format json

# 3. Add missing docstrings
python scripts/ollama_code_assistant.py docstring src/app/new_feature.py > src/app/new_feature_v2.py
```

### 2. Legacy Code Cleanup

```bash
# 1. Identify refactoring opportunities
python scripts/ollama_code_assistant.py refactor src/app/legacy_module.py --format json > refactor_plan.json

# 2. Generate comprehensive docstrings
python scripts/ollama_code_assistant.py docstring src/app/ --batch

# 3. Create test coverage
for file in src/app/*.py; do
    python scripts/ollama_code_assistant.py test "$file" -o tests/
done
```

### 3. Privacy-Sensitive Resume Analysis

```bash
# Analyze resume content locally (no cloud upload)
python scripts/ollama_code_assistant.py review data/resume.txt -m qwen2.5-coder:32b

# Generate job matching logic
# (Create custom prompt for resume -> job matching)
```

### 4. Batch Code Quality Report

```bash
# Review entire codebase
python scripts/ollama_code_assistant.py review src/ --batch --format json > quality_report.json

# Parse results
python -c "
import json
with open('quality_report.json') as f:
    data = json.load(f)
    high_severity = sum(1 for file in data.values()
                       if file.get('severity') == 'high')
    print(f'High severity issues: {high_severity}')
"
```

## Performance Tips

### 1. Model Selection by Task

```bash
# Fast feedback (code review, bug detection)
-m qwen2.5-coder:32b

# Code generation (boilerplate, implementation)
-m deepseek-coder:33b

# Documentation (explanations, teaching)
-m codellama:34b
```

### 2. Batch Processing

For multiple files, use batch mode to reuse model in memory:
```bash
# Inefficient (loads model for each file)
for file in src/app/*.py; do
    python scripts/ollama_code_assistant.py review "$file"
done

# Efficient (single model load)
python scripts/ollama_code_assistant.py review src/app/ --batch
```

### 3. Hardware Optimization

**12GB VRAM (RTX 4070 Ti):**
- Use Q4 quantization for 32-34B models
- Avoid concurrent model runs
- Close GPU-intensive apps during inference

**8GB VRAM:**
- Use 7B-13B models (qwen2.5-coder:7b, codellama:13b)
- Q4 quantization mandatory

**4GB VRAM:**
- Use smallest models (phi-3:3b, qwen2.5-coder:1.5b)
- CPU inference may be faster

### 4. Context Window Limits

| Model | Context | Best For |
|-------|---------|----------|
| qwen2.5-coder:32b | 32k tokens | Large files (up to ~2000 lines) |
| deepseek-coder:33b | 16k tokens | Medium files (~1000 lines) |
| codellama:34b | 16k tokens | Medium files (~1000 lines) |

For files exceeding context, split into chunks or use cloud LLMs.

## Troubleshooting

### "Ollama not installed or not running"

**Windows:**
```powershell
# Check if Ollama service is running
Get-Service -Name "Ollama" | Select-Object Status

# Start service
Start-Service "Ollama"
```

**Linux/Mac:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama server
ollama serve
```

### "Model not found. Pulling..."

Script auto-pulls missing models. If it fails:
```bash
# Manually pull model
ollama pull qwen2.5-coder:32b

# Check available models
ollama list
```

### Query Timeout (5 min)

For very large files or complex tasks:
1. **Split file**: Break into smaller chunks
2. **Use faster model**: Switch to 7B/13B variant
3. **Increase timeout**: Edit script line 106 (timeout=300 -> timeout=600)

### Out of Memory (OOM)

```bash
# Check model size
ollama show qwen2.5-coder:32b

# Switch to smaller quantization
ollama pull qwen2.5-coder:7b  # 4.5GB vs 21GB

# Or use CPU inference (slower but no VRAM limit)
OLLAMA_DEVICE=cpu ollama run qwen2.5-coder:32b
```

## Integration with Job-Lead-Finder

### Privacy-Sensitive Operations

```python
# Resume analysis (never sent to cloud)
from scripts.ollama_code_assistant import OllamaAssistant

assistant = OllamaAssistant("qwen2.5-coder:32b")
with open("data/resume.txt") as f:
    resume = f.read()

analysis = assistant.query(
    f"Extract skills and experience from resume:\n{resume}",
    system_prompt="You are a resume analysis expert. Extract technical skills, years of experience, and key achievements."
)
```

### Batch Job Description Analysis

```python
# Analyze all saved job postings offline
import json
from pathlib import Path
from scripts.ollama_code_assistant import OllamaAssistant

assistant = OllamaAssistant("qwen2.5-coder:32b")

with open("data/leads.json") as f:
    jobs = json.load(f)

for job in jobs:
    if job.get("description"):
        analysis = assistant.query(
            f"Extract required skills: {job['description'][:2000]}",
            system_prompt="List technical skills required for this job."
        )
        job["extracted_skills"] = analysis.split(", ")
```

### Offline Code Review (CI/CD)

```bash
# Add to pre-commit hook
#!/bin/bash
# .git/hooks/pre-commit

echo "Running Ollama code review..."
python scripts/ollama_code_assistant.py review src/ --batch --format json > .code_review.json

# Parse and fail if high severity issues
high_severity=$(python -c "
import json
with open('.code_review.json') as f:
    data = json.load(f)
    print(sum(1 for file in data.values() if file.get('severity') == 'high'))
")

if [ "$high_severity" -gt 0 ]; then
    echo "❌ Found $high_severity high severity issues. Commit blocked."
    exit 1
fi

echo "✅ Code review passed"
```

## Comparison: Ollama vs Cloud LLMs

| Feature | Ollama (Local) | GitHub Copilot / Cloud |
|---------|----------------|------------------------|
| **Privacy** | ✅ Complete | ⚠️ Data sent to cloud |
| **Cost** | ✅ Free (hardware only) | ⚠️ API costs / subscription |
| **Offline** | ✅ Full functionality | ❌ Requires internet |
| **Speed** | ⚠️ Depends on hardware | ✅ Fast (cloud GPUs) |
| **Context** | ⚠️ 16k-32k tokens | ✅ 128k-1M tokens |
| **Autonomy** | ❌ CLI only | ✅ GitHub integration (@copilot) |
| **Batch ops** | ✅ Unlimited queries | ⚠️ Rate limits |
| **Latest models** | ⚠️ Community releases | ✅ Cutting-edge |

**Best Practice:** Use both strategically:
- **Local**: Privacy-sensitive code, batch processing, offline work, experimentation
- **Cloud**: Autonomous workflows, complex reasoning, large context needs

## References

- [KDNuggets: Top 5 Small AI Coding Models](https://www.kdnuggets.com/top-5-small-ai-coding-models-that-you-can-run-locally)
- [Ollama Documentation](https://ollama.ai/docs)
- [Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct)
- [DeepSeek-Coder](https://huggingface.co/deepseek-ai/deepseek-coder-33b-instruct)
- [CodeLlama](https://huggingface.co/codellama/CodeLlama-34b-Instruct-hf)

## License

Part of job-lead-finder project. See main LICENSE file.
