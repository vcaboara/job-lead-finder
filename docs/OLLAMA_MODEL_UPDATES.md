# Ollama Model Updates - Maintenance Guide

## Do Models Need Updates?

**Yes!** Ollama models get regular updates:

### What Gets Updated

1. **Quantization Improvements**
   - Better Q4/Q5/Q8 quantizations (smaller size, same quality)
   - Performance optimizations
   - Memory usage improvements

2. **Bug Fixes**
   - Tokenization issues
   - Context handling bugs
   - Compatibility fixes

3. **New Model Versions**
   - Fine-tuned variants (e.g., qwen2.5-coder:32b-v2)
   - Better training data
   - Improved accuracy

4. **Security Patches**
   - Vulnerability fixes
   - Safety improvements

## How to Check for Updates

### Check Model Age

```bash
# List all models with modification dates
ollama list

# Output shows:
# NAME                   ID              SIZE      MODIFIED
# qwen2.5-coder:32b      a1b2c3d4...    21 GB     3 weeks ago
# deepseek-coder:33b     e5f6g7h8...    20 GB     2 months ago
```

**Rule of Thumb:**
- Models older than 3 months → Check for updates
- Models older than 6 months → Definitely update

### Check Ollama Version

```bash
# Check Ollama CLI version
ollama --version

# Output: ollama version is 0.13.2
```

**Update Ollama:**
```powershell
# Windows (winget)
winget upgrade Ollama.Ollama

# Or download from https://ollama.ai/download
```

```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh
```

### Check for New Model Versions

```bash
# Search for model on Ollama website
# https://ollama.ai/library/qwen2.5-coder

# Look for:
# - New tags (e.g., :32b-v2, :32b-instruct-q5)
# - Recent updates (check "Last updated" date)
# - Release notes
```

## How to Update Models

### Option 1: Pull Latest Version

```bash
# Pull latest version of specific model
ollama pull qwen2.5-coder:32b

# Ollama will:
# 1. Check if newer version exists
# 2. Download only if updated
# 3. Replace old version
```

**Note:** If no update available, you'll see:
```
✓ qwen2.5-coder:32b is already up to date
```

### Option 2: Pull Specific Tag

```bash
# Pull specific quantization
ollama pull qwen2.5-coder:32b-q5  # Higher quality (larger size)
ollama pull qwen2.5-coder:32b-q4  # Smaller size (faster)

# Pull by date/version
ollama pull qwen2.5-coder:32b-2024-12  # December 2024 version
```

### Option 3: Remove and Re-pull

```bash
# Remove old model
ollama rm qwen2.5-coder:32b

# Pull fresh copy
ollama pull qwen2.5-coder:32b
```

**Use when:**
- Corrupted model
- Disk space issues
- Major version change

## Update Schedule

### Recommended Maintenance

| Frequency | Action | Reason |
|-----------|--------|--------|
| **Weekly** | Check Ollama version | CLI improvements |
| **Monthly** | Check model updates | Bug fixes, improvements |
| **Quarterly** | Update all models | Major improvements |
| **Before major work** | Update relevant model | Best performance |

### Example Monthly Routine

```bash
# 1. Check Ollama version
ollama --version

# 2. List current models
ollama list

# 3. Update Ollama if needed
winget upgrade Ollama.Ollama  # Windows
# or
curl -fsSL https://ollama.ai/install.sh | sh  # Linux/Mac

# 4. Update key models
ollama pull qwen2.5-coder:32b
ollama pull deepseek-coder:33b
ollama pull codellama:34b

# 5. Verify updates
ollama list  # Check new MODIFIED dates
```

## What to Watch For

### Official Announcements

**Ollama Blog**: https://ollama.ai/blog
- New model releases
- Performance improvements
- Breaking changes

**Model Provider Blogs:**
- Qwen: https://qwenlm.github.io/blog/
- DeepSeek: https://www.deepseek.com/
- Meta (CodeLlama): https://ai.meta.com/blog/

### GitHub Releases

**Ollama GitHub**: https://github.com/ollama/ollama/releases
- CLI updates
- New features
- Bug fixes

### Community Discussions

**Reddit r/ollama**: https://reddit.com/r/ollama
- User experiences
- Performance comparisons
- Tips and tricks

## Upgrade Considerations

### Breaking Changes

Sometimes updates include breaking changes:

1. **API Changes**
   - Command syntax changes
   - Parameter updates
   - Output format changes

2. **Model Format Changes**
   - Requires re-download
   - Old models incompatible
   - Disk space needed for both

3. **Performance Changes**
   - Slower/faster inference
   - Different memory usage
   - Quality trade-offs

**Mitigation:**
- Test updates on non-critical work first
- Keep old version until verified
- Read release notes carefully

### Disk Space Management

Models take significant space:

```bash
# Check current usage
ollama list

# Calculate total
# qwen2.5-coder:32b: 21 GB
# deepseek-coder:33b: 20 GB
# codellama:34b: 21 GB
# Total: ~62 GB
```

