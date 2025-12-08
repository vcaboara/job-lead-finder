# Job Lead Finder - Product Requirements Document (PRD)

## Vision & Purpose

**Problem Statement:**
Job seekers face fragmentation across multiple job boards, lack of organization in tracking applications, and difficulty in evaluating job fit without AI assistance. Manual resume uploads and configuration management create friction in the job search process.

**Solution:**
Job Lead Finder is an AI-powered job search aggregation and tracking platform that:
- Consolidates jobs from multiple sources (WeWorkRemotely, RemoteOK, Remotive, company career pages)
- Provides intelligent job evaluation and custom cover letter generation via Google Gemini/Ollama
- Tracks application status through the entire hiring funnel
- Offers both CLI and web UI interfaces for flexible workflows
- Discovers companies passively via JSearch API integration

## Core Value Propositions

1. **Unified Job Discovery** - Single interface for multiple job sources
2. **AI-Enhanced Evaluation** - Gemini-powered job-resume matching and cover letter generation
3. **Application Tracking** - Organized funnel from discovery to offer
4. **Flexible Interface** - CLI for automation, Web UI for interactive browsing
5. **Company Discovery** - Passive identification of hiring companies via JSearch

## Target Users

### Primary Personas

**1. Active Job Seeker**
- Applying to multiple positions daily
- Needs organization and tracking
- Values AI-powered cover letters
- Wants resume-job matching

**2. Passive Candidate**
- Monitoring market opportunities
- Interested in company discovery
- Prefers quick evaluation
- Occasional application tracking

**3. Recruiter/Career Coach**
- Managing multiple candidates
- Bulk job discovery
- Tracking application pipelines
- Resume format flexibility

## Key Features & Requirements

### Must-Have (P0)

#### Job Aggregation
- **WeWorkRemotely Integration** - Scrape remote job listings
- **RemoteOK Integration** - API-based job retrieval
- **Remotive Integration** - Job board scraping
- **Company Career Pages** - Gemini-powered direct company search
- **Round-Robin Distribution** - Ensure diversity across providers
- **Parallel** - Use providers in parallel to find job listings for quality comparisons, etc. (TODO)

#### Job Tracking
- **Status Management** - new, applied, interviewing, rejected, offer, hidden
- **SQLite Storage** - Persistent job and application data
- **Search & Filter** - By status, provider, keyword
- **Duplicate Detection** - Avoid showing same job multiple times

#### AI Features (Gemini/Ollama)
- **Job Evaluation** - Match score against resume
- **Cover Letter Generation** - Customized per application
- **Company Career Page Discovery** - Find direct application links

#### Resume Management
- **Multi-Format Upload** - .txt, .md, .pdf, .docx
- **File Size Limits** - txt/md: 1MB, pdf: 2MB, docx: 1MB
- **Security Scanning** - Malicious content detection (scripts, macros, binary data)
- **Text Extraction** - PDF via pypdf, DOCX via python-docx
- **Mojibake Cleaning** - UTF-8 encoding fixes for PDFs

#### Web UI
- **FastAPI Server** - RESTful API at http://localhost:8000
- **Search Interface** - Find jobs with filters
- **Resume Upload** - Drag-and-drop with validation
- **Configuration Management** - System instructions, blocked entities
- **Link Validation** - Detect 404s and soft-404s

### Should-Have (P1)

#### Company Discovery (JSearch)
- **Search by Query** - Job title, location, tech stack
- **Tech Stack Detection** - Identify 30+ technologies
- **Industry Classification** - Tech, finance, healthcare, etc.
- **Company Database** - SQLite storage for discovered companies
- **CLI Commands** - `discover` with filters and save option

#### Link Discovery
- **Career Page Finding** - Extract direct application URLs from aggregators
- **Link Validation** - HTTP status checks, soft-404 detection
- **URL Normalization** - Canonicalize links for deduplication

#### Testing & Quality
- **Comprehensive Test Suite** - pytest + pytest-asyncio
- **Pre-commit Hooks** - black, isort, flake8, pytest
- **Test Runtime Optimization** - Target <5s via mocking
- **Code Quality** - 120 char line length, black formatting

### Nice-to-Have (P2)

