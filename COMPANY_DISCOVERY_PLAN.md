# Company Discovery Feature - Implementation Plan

**Goal**: Enable automated discovery of companies and job opportunities beyond traditional aggregators, making job searching passive and efficient.

**Key Principle**: Extensible architecture for any industry (tech-focused initially)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ Discovery Sources (Pluggable Providers)             │
├─────────────────────────────────────────────────────┤
│ • HN Who's Hiring (tech)                            │
│ • YC Companies (startups)                           │
│ • GitHub Organizations (open source companies)      │
│ • AngelList/Wellfound (startups)                    │
│ • Industry-specific sources (extensible)            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Company Database (SQLite)                           │
├─────────────────────────────────────────────────────┤
│ • company_id, name, website, industry               │
│ • careers_url, last_checked, found_via              │
│ • employee_count, funding_stage, tech_stack         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Careers Page Crawler (Background Service)           │
├─────────────────────────────────────────────────────┤
│ • Daily/hourly checks of discovered companies       │
│ • Extract job listings from careers pages           │
│ • Match against user profile/resume                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Smart Notifications (Low-friction output)           │
├─────────────────────────────────────────────────────┤
│ • Email digest (daily/weekly)                       │
│ • Slack/Discord webhooks                            │
│ • In-app notifications                              │
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Week 1-2)
**Goal**: Set up extensible discovery infrastructure

### Tasks:
- [ ] **1.1 Create Discovery Provider Interface**
  - File: `src/app/discovery/base_provider.py`
  - Abstract base class for all discovery sources
  - Methods: `discover_companies()`, `get_metadata()`, `supported_industries()`
  
- [ ] **1.2 Company Database Schema**
  - File: `src/app/discovery/company_store.py`
  - SQLite database for discovered companies
  - Schema: companies, jobs, discovery_log
  - CRUD operations with async support
  
- [ ] **1.3 Configuration System**
  - Add to `config.json`: discovery settings
  - Industry preferences
  - Check frequency (hourly/daily)
  - Notification preferences

### Deliverables:
- Base provider interface
- Company database with migrations
- Config schema updates
- Unit tests for database operations

---

## Phase 2: First Discovery Source - HN Who's Hiring (Week 2-3)
**Goal**: Implement simplest, highest-value source

### Tasks:
- [ ] **2.1 HN Parser Provider**
  - File: `src/app/discovery/providers/hn_provider.py`
  - Parse monthly "Who is hiring?" threads
  - Extract: company name, description, tech stack, location
  - Detect thread ID automatically (changes monthly)
  
- [ ] **2.2 Company Extraction Logic**
  - Use Gemini to parse unstructured HN posts
  - Extract structured data: company, role, requirements
  - Detect careers URL if mentioned
  
- [ ] **2.3 CLI Command**
  - `python -m app.main discover --source hn`
  - Store discovered companies in database
  - Show summary of new discoveries

### Deliverables:
- Working HN parser
- 50-100 companies discovered per month
- Integration tests
- CLI command

---

## Phase 3: Careers Page Crawler (Week 3-4)
**Goal**: Monitor discovered companies for job openings

### Tasks:
- [ ] **3.1 Careers URL Discovery**
  - File: `src/app/discovery/careers_finder.py`
  - Given company website, find careers page
  - Common patterns: `/careers`, `/jobs`, `/join`, `/work-with-us`
  - Use sitemap.xml if available
  
- [ ] **3.2 Job Listing Scraper**
  - File: `src/app/discovery/job_scraper.py`
  - Extract job listings from careers pages
  - Handle different formats (Greenhouse, Lever, custom)
  - Respect robots.txt
  
- [ ] **3.3 Background Service**
  - File: `src/app/discovery/crawler_daemon.py`
  - Async job checking (100+ companies/hour)
  - Configurable check frequency per company
  - Rate limiting and polite crawling

### Deliverables:
- Careers page finder (70%+ success rate)
- Multi-format job scraper
- Background daemon service
- Docker support for continuous running

---

## Phase 4: Smart Matching & Notifications (Week 4-5)
**Goal**: Surface relevant opportunities with minimal user effort

### Tasks:
- [ ] **4.1 Job Matching Engine**
  - Use existing Gemini evaluation
  - Match against uploaded resume
  - Score: company size, tech stack, role fit
  
- [ ] **4.2 Notification System**
  - File: `src/app/discovery/notifier.py`
  - Email digest (HTML template)
  - Webhook support (Slack, Discord)
  - In-app notification queue
  
- [ ] **4.3 UI Integration**
  - New tab: "Discovered Companies"
  - Show: company name, last checked, # of jobs
  - One-click: open careers page, track company

### Deliverables:
- Working notification system
- Email template with job matches
- UI panel for discovered companies
- User preferences for notifications

---

## Phase 5: Additional Discovery Sources (Week 5-6)
**Goal**: Expand coverage beyond tech/HN

### Tasks:
- [ ] **5.1 YC Companies Provider**
  - File: `src/app/discovery/providers/yc_provider.py`
  - Fetch YC company directory
  - Filter by batch, status (active/acquired)
  - ~4000 companies
  
- [ ] **5.2 GitHub Organizations Provider**
  - File: `src/app/discovery/providers/github_provider.py`
  - Find orgs with active repos in user's tech stack
  - Filter by language, activity, size
  
