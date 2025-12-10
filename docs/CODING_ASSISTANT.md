# Local Coding Assistant with Ollama

This guide explains how to use local LLM models for code generation, refactoring, bug fixing, and testing - all running locally with **zero API costs**.

## Overview

The coding assistant uses Ollama to run specialized code models locally:
- **DeepSeek Coder 6.7B**: Optimized for code generation and understanding
- **CodeLlama 7B**: Meta's code-specific LLaMA model
- **Zero cost**: No API keys, no quotas, completely free
- **Privacy**: Your code never leaves your machine

## Quick Start

### 1. Setup (One-Time)

Run the automated setup script to download and verify models:

```powershell
# Setup all recommended models (DeepSeek Coder + CodeLlama)
python scripts/setup_ollama_models.py

# Or setup only what you need
python scripts/setup_ollama_models.py --coding-only
python scripts/setup_ollama_models.py --reviews-only
```

The script will:
- ✅ Check Ollama is running
- ✅ Download required models (3.8 GB each)
- ✅ Verify models work correctly
- ✅ Show clear error messages if anything fails

**First time?** The download takes 5-10 minutes per model depending on your internet speed. Grab a coffee! ☕

### 2. Verify Setup

Check that models are ready:

```powershell
# List installed models
ollama list

# Or via Docker
docker exec job-lead-finder-ollama-1 ollama list
```

You should see:
```
NAME                    SIZE
deepseek-coder:6.7b    3.8 GB
codellama:7b           3.8 GB
llama3.2:3b            2.0 GB
```

## Usage

### Generate Code

Create new functions, classes, or scripts from natural language:

```powershell
# Generate a function
python tools/coding_assistant.py generate "Create a function to parse CSV files with error handling"

# Generate a class
python tools/coding_assistant.py generate "Create a User class with email validation and password hashing"

# Save to file
python tools/coding_assistant.py generate "Parse JSON config file" -o src/app/config_parser.py
```

**Output includes:**
- Type hints
- Docstrings
- Error handling
- PEP 8 compliant code

### Refactor Code

Improve existing code for better quality:

```powershell
# Refactor a file
python tools/coding_assistant.py refactor src/app/job_finder.py

# Save refactored version
python tools/coding_assistant.py refactor src/app/utils.py -o src/app/utils_refactored.py
```

**Improvements include:**
- Better variable names
- Extracted helper functions
- Reduced complexity
- Performance optimizations
- Better error handling

### Fix Bugs

Debug errors with AI assistance:

```powershell
# Fix based on error message
python tools/coding_assistant.py fix "AttributeError: 'NoneType' object has no attribute 'get'"

# Fix with code context
python tools/coding_assistant.py fix "KeyError: 'email'" src/app/config.py

# Fix with full traceback
python tools/coding_assistant.py fix "$(cat error.log)" src/app/main.py
```

**AI provides:**
1. Root cause analysis
2. Fixed code
3. Prevention tips

### Write Tests

Generate comprehensive pytest tests:

```powershell
# Generate tests for a file
python tools/coding_assistant.py test src/app/utils.py

# Save tests
python tools/coding_assistant.py test src/app/parser.py -o tests/test_parser.py
```

**Tests include:**
- Happy path cases
- Edge cases
- Error handling tests
- Fixtures and parametrize
- Mock external dependencies

### Review Code

Get detailed code review feedback:

```powershell
# Review a file
python tools/coding_assistant.py review src/app/main.py

# Review before committing
python tools/coding_assistant.py review $(git diff --name-only --cached)
```

**Review covers:**
- Potential bugs
- Performance issues
- Security vulnerabilities
- Best practices
- Code style

## Advanced Usage

### Custom Models

Use different models for specific tasks:

```powershell
# Use CodeLlama for generation
python tools/coding_assistant.py generate "..." --model codellama:7b

# Use smaller model for quick tasks
python tools/coding_assistant.py review file.py --model llama3.2:3b
```

**Model recommendations:**
- `deepseek-coder:6.7b` - Best for code generation (default)
- `codellama:7b` - Good for refactoring and reviews
- `llama3.2:3b` - Faster but less capable

### Batch Processing

Process multiple files:

```powershell
# Refactor all Python files in a directory
Get-ChildItem src/app/*.py | ForEach-Object {
    python tools/coding_assistant.py refactor $_.FullName -o "refactored/$($_.Name)"
}

# Generate tests for all source files
Get-ChildItem src/app/*.py | ForEach-Object {
    $testFile = "tests/test_$($_.Name)"
    python tools/coding_assistant.py test $_.FullName -o $testFile
}
```

### Integration with Git

Use in your development workflow:

```powershell
# Review changed files before committing
git diff --name-only | Where-Object { $_ -match '\.py$' } | ForEach-Object {
    python tools/coding_assistant.py review $_
}

# Generate tests for new files
git diff --name-only --diff-filter=A | Where-Object { $_ -match '\.py$' } | ForEach-Object {
    python tools/coding_assistant.py test $_ -o "tests/test_$(Split-Path $_ -Leaf)"
}
```

## Troubleshooting

### Ollama Not Running

**Error:** `Cannot connect to Ollama server`

**Solution:**
```powershell
# Check if Ollama container is running
docker compose ps

# Start Ollama
docker compose up -d ollama

# Or start all services
docker compose up -d
```

### Model Not Found

