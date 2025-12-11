# AI Search-Match Framework - Extraction Plan

**Framework Name:** `ai-search-match-framework`

**Goal:** Extract reusable AI-powered search, match, and tracking infrastructure from job-lead-finder into a standalone framework that can be used for:
- Job lead generation
- IP commercialization
- Customer prospecting
- Market research
- Any "search entities → match against criteria → track results" workflow

## What to Extract

### Core Infrastructure (Reusable)

**1. AI Orchestration**
- `src/app/mcp_providers.py` - Multi-provider LLM fallback system
- `src/app/ollama_provider.py` - Local LLM integration
- `src/app/gemini_provider.py` - Gemini API wrapper
- `scripts/ollama_code_assistant.py` - Code generation assistant
- `tools/llm_api.py` - Universal LLM API with multiple providers

**2. Search & Discovery**
- `tools/search_engine.py` - Google search wrapper
- `tools/web_scraper.py` - Concurrent web scraping
- `src/app/link_finder.py` - Career page discovery (adapt for company discovery)
- `src/app/link_validator.py` - URL validation and classification

**3. Docker Infrastructure**
- `docker-compose.yml` - Multi-service orchestration
- MCP server configurations (vibe-check, brave-search, fetch)
- `Dockerfile` - Base Python app container
- `.github/workflows/` - CI/CD and AI review automation

**4. UI Framework**
- `src/app/ui_server.py` - Flask API server
- `src/app/templates/*.html` - Modern dark mode UI (consolidate nav/dashboard)
- Background job processing with Celery
- Real-time progress tracking

**5. Configuration Management**
- `src/app/config_manager.py` - JSON config with validation
- `.env` template with API key management
- `pyproject.toml` - Python dependencies and project metadata

**6. AI Resource Monitoring**
- Token usage tracking across providers
- Cost optimization (Ollama → Gemini → OpenAI priority)
- `docs/TOKEN_OPTIMIZATION.md` principles

### Domain-Specific (Adapt/Replace)

**Job-specific (Remove/Adapt):**
- `src/app/job_finder.py` → Replace with `company_finder.py`
- `src/app/job_tracker.py` → Replace with `lead_tracker.py`
- `data/resume.txt` → Replace with `data/ip_portfolio.txt` or similar
- Job board providers → Replace with company discovery sources

## Extraction Options

### Option 1: Template Repository (Recommended)

Create `ai-lead-generator-framework` as a GitHub template:

**Structure:**
```
ai-lead-generator-framework/
├── core/                    # Reusable infrastructure
│   ├── ai/                 # LLM providers
│   ├── search/             # Search & scraping
│   ├── ui/                 # Web UI framework
│   └── config/             # Configuration management
├── docker-compose.yml      # MCP services
├── pyproject.toml          # Dependencies
├── .github/                # CI/CD workflows
└── examples/
    ├── job-lead-finder/    # This repo as example
    └── ip-commercialization/  # New use case
```

**Benefits:**
- Click "Use this template" to create new repos
- Keep improvements synced via git
- Clear separation of framework vs domain logic
- Easy to maintain multiple lead gen projects

### Option 2: Python Package

Publish `ai-lead-generator` to PyPI:

```python
# In new repo
pip install ai-lead-generator

from ai_lead_generator import SearchEngine, LLMProvider, LeadTracker
```

**Benefits:**
- Version control for framework
- Installable dependency
- Professional distribution

**Drawbacks:**
- More setup overhead
- Docker configs still need copying

### Option 3: Git Submodule

Keep framework in separate repo, include as submodule:

```bash
git submodule add https://github.com/vcaboara/ai-lead-framework core/
```

**Drawbacks:**
- Submodule complexity (as seen with vibe-check-mcp)
- Not recommended based on your preference

## Recommended Approach

**Phase 1: Create Template Repo** (2-3 hours)
1. Create new repo: `ai-lead-generator-framework`
2. Extract core infrastructure (listed above)
3. Create example usage documentation
4. Mark as template repo on GitHub

**Phase 2: Refactor This Repo** (1-2 hours)
1. Install framework as dependency
2. Remove duplicated infrastructure code
3. Keep only job-specific logic

**Phase 3: Create IP Commercialization Repo** (30 min)
1. Click "Use this template" on framework repo
2. Implement IP-specific logic:
   - Company discovery (vs job discovery)
   - IP portfolio matching (vs resume matching)
   - Decision-maker identification (vs hiring manager)
   - Outreach tracking (vs application tracking)

## Configuration Differences

### Job-Lead-Finder (Current)
```json
{
  "search_terms": ["python developer", "senior engineer"],
  "profile": "data/resume.txt",
  "match_threshold": 0.7,
  "providers": ["jsearch", "indeed", "linkedin"]
}
```

### IP-Commercialization (New)
```json
{
  "search_terms": ["companies needing {your_ip_tech}", "potential licensees"],
  "profile": "data/ip_portfolio.md",
  "match_threshold": 0.8,
  "providers": ["linkedin_sales", "crunchbase", "pitchbook", "zoominfo"]
}
```

## MCP Services to Reuse

All containerized MCP servers are reusable:
- ✅ `vibe-check-mcp` - Code/content validation
- ✅ `brave-search-mcp` - Better search than Google
- ✅ `fetch-mcp` - Web scraping (from your screenshot)
- ✅ `ollama-tunnel` - Free LLM access via cloudflare
- ✅ `ai-monitor` - Token usage tracking

## Next Steps

1. ✅ Clean up vibe-check-mcp submodule
2. ✅ Add Fetch MCP (from your screenshot)
3. ⏳ Consolidate nav.html and dashboard.html
4. ⏳ Create framework template repo
5. ⏳ Document IP commercialization use case
6. ⏳ Extract core infrastructure

## Questions to Answer

**For IP Commercialization Repo:**
- What IP/technology are you looking to commercialize?
- Target industries/company sizes?
- B2B or B2C focus?
- Geographic constraints?
- Outreach method (email, LinkedIn, cold call)?

**Naming:**
- `ip-lead-finder`
- `tech-commercialization-assistant`
- `patent-licensing-leads`
- Custom name?