**Before updating:**
```bash
# Check available space
Get-PSDrive C | Select-Object Used,Free  # Windows
df -h /  # Linux/Mac

# Clean up old models
ollama rm old-model:version
```

## Automation

### Update Script

Create `scripts/update_ollama_models.ps1`:

```powershell
#!/usr/bin/env pwsh
# Update all Ollama models used by job-lead-finder

Write-Host "Updating Ollama models..." -ForegroundColor Cyan

# Models to update
$models = @(
    "qwen2.5-coder:32b",
    "deepseek-coder:33b",
    "codellama:34b"
)

foreach ($model in $models) {
    Write-Host "Updating $model..." -ForegroundColor Yellow
    ollama pull $model

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $model updated successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ $model update failed" -ForegroundColor Red
    }
}

Write-Host "`nCurrent models:" -ForegroundColor Cyan
ollama list
```

**Run monthly:**
```powershell
pwsh scripts/update_ollama_models.ps1
```

### Check Script

Create `scripts/check_ollama_updates.py`:

```python
#!/usr/bin/env python3
"""Check if Ollama models need updates"""

import subprocess
import json
from datetime import datetime, timedelta

def check_model_age():
    """Check age of installed models"""
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Ollama not running")
        return

    lines = result.stdout.strip().split("\n")[1:]  # Skip header

    print("Model Update Check:")
    print("-" * 60)

    for line in lines:
        parts = line.split()
        name = parts[0]
        modified = " ".join(parts[-2:])  # "X days/weeks ago"

        # Parse age
        if "week" in modified or "month" in modified:
            status = "⚠️ Consider updating"
        elif "day" in modified:
            status = "✅ Up to date"
        else:
            status = "❓ Check manually"

        print(f"{status} {name:30} (modified: {modified})")

if __name__ == "__main__":
    check_model_age()
```

**Run weekly:**
```bash
python scripts/check_ollama_updates.py
```

## Best Practices

### ✅ Do

1. **Update Ollama CLI regularly** (monthly)
2. **Check model updates** before major projects
3. **Read release notes** before updating
4. **Test updates** on small tasks first
5. **Keep disk space** for updates (30-40GB free)
6. **Update one model at a time** to isolate issues

### ❌ Don't

1. **Auto-update during work** (might break workflow)
2. **Delete old model immediately** (test new one first)
3. **Update all models at once** (disk space issues)
4. **Ignore release notes** (breaking changes)
5. **Update right before deadline** (stability risk)

## Troubleshooting Updates

### Update Fails

```bash
# Error: "failed to pull model"

# Solutions:
1. Check internet connection
2. Check disk space (need 2x model size)
3. Try again (network issues)
4. Check Ollama version (outdated CLI)
```

### Model Corrupted After Update

```bash
# Remove corrupted model
ollama rm qwen2.5-coder:32b

# Re-pull
ollama pull qwen2.5-coder:32b
```

### Performance Regression

```bash
# Roll back to previous version
ollama rm qwen2.5-coder:32b
ollama pull qwen2.5-coder:32b-v1  # Specific old version

# Or use different quantization
ollama pull qwen2.5-coder:32b-q5  # Higher quality
```

### Disk Space Issues

```bash
# Check usage
ollama list

# Remove unused models
ollama rm llama3.2:3b  # Small models you don't use

# Clean Docker (if using)
docker system prune -a

# Move Ollama data (advanced)
# Edit Ollama config to use different disk
```

## Version Tracking

### Document Current Versions

Add to `docs/TECHNICAL.md`:

```markdown
## Ollama Models (Last Updated: 2025-12-10)

| Model | Version | Size | Purpose |
|-------|---------|------|---------|
| qwen2.5-coder:32b | Q4 | 21GB | Code review |
| deepseek-coder:33b | Q4 | 20GB | Code generation |
| codellama:34b | Q4 | 21GB | Documentation |

Last checked: 2025-12-10
Next check: 2026-01-10
```

### Git Track Updates

```bash
# After updating models
git commit -m "docs: Update Ollama model versions (2025-12-10)"
```

## Summary

**Key Points:**
- ✅ Models DO get updates (monthly/quarterly)
- ✅ Check for updates monthly
- ✅ Update Ollama CLI regularly
- ✅ Read release notes before updating
- ✅ Test updates before production use
- ✅ Keep 30-40GB free for updates

**Quick Update:**
```bash
# Monthly maintenance (5 minutes)
ollama --version                    # Check CLI
ollama pull qwen2.5-coder:32b       # Update models
ollama pull deepseek-coder:33b
ollama pull codellama:34b
ollama list                         # Verify updates
```

**Stay Informed:**
- Ollama blog: https://ollama.ai/blog
- GitHub releases: https://github.com/ollama/ollama/releases
- Weekly check: `python scripts/check_ollama_updates.py`

Your models are tools - keep them sharp! 🔧
