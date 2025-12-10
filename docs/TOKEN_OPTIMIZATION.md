# Token Optimization Guide

**Goal:** Maximize free/local AI resources, minimize token usage from paid services (GitHub Copilot, Gemini, OpenAI).

## Token Usage Priority (Lowest to Highest Cost)

### 1. **Local Ollama** (FREE - Use for everything possible)
- **Cost:** $0
- **Quota:** Unlimited
- **Speed:** 5-30 seconds
- **Use for:**
  - ✅ Job resume matching and scoring
  - ✅ Code generation and refactoring
  - ✅ Writing tests
  - ✅ Code reviews (in PRs)
  - ✅ Bug fixing assistance
  - ✅ General coding questions

**Setup:**
```powershell
# One-time setup
python scripts/setup_ollama_models.py

# Verify running
docker compose ps | Select-String ollama
```

**Usage:**
```powershell
# Code generation
python tools/coding_assistant.py generate "Create a function to..."

# Job matching (already configured as default)
# Runs automatically when evaluating jobs
```

### 2. **Gemini Flash 2.0** (FREE tier available)
- **Cost:** Free tier: 15 requests/minute, 1500/day
- **Quota:** Limited but renewable daily
- **Speed:** 2-5 seconds
- **Use for:**
  - ✅ Complex code analysis when Ollama is slow
  - ✅ AI PR reviews (fallback if Ollama tunnel down)
  - ✅ Company career page searches
  - ✅ Cover letter generation

**Current Config:** Already set as fallback in AI PR reviews

