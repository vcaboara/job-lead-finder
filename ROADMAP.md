# Job Lead Finder — Autonomous Agent Roadmap

**Goal:** Minimal-touch system: finds jobs → scores them → generates application materials → submits applications → tracks outcomes. Vincent's hands stay off the keyboard.

**Compute strategy:**
- `llama3.2:3b` (Ollama) — fast job scoring/filtering, no cost
- `gemma4:12b` (Ollama) — quality cover letters/resume tailoring, no cost, fits in 12GB VRAM
- `claude-sonnet-4-6` — complex reasoning, debugging, quality review when Ollama output isn't good enough
- Gemini — avoid (unreliable optimism-bias)

---

## Status Legend
- `[ ]` Not started
- `[~]` In progress
- `[x]` Complete
- `[!]` Blocked

---

## Phase 0 — Bug Fixes & Foundations
*Target: Repo is stable and running end-to-end*

- [x] Job scraping (WeWorkRemotely, JSearch, Gemini fallback)
- [x] Ollama job scoring pipeline
- [x] JSON job tracker with status states
- [x] Background scheduler skeleton
- [x] FastAPI UI with job dashboard
- [x] Docker 8-service stack
- [ ] **Fix: background_scheduler.py tracker method name mismatch** (track() vs track_job())
- [ ] **Fix: upgrade default Ollama model to gemma4:12b for generation tasks**
- [ ] **Add: resume.txt loaded into repo** (blocking all generation — needs Vincent's resume)
- [ ] **Fix: cover_letter_generator.py — implement with Ollama (gemma4:12b)**
- [ ] **Fix: resume_generator.py — implement with Ollama (gemma4:12b)**
- [ ] Wire cover letter endpoint in UI (POST /api/jobs/{job_id}/cover-letter)
- [ ] Run full test suite clean on main

---

## Phase 1 — Autonomous Discovery & Scoring
*Target: System wakes up daily, finds new jobs, scores them, surfaces top 10*

- [ ] Scheduler: daily job discovery run (6am, configurable)
- [ ] Score threshold filter: only surface jobs scoring ≥ 65 (configurable)
- [ ] Duplicate detection: don't re-show jobs already tracked
- [ ] Job source expansion: RemoteOK, Remotive scrapers (direct HTTP, no API key needed)
- [ ] Role/keyword config: Vincent's target titles stored in config (not hardcoded)
- [ ] Salary range filter (skip jobs below threshold)
- [ ] Remote-only filter toggle
- [ ] UI: "Today's leads" view sorted by score descending
- [ ] Notification: write daily digest to `data/daily_digest.md` (readable without UI)

---

## Phase 2 — Application Materials Generation
*Target: One click generates tailored cover letter + resume section highlights*

- [ ] Resume ingestion: parse resume.txt into structured sections (skills, experience, etc.)
- [ ] Cover letter generation: Ollama gemma4:12b with job description + resume context
- [ ] Cover letter: job-specific tailoring (match keywords from JD to resume)
- [ ] Resume highlights: generate a 3-bullet "why I'm a fit" blurb per job
- [ ] Template: cover letter has Vincent's name, contact, date auto-filled
- [ ] UI: cover letter preview + copy-to-clipboard
- [ ] UI: export cover letter as .txt / .docx
- [ ] Quality gate: if Ollama cover letter scores < threshold, escalate to Claude API

---

## Phase 3 — Autonomous Application Submission
*Target: System submits applications without Vincent's involvement*

- [ ] Playwright browser automation setup (already in dependencies)
- [ ] **Greenhouse** form filler (most common ATS, predictable form structure)
- [ ] **Lever** form filler (second most common)
- [ ] **Ashby** form filler (growing, clean API-like forms)
- [ ] **LinkedIn Easy Apply** automation (highest volume, most complex)
- [ ] Application deduplication: don't apply to same job twice
- [ ] Application tracking: log submission timestamp, form URL, confirmation number
- [ ] Status: auto-mark jobs as "applied" after successful submission
- [ ] Error handling: if form fails, flag for manual review (don't silently drop)
- [ ] Human-in-loop escape hatch: jobs flagged "review_before_apply" pause for confirmation

---

## Phase 4 — Outcome Learning & Personalization
*Target: System learns what works and improves over time*

- [ ] Load Vincent's job application history (prior roles, rejections, interviews)
- [ ] Score calibration: adjust weights based on which job types got responses
- [ ] Cover letter A/B tracking: log which templates lead to responses
- [ ] Skill gap analysis: identify patterns in rejections (missing skills to acquire)
- [ ] Arboreum context: flag jobs at companies likely to value climate-tech background
- [ ] SQLite migration: move from JSON tracker to proper DB for query/analytics
- [ ] Weekly report: `data/weekly_report.md` — applications sent, responses, pipeline

---

## What We Need From Vincent (blocking items)

- [ ] **Resume file** — upload as `resume.txt` or `resume.pdf` in repo root (CRITICAL — blocks Phase 0 completion and all of Phases 1-4)
- [ ] **Target job titles** — what roles to search for (e.g., "Principal Engineer", "Staff Engineer", "Director of Engineering")
- [ ] **Salary floor** — minimum acceptable (for filtering)
- [ ] **Remote-only?** — or willing to consider hybrid/onsite?
- [ ] **Blocked companies** — any companies to never apply to

---

## Architecture Notes

```
[Scheduler: daily 6am]
    → scrape sources (WeWorkRemotely, RemoteOK, Remotive, JSearch)
    → deduplicate against tracker
    → Ollama llama3.2:3b batch score vs resume
    → filter: score ≥ 65, remote-ok, salary ≥ floor
    → generate cover letter: Ollama gemma4:12b
    → write to tracker (status: "ready")
    → write daily_digest.md

[UI: always-on]
    → show "ready" jobs sorted by score
    → one-click → apply (Playwright automation)
    → track status transitions

[Weekly]
    → generate outcome report
    → adjust scoring weights
```

---

## Current Branch / PR Log

| Branch | Status | Description |
|--------|--------|-------------|
| main | stable | Current production state |
| (next) | pending | Phase 0 fixes + cover letter generation |
