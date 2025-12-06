# Task Tracker

Track all development tasks for Job Lead Finder project.

## Current Sprint (Dec 2025)

### 🎯 High Priority

- [ ] **Integrate JSearch into UI** (Not Started)
  - [ ] Add "Discover Companies" button to UI
  - [ ] Create discovery results page
  - [ ] Show JSearch companies in searchable list
  - [ ] Allow filtering by tech stack, location, etc.
  - [ ] Save discovered companies to database

- [x] **Discovery CLI Command** (Completed: Dec 6, 2025)
  - [x] Create CLI command: `python -m app.main discover`
  - [x] Support query, location, industry, tech stack filters
  - [x] Add --save flag to persist to database
  - [x] Add --verbose flag for detailed output
  - [x] Handle companies without websites gracefully

### 📋 Medium Priority

- [ ] **Background Monitoring** (Not Started)
  - [ ] Schedule daily discovery runs
  - [ ] Track which companies are new vs. seen before
  - [ ] Email/notification system for new discoveries

- [ ] **UI Improvements from Lovable.dev** (Not Started)
  - [ ] Decide which UI components to adopt
  - [ ] Copy and adapt styling
  - [ ] Maintain existing functionality
  - [ ] Test responsive design

### 🔍 Low Priority

- [ ] **Export/Import Functionality** (Not Started)
  - [ ] Export tracked jobs to CSV
  - [ ] Import jobs from CSV
  - [ ] Export discovered companies

- [ ] **Advanced Filtering** (Not Started)
  - [ ] Filter jobs by multiple criteria
  - [ ] Save filter presets
  - [ ] Search across all fields

## ✅ Recently Completed

- [x] **Discovery CLI Command** (Completed: Dec 6, 2025)
  - [x] Added `discover` subcommand to main.py
  - [x] Query, location, industry, tech stack filters
  - [x] Save to database with --save flag
  - [x] Skip companies without websites
  - [x] Verbose output mode
  - [x] Integration with JSearchProvider

- [x] **Documentation Updates** (Completed: Dec 6, 2025)
  - [x] Updated README.md with JSearch discovery feature
  - [x] Added environment setup section for API keys
  - [x] Updated project structure to show discovery/ package
  - [x] Added CHANGELOG entry for discovery system
  - [x] Updated CLI usage examples

- [x] **JSearch Provider Implementation** (Completed: Dec 5, 2025)
  - [x] Create jsearch_provider.py with BaseDiscoveryProvider interface
  - [x] Implement discover_companies() with pagination
  - [x] Add tech stack detection (30+ technologies)
  - [x] Handle API errors and rate limits
  - [x] Write 13 comprehensive tests (all passing)
  - [x] Create test script (test_jsearch.py)
  - [x] Document in JSEARCH_PROVIDER.md

- [x] **Clear All Button** (Completed: Dec 4, 2025)
  - [x] Add Clear All button to UI
  - [x] Implement DELETE /api/jobs/tracked/clear endpoint
  - [x] Add confirmation dialog
  - [x] Update tests

- [x] **Fix Track Button** (Completed: Dec 4, 2025)
  - [x] Create POST /api/jobs/track endpoint
  - [x] Send full job data from frontend
  - [x] Fix tests to manually track jobs
  - [x] Verify Track button works after Clear All

- [x] **Remove Auto-Tracking** (Completed: Dec 4, 2025)
  - [x] Remove tracker.track_job() from search results
  - [x] Update all tests
  - [x] Verify manual tracking only

- [x] **Git Workflow Fix** (Completed: Dec 4, 2025)
  - [x] Reset main to origin/main
  - [x] Create feature branches
  - [x] Document workflow in PLANNING.md

- [x] **Formatter Cleanup** (Completed: Dec 4, 2025)
  - [x] Remove autopep8
  - [x] Configure Black explicitly
  - [x] Fix quote style conflicts

- [x] **Discovery Phase 1** (Completed: Dec 3, 2025)
  - [x] Create base_provider.py abstract class
  - [x] Create company_store.py with SQLite
  - [x] Create config.py for discovery settings
  - [x] Write comprehensive tests
  - [x] Document architecture

## 📝 Discovered During Work

### From JSearch Implementation
- [ ] Add more technologies to tech stack detection
- [ ] Improve industry classification (currently only TECH/OTHER)
- [ ] Add company size estimation logic
- [ ] Rate limiting helper for RapidAPI calls

### From Previous Work
- [ ] Fix unclosed SQLite connections in discovery config tests
- [ ] Add context engineering documentation
- [ ] Consider UI redesign from Lovable.dev

## 🚫 Blocked / On Hold

None currently.

## 📚 Backlog

- PDF resume extraction improvements
- Better error messages in UI
- Job application deadline tracking
- Interview preparation notes
- Salary range tracking
- Company research notes integration
- Integration with calendar for interview scheduling

## 💡 Ideas for Future

- Chrome extension for one-click job tracking
- LinkedIn profile analyzer
- Cover letter templates
- Interview question database
- Salary negotiation tips
- Job market analytics dashboard
- AI-powered interview prep

---

## How to Use This File

- **Starting a task**: Move from backlog to current sprint, add date
- **Completing a task**: Check it off, add completion date
- **Discovering new work**: Add to "Discovered During Work" section
- **Blocking**: Move to "Blocked" with reason
- **New ideas**: Add to "Ideas for Future"

Last updated: December 5, 2025