### 3. **GitHub Copilot** (PAID - Save for interactive coding)
- **Cost:** $10/month or enterprise quota
- **Quota:** Limited monthly (you've used 25% in 9 days)
- **Speed:** Real-time
- **Use for:**
  - ✅ Line-by-line autocomplete in VS Code
  - ✅ Quick inline suggestions
  - ✅ Chat for complex architectural questions
  - **❌ Avoid for:** Bulk code generation, PR reviews, repetitive tasks

### 4. **OpenAI/Anthropic** (EXPENSIVE - Emergency only)
- **Cost:** $0.03-0.15 per request
- **Quota:** Pay-per-use
- **Use for:**
  - ⚠️ Last resort if all else fails
  - ⚠️ Production critical features only

## Optimization Checklist

### ✅ Already Configured

1. **Job Evaluation:** Uses Ollama first, Gemini fallback
   - File: `src/app/job_finder.py` (lines 28-51)
   - Priority: Ollama → Gemini → None

2. **AI PR Reviews:** Uses Gemini → OpenAI → Ollama → Skip
   - File: `.github/workflows/ai-pr-review.yml`
   - Triggers: Only on PR open/ready (not every push)
   - Skips: draft PRs, test commits, chore commits

3. **Local Coding Assistant:** Always uses Ollama (free)
   - Tool: `tools/coding_assistant.py`
   - Models: DeepSeek Coder, CodeLlama

### ⚠️ Needs Configuration

1. **Add OLLAMA_BASE_URL to GitHub Actions**
   - Currently missing from workflow environment
   - Prevents free Ollama reviews from working
   - **Fix required:** See "Missing Configuration" section below

2. **Configure .env file** (if not exists)
   - Create `.env` file with API priorities
   - See "Environment Setup" section below

3. **Update docker-compose.yml environment**
   - Ensure Ollama is default for all services
   - See "Docker Configuration" section below

## Missing Configuration (CRITICAL)

### Issue 1: Ollama URL not exposed to GitHub Actions

**Current:** `.github/workflows/ai-pr-review.yml` line 209:
```yaml
env:
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  # MISSING: OLLAMA_BASE_URL
```

**Fix:**
```yaml
env:
  OLLAMA_BASE_URL: ${{ secrets.OLLAMA_BASE_URL }}
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Impact:** Without this, AI PR reviews will NEVER use free Ollama - wasting Gemini quota!

### Issue 2: No .env file template

**Create `.env` file:**
```bash
# Token Optimization - Priority Order (Free → Paid)

# 1. LOCAL OLLAMA (FREE - highest priority)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b

# 2. GEMINI (FREE tier - fallback)
GEMINI_API_KEY=your_gemini_key_here
GOOGLE_API_KEY=${GEMINI_API_KEY}

# 3. GITHUB COPILOT (PAID - use sparingly)
GITHUB_TOKEN=your_github_token_here

# 4. EMERGENCY ONLY (EXPENSIVE)
OPENAI_API_KEY=sk-your-key-here  # Only for last resort
ANTHROPIC_API_KEY=sk-your-key-here  # Only for last resort

# Job Search APIs (use Ollama for evaluation)
RAPIDAPI_KEY=your_rapidapi_key_here  # JSearch company discovery

# Application Settings
USE_OLLAMA=true  # Force Ollama for job evaluation
PREFER_LOCAL_AI=true  # Prefer local over cloud APIs
```

## Environment Setup

### Step 1: Create .env file

```powershell
# Copy this content to .env
New-Item -Path .env -ItemType File -Force
```

Then add the configuration above.

### Step 2: Verify Ollama is running

```powershell
# Check Ollama container
docker compose ps ollama

# Check Ollama tunnel (for GitHub Actions)
docker compose ps ollama-tunnel

# Test Ollama locally
curl http://localhost:11434/api/tags
```

### Step 3: Verify models are downloaded

```powershell
# List models
ollama list
# Or via Docker
docker exec job-lead-finder-ollama-1 ollama list

# Expected:
# deepseek-coder:6.7b    3.8 GB
# codellama:7b           3.8 GB
# llama3.2:3b            2.0 GB
```

### Step 4: Test token optimization

```powershell
# Test job evaluation (should use Ollama)
python -c "from src.app.job_finder import _get_evaluation_provider; p = _get_evaluation_provider(); print(f'Provider: {type(p).__name__}')"
# Expected: "Provider: OllamaProvider"

# Test coding assistant
python tools/coding_assistant.py generate "Simple hello function"
# Should respond in 5-10 seconds with code
```

## Docker Configuration

Update `docker-compose.yml` to prioritize Ollama:

```yaml
services:
  app:
    environment:
      # Force Ollama priority
      - USE_OLLAMA=true
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=deepseek-coder:6.7b
      # Gemini as fallback only
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GOOGLE_API_KEY=${GEMINI_API_KEY}

  worker:
    environment:
      # Same priority for background jobs
      - USE_OLLAMA=true
      - OLLAMA_BASE_URL=http://ollama:11434
```

## Usage Recommendations

### For Daily Development

**Use Local Ollama for:**
- Generating boilerplate code
- Writing tests
- Refactoring functions
- Fixing simple bugs
- Code reviews

**Example workflow:**
```powershell
# 1. Generate initial code with Ollama
python tools/coding_assistant.py generate "Create a data validator class" -o src/app/validator.py

# 2. Refine with Copilot in VS Code
# Open file, use inline suggestions for details

# 3. Generate tests with Ollama
python tools/coding_assistant.py test src/app/validator.py -o tests/test_validator.py

# 4. Create PR (AI review uses Ollama via tunnel)
git checkout -b feature/validator
git commit -am "[AI] feat: Add data validator"
git push origin feature/validator
gh pr create
```

### For Job Searching

**Already optimized!** Job evaluation automatically uses:
1. Ollama (if available) - FREE
2. Gemini (if Ollama fails) - FREE tier
3. No evaluation (if both fail) - Shows unscored jobs

No action needed - just ensure Ollama is running.

### For Complex Architectural Questions

Use GitHub Copilot Chat for:
- System design discussions
- Architecture decisions
- Complex debugging
- Multi-file refactoring guidance

These are harder for local models and worth the token cost.

## Monitoring Token Usage

### GitHub Copilot

Check quota usage:
```powershell
# Your usage: 25% in 9 days (on track for 75% monthly)
# Goal: <50% monthly by using Ollama for bulk tasks
```

### Gemini

Monitor at: https://aistudio.google.com/app/apikey
- Free tier: 15 RPM, 1500 RPD
- Check usage daily
- Should be <100 requests/day with Ollama priority

### Ollama

Check performance:
```powershell
# Monitor resource usage
docker stats job-lead-finder-ollama-1

# Check generation times in logs
docker compose logs ollama | Select-String "generated"
```

## Troubleshooting

### Ollama not being used for job evaluation

**Check:**
```powershell
# 1. Is Ollama running?
docker compose ps ollama

# 2. Are models downloaded?
ollama list

# 3. Test provider selection
python -c "from src.app.job_finder import _get_evaluation_provider; print(type(_get_evaluation_provider()).__name__)"
```

**Expected:** `OllamaProvider`
**If not:** Run `python scripts/setup_ollama_models.py`

### AI PR reviews not using Ollama

**Check:**
1. Is `OLLAMA_BASE_URL` set as GitHub secret?
   ```powershell
   gh secret list | Select-String OLLAMA
   ```

2. Is ollama-tunnel running?
   ```powershell
   docker compose ps ollama-tunnel
   docker compose logs ollama-tunnel | Select-String https://
   ```

3. Is tunnel URL current in secret?
   ```powershell
   # Get current URL
   docker compose logs ollama-tunnel | Select-String "https://" | Select-Object -Last 1

   # Update if changed
   gh secret set OLLAMA_BASE_URL --body "https://your-new-url.trycloudflare.com"
   ```

### Copilot quota running low

**Reduce usage:**
1. Use Ollama for code generation: `python tools/coding_assistant.py generate "..."`
2. Use Ollama for refactoring: `python tools/coding_assistant.py refactor file.py`
3. Use Ollama for tests: `python tools/coding_assistant.py test file.py`
4. Reserve Copilot for inline completions and complex questions

**Expected savings:** 40-50% reduction in quota usage

## Cost Comparison

Monthly costs with different strategies:

| Strategy | Copilot | Gemini | OpenAI | Ollama | Total |
|----------|---------|--------|--------|--------|-------|
| **All Copilot** | $10 (quota used) | $0 | $0 | $0 | **$10** |
| **All Cloud APIs** | $10 | $0 (free) | $15 | $0 | **$25** |
| **Optimized (Recommended)** | $5 (50% quota) | $0 (free) | $0 | $0 | **$5** |
| **100% Local** | $0 (minimal) | $0 | $0 | $0 | **$0** |

**Recommended:** Optimized strategy
- Use Ollama for 80% of tasks
- Use Copilot for inline completions
- Use Gemini free tier for emergencies
- Save 50% on Copilot quota

## Action Items

### Immediate (Critical)

- [ ] Add `OLLAMA_BASE_URL` to AI PR review workflow environment
- [ ] Create `.env` file with priority configuration
- [ ] Verify Ollama is running and models downloaded
- [ ] Test job evaluation uses Ollama
- [ ] Test AI PR review can reach Ollama tunnel

### Short-term (This Week)

- [ ] Run `python scripts/setup_ollama_models.py` to ensure all models ready
- [ ] Create test PR to verify AI review uses Ollama
- [ ] Use coding assistant for next 5 code tasks instead of Copilot
- [ ] Monitor Copilot quota usage (should decrease)

### Long-term (This Month)

- [ ] Achieve <50% monthly Copilot quota usage
- [ ] Document personal workflow using Ollama
- [ ] Set up monitoring dashboard for token usage
- [ ] Create scripts to auto-switch based on quota

## Summary

**Current State:**
- ✅ Ollama configured for job evaluation
- ✅ Coding assistant ready to use
- ✅ Ollama tunnel running for GitHub Actions
- ⚠️ Missing: OLLAMA_BASE_URL in workflow environment
- ⚠️ Missing: .env file with clear priorities

**After Optimization:**
- 🎯 80% of AI tasks use free Ollama
- 🎯 15% use Gemini free tier
- 🎯 5% use Copilot for inline help
- 🎯 0% use paid APIs (OpenAI/Anthropic)
- 🎯 Save 50% on Copilot quota monthly
- 🎯 Hands get more rest while AI works 24/7!

---

**Next Steps:** Apply the fixes in "Missing Configuration" section, then create a PR to merge these optimizations.