- [ ] **5.3 Industry-Agnostic Providers**
  - LinkedIn company search API
  - Crunchbase API (requires key)
  - Local business directories

### Deliverables:
- 2-3 additional working providers
- Combined discovery from multiple sources
- Deduplication logic
- Provider health monitoring

---

## Phase 6: Optimization & Polish (Week 6-7)
**Goal**: Production-ready, efficient, user-friendly

### Tasks:
- [ ] **6.1 Performance Optimization**
  - Async/concurrent crawling
  - Caching strategies
  - Database indexing
  
- [ ] **6.2 User Experience**
  - Onboarding flow for discovery setup
  - Discovery status dashboard
  - Company watchlist feature
  
- [ ] **6.3 Monitoring & Logging**
  - Discovery metrics (companies/day, success rate)
  - Error tracking for failed scrapes
  - Provider health checks

### Deliverables:
- Sub-5-minute discovery runs
- 90%+ uptime for background service
- User-friendly setup wizard
- Metrics dashboard

---

## File Structure (New)

```
src/app/
├── discovery/
│   ├── __init__.py
│   ├── base_provider.py          # Abstract provider interface
│   ├── company_store.py           # SQLite database for companies
│   ├── careers_finder.py          # Find careers URLs
│   ├── job_scraper.py             # Scrape job listings
│   ├── crawler_daemon.py          # Background service
│   ├── notifier.py                # Notification system
│   ├── matcher.py                 # Job matching logic
│   └── providers/
│       ├── __init__.py
│       ├── hn_provider.py         # Hacker News
│       ├── yc_provider.py         # Y Combinator
│       ├── github_provider.py     # GitHub orgs
│       └── linkedin_provider.py   # LinkedIn (future)
│
├── discovery_cli.py               # CLI commands for discovery
└── discovery_ui.py                # UI endpoints for discovery

tests/
├── test_discovery/
│   ├── test_company_store.py
│   ├── test_providers.py
│   ├── test_scraper.py
│   └── fixtures/
│       └── sample_careers_pages.html
```

---

## Configuration Schema Updates

Add to `config.json`:

```json
{
  "discovery": {
    "enabled": true,
    "check_frequency_hours": 24,
    "sources": {
      "hn_whos_hiring": { "enabled": true },
      "yc_companies": { "enabled": true },
      "github_orgs": { "enabled": false }
    },
    "filters": {
      "company_size": ["startup", "small", "medium"],
      "industries": ["tech", "saas", "developer-tools"],
      "locations": ["remote", "seattle", "san-francisco"],
      "funding_stages": ["seed", "series-a", "series-b"]
    },
    "notifications": {
      "email": {
        "enabled": false,
        "address": "",
        "frequency": "daily"
      },
      "webhook": {
        "enabled": false,
        "url": ""
      }
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
- Provider interface compliance
- Database CRUD operations
- URL parsing/extraction
- Notification formatting

### Integration Tests
- Full discovery flow (source → database → notification)
- Multi-provider deduplication
- Crawler rate limiting

### End-to-End Tests
- CLI: discover → store → notify
- UI: view discoveries → track company → get notified

---

## Success Metrics

### Phase 1-2 (Foundation + HN)
- ✅ Discover 50+ companies from single HN thread
- ✅ Store companies in database
- ✅ CLI command working

### Phase 3-4 (Crawler + Notifications)
- ✅ Successfully find careers pages for 70%+ of companies
- ✅ Extract jobs from 50%+ of careers pages
- ✅ Send first email digest with matched jobs

### Phase 5-6 (Expansion + Polish)
- ✅ 500+ companies in database
- ✅ Check 100+ careers pages per day
- ✅ <5% false positive match rate
- ✅ User can set up discovery in <5 minutes

---

## Next Steps (Priority Order)

1. **Review this plan** - Adjust phases/scope as needed
2. **Start Phase 1.1** - Create base provider interface
3. **Implement Phase 1.2** - Company database schema
4. **Quick win: Phase 2.1** - HN parser (can be done in parallel)

---

## Industry Extensibility Strategy

The provider interface supports any industry:

```python
class IndustryProvider(BaseDiscoveryProvider):
    def supported_industries(self) -> list[str]:
        return ["healthcare", "finance", "tech"]
    
    def discover_companies(self, filters: dict) -> list[Company]:
        # Industry-specific discovery logic
        pass
```

**Future providers:**
- Healthcare: HealthcareITJobs, Doximity
- Finance: eFinancialCareers, Wall Street Oasis
- Academia: HigherEdJobs, Chronicle Vitae
- Non-profit: Idealist, CharityNavigator

Each industry can have its own discovery sources while sharing:
- Company database
- Crawler infrastructure
- Notification system
- Matching engine

---

## Notes

- **Desktop vs Laptop**: This plan assumes continuous background service on desktop (24/7), laptop for development/testing
- **Resource Usage**: Background crawler designed for <100MB RAM, <5% CPU when idle
- **Privacy**: All data stored locally, no external tracking
- **Extensibility**: Plugin architecture allows community contributions of new providers

---

## Questions for Next Session

1. What industries beyond tech are you interested in?
2. Email vs Slack vs in-app notifications preference?
3. How aggressive should discovery be? (100 vs 1000 companies/month)
4. Any specific companies/sources you already know you want to track?