- **Ollama Integration** - Local LLM fallback (removed as of PR #43)
- **Token Compression** - Reduce API costs via AI-Coding-Style-Guides
- **Async Job Fetching** - Parallel provider requests
- **Worker Process** - Background job discovery
- **Docker Deployment** - Containerized application

## User Workflows

### Workflow 1: CLI Job Search
```bash
# Search and evaluate jobs
uv run python -m app.main find -q "remote python developer" --resume resume.txt -n 10

# Discover companies
uv run python -m app.main discover -q "Python engineer" -l "Remote" --save

# Check health
uv run python -m app.main health
```

### Workflow 2: Web UI Job Discovery
1. Navigate to http://localhost:8000
2. Upload resume (drag-and-drop or select file)
3. Configure search preferences (industries, tech stacks)
4. Search for jobs with filters
5. View AI-generated evaluations
6. Update application status
7. Generate custom cover letters

### Workflow 3: Resume Upload
1. Select file (.txt, .md, .pdf, .docx)
2. Validate file size and format
3. Scan for malicious content
4. Extract text (with mojibake cleaning for PDFs)
5. Store and use for job matching

## Technical Constraints

### Performance
- **Test Runtime** - <5 seconds for full suite
- **API Rate Limits** - Respect provider rate limits
- **File Size** - Max 5MB total, format-specific limits

### Security
- **Input Validation** - All user inputs sanitized
- **Malicious Content Detection** - Scripts, macros, binary data
- **Secret Management** - API keys via .env file (not hardcoded)

### Compatibility
- **Python** - 3.12+
- **Browsers** - Modern browsers (Chrome, Firefox, Safari, Edge)
- **Docker** - Optional deployment via docker-compose

## Success Metrics

### User Engagement
- **Job Discovery Rate** - Jobs found per search
- **Application Conversion** - % of discoveries leading to applications
- **Resume Upload Success** - % of uploads passing validation

### System Performance
- **Test Suite Runtime** - <5 seconds (target)
- **API Response Time** - <2s for job search
- **Uptime** - >99% for web UI

### AI Quality
- **Job Match Accuracy** - User satisfaction with AI evaluations
- **Cover Letter Quality** - Acceptance rate of generated letters
- **Company Discovery Precision** - Relevance of JSearch results

## Future Enhancements

### Roadmap Items
1. **Token Compression** - Reduce API costs via style guides
2. **Advanced Filtering** - Salary range, company size, remote vs hybrid
3. **Email Notifications** - New job alerts matching criteria
4. **Calendar Integration** - Interview scheduling
5. **Application Templates** - Pre-filled forms for common fields
6. **Analytics Dashboard** - Application funnel metrics

### Integration Opportunities
- **LinkedIn** - Import profile data
- **Indeed** - Additional job source
- **Greenhouse/Lever** - ATS integrations
- **Google Calendar** - Interview scheduling
- **Notion/Airtable** - Export job data

## Dependencies & Assumptions

### Assumptions
- Users have valid API keys for Gemini and/or JSearch
- Job boards maintain stable HTML structure
- Users prefer privacy (local SQLite vs cloud storage)
- Docker is optional, not mandatory

### Key Dependencies
- **Google Gemini API** - For AI features (optional)
- **JSearch API (RapidAPI)** - For company discovery (optional)
- **Job Board Availability** - WeWorkRemotely, RemoteOK, Remotive
- **Python Ecosystem** - FastAPI, SQLAlchemy, httpx, beautifulsoup4

## Compliance & Legal

### Data Privacy
- **Local Storage** - All data stored locally (no cloud sync)
- **No Tracking** - No analytics or user tracking
- **API Key Security** - User-managed, not transmitted

### Terms of Service
- **Job Board Scraping** - Respect robots.txt and rate limits
- **API Usage** - Comply with Gemini and JSearch ToS
- **Resume Data** - User owns all uploaded data

## Documentation

### Required Documentation
- **README.md** - Quick start, features, installation (root)
- **docs/PERSONAL_CONFIG_GUIDE.md** - API key setup
- **docs/AGGREGATOR_TO_COMPANY_GUIDE.md** - Company search workflow
- **docs/JSEARCH_PROVIDER.md** - JSearch integration guide
- **docs/DISCOVERY_CLI.md** - CLI usage guide
- **docs/PROVIDERS.md** - Provider architecture
- **docs/RULEBOOK_INTEGRATION.md** - Rulebook-AI usage guide
- **docs/GITHUB_RULEBOOK_INTEGRATION.md** - GitHub Actions integration
- **docs/TODO.md** - Technical debt and future improvements
- **CHANGELOG.md** - Version history and changes (root)

### Developer Documentation
- **memory/docs/architecture.md** - System components and relationships
- **memory/docs/technical.md** - Development environment and stack
- **memory/tasks/tasks_plan.md** - Detailed task backlog
- **memory/tasks/active_context.md** - Current work focus
- **API Documentation** - FastAPI auto-generated docs at /docs
- **Test Guide** - Running and writing tests
- **Contributing Guide** - Code style, PR process

### Git Workflow & Version Control
**CRITICAL:** Direct pushes to `main` branch are **PROHIBITED**. All changes must follow the PR workflow:

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes & Commit**: Follow conventional commits (feat:, fix:, docs:, etc.)
3. **Push Branch**: `git push -u origin feature/your-feature-name`
4. **Create Pull Request**: On GitHub, create PR targeting `main`
5. **Automated Versioning**: Upon PR merge, GitHub Actions automatically:
   - Bumps version in `pyproject.toml` based on conventional commits
   - Creates git tag with release notes
   - Publishes GitHub release

**Branch Protection:**
- Pre-commit hook prevents direct pushes to `main`/`master`
- All commits must pass: black, isort, flake8, pytest
- See `docs/VERSIONING.md` for complete workflow details

---

**Document Status:** Living document, updated with each major feature release
**Last Updated:** December 2025
**Version:** 2.0 (Post-Enhanced Resume Upload & Company Discovery)
