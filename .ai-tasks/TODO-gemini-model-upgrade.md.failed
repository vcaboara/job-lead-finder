# TODO: Upgrade to Latest Gemini Models

## Current Status
- **Using:** `gemini-2.0-flash-exp` (now "Previous generation")
- **Available:** Gemini 3 Pro, 2.5 Flash, 2.5 Flash-Lite, 2.5 Pro
- **Source:** https://ai.google.dev/gemini-api/docs/models (Updated Dec 10, 2025)

## Recommended Upgrades

### Option 1: Gemini 2.5 Flash (RECOMMENDED)
- **Model:** `gemini-2.5-flash`
- **Why:** Best price-performance, designed for agentic use cases
- **Use for:** Current AI PR reviews, LLM API tool, general tasks
- **Cost:** Lower than 2.0 Flash
- **Speed:** Similar to 2.0 Flash

### Option 2: Gemini 3 Pro
- **Model:** `gemini-3-pro-preview`
- **Why:** Most intelligent, best for complex reasoning
- **Use for:** Architecture design, complex debugging, planning
- **Cost:** Higher (premium tier)
- **Speed:** Slower but more capable

### Option 3: Gemini 2.5 Flash-Lite
- **Model:** `gemini-2.5-flash-lite`
- **Why:** Fastest, most cost-efficient
- **Use for:** High-volume simple tasks, quick checks
- **Cost:** Lowest
- **Speed:** Fastest

## Implementation Plan

### Phase 1: Update Default Models (15 min)
- [ ] Update `tools/llm_api.py`: Change default from `gemini-2.0-flash-exp` → `gemini-2.5-flash`
- [ ] Update `.github/workflows/ai-pr-review.yml`: Use `gemini-2.5-flash`
- [ ] Update docs mentioning Gemini 2.0 Flash → 2.5 Flash

### Phase 2: Test New Models (30 min)
- [ ] Test `gemini-2.5-flash` with LLM API tool
- [ ] Test AI PR review workflow with new model
- [ ] Compare response quality and speed
- [ ] Monitor API costs

### Phase 3: Advanced Usage (Optional - 1 hour)
- [ ] Add Gemini 3 Pro option for complex tasks
- [ ] Use 2.5 Flash-Lite for high-volume operations
- [ ] Create model selection strategy based on task complexity
- [ ] Document model usage guidelines

## Files to Update

```
tools/llm_api.py (line 170)
.github/workflows/ai-pr-review.yml (line 197)
docs/COPILOT_WORKFLOW.md (mentions Gemini Flash 2.0)
docs/OLLAMA_TUNNEL_SETUP.md (mentions Gemini Flash 2.0)
docs/TOKEN_OPTIMIZATION.md (mentions Gemini Flash 2.0)
```

## Benefits
✅ Latest model capabilities (thinking, agentic features)
✅ Better price-performance
✅ Future-proof (2.0 Flash is now "previous generation")
✅ Access to Gemini 3 Pro for advanced tasks

## Risks
⚠️ API changes (test thoroughly)
⚠️ Pricing changes (monitor costs)
⚠️ Different response formats (validate outputs)

## Decision
**UPGRADE TO 2.5 FLASH** - It's designed for exactly our use case (agentic, large scale processing)