**Error:** `Model deepseek-coder:6.7b not found`

**Solution:**
```powershell
# Run setup script
python scripts/setup_ollama_models.py

# Or manually pull the model
ollama pull deepseek-coder:6.7b
# Or via Docker
docker exec job-lead-finder-ollama-1 ollama pull deepseek-coder:6.7b
```

### Slow Generation

**Issue:** Code generation takes too long

**Solutions:**
1. **Use smaller model:** `--model llama3.2:3b` (faster, less capable)
2. **Increase timeout:** Models need time for complex code
3. **Simplify prompt:** Break complex requests into smaller tasks
4. **Check resources:** Ensure Docker has enough RAM (8GB+ recommended)

### Quality Issues

**Issue:** Generated code is not good enough

**Solutions:**
1. **Be more specific:** Add details to your prompt
2. **Try different model:** `--model codellama:7b` may work better for some tasks
3. **Iterate:** Use the output as a starting point and refine
4. **Provide context:** For fixes/refactors, include the actual code

### Out of Memory

**Error:** Ollama crashes or generation fails

**Solution:**
```powershell
# Check Docker resource limits
docker stats

# Increase Docker Desktop memory:
# Settings > Resources > Memory > Increase to 8GB+

# Or use smaller model
python tools/coding_assistant.py generate "..." --model llama3.2:3b
```

## Best Practices

### 1. Start Small

Don't try to generate entire applications. Start with:
- Individual functions
- Small classes
- Utility modules
- Test cases

### 2. Review and Refine

AI-generated code is a **starting point**, not a finished product:
- ✅ Review for correctness
- ✅ Test thoroughly
- ✅ Refine as needed
- ✅ Add project-specific details

### 3. Use for Boilerplate

Best use cases:
- ✅ CRUD operations
- ✅ Data parsing
- ✅ Test scaffolding
- ✅ Configuration handling
- ✅ API clients

### 4. Iterate

If the first result isn't perfect:
1. Refine your prompt with more details
2. Try a different model
3. Generate multiple versions and combine the best parts
4. Use the output as a base and manually improve

### 5. Combine with Other Tools

The coding assistant works great with:
- **GitHub Copilot** - Use for line completions, Ollama for larger chunks
- **AI PR Reviews** - Generate code locally, review in PRs
- **Black/isort** - Auto-format AI-generated code
- **pytest** - Test AI-generated functions

## Cost Comparison

| Service | Cost per Request | Monthly Cost (100 requests) |
|---------|------------------|------------------------------|
| **Ollama (Local)** | $0.00 | $0.00 |
| GitHub Copilot | Quota-based | ~$10 (quota usage) |
| OpenAI GPT-4 | $0.03 | $3.00 |
| Claude 3.5 | $0.015 | $1.50 |

**Ollama is completely free** - no quotas, no limits, no API keys!

## Performance

Typical generation times on modern hardware:

| Task | DeepSeek Coder 6.7B | CodeLlama 7B | Llama3.2 3B |
|------|---------------------|--------------|-------------|
| Simple function | 5-10s | 5-10s | 3-5s |
| Complex class | 15-30s | 15-30s | 10-15s |
| Test suite | 30-60s | 30-60s | 20-30s |
| Code review | 20-40s | 20-40s | 15-25s |

**Hardware requirements:**
- **Minimum:** 8GB RAM, 4 CPU cores
- **Recommended:** 16GB RAM, 8 CPU cores
- **GPU:** Optional but significantly faster with NVIDIA GPU + CUDA

## Examples

### Example 1: Generate a Data Parser

```powershell
python tools/coding_assistant.py generate "Create a function to parse YAML configuration files with validation"
```

**Output:**
```python
from pathlib import Path
from typing import Any, Dict
import yaml

def parse_config(file_path: str) -> Dict[str, Any]:
    """Parse and validate YAML configuration file.

    Args:
        file_path: Path to YAML config file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        ValueError: If required keys are missing
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML: {e}")

    if not isinstance(config, dict):
        raise ValueError("Config must be a dictionary")

    return config
```

### Example 2: Fix a Bug

```powershell
python tools/coding_assistant.py fix "TypeError: 'NoneType' object is not subscriptable" src/app/parser.py
```

**Output:**
```
Root Cause:
The error occurs when trying to access an index/key on a None object.
This typically happens when a function returns None instead of expected data.

Fixed Code:
# Before
result = get_data()
value = result['key']  # Fails if result is None

# After
result = get_data()
if result is not None:
    value = result.get('key', default_value)
else:
    # Handle None case
    value = default_value

Prevention:
1. Always check for None before accessing attributes
2. Use .get() method for dictionaries (returns None instead of raising KeyError)
3. Add type hints to catch issues early
4. Validate function returns
```

## Next Steps

1. **Run setup:** `python scripts/setup_ollama_models.py`
2. **Try examples:** Start with simple code generation
3. **Integrate into workflow:** Use for boilerplate, tests, reviews
4. **Compare with Copilot:** Find the right balance for your needs

## Related Docs

- [Ollama Tunnel Setup](OLLAMA_TUNNEL_SETUP.md) - For AI PR reviews
- [PR Review Criteria](../rules_template/01-rules/02-pr-review-criteria.md) - What to look for in code reviews
- [Contributing](../README.md) - Development workflow

---

**Questions?** Open an issue or check the [Ollama documentation](https://ollama.ai/docs).
