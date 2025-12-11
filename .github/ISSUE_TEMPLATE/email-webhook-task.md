---
name: Email Webhook Integration
about: P1 Track 2 - Inbound Email Webhook System
title: '[AI] P1: Inbound Email Webhook Integration'
labels: enhancement, ai-mlops-test
assignees: ''
---

## Task Type

**Priority**: P1 (Email Integration)
**Agent**: @copilot
**Estimated Effort**: 3-4 hours
**Branch**: `feature/email-webhook-integration`

## Context

Previous PR #86 implemented IMAP credential-based email access, which was the wrong approach. Users should not share email credentials.

**Better approach**: Inbound email webhook system where users forward job-related emails to unique addresses (e.g., `user-abc123@jobforge.com`).

**RFC**: Complete specification at `memory/tasks/rfc/email-webhook-integration.md`

## Objective

Implement inbound email webhook system for automated job discovery and application tracking via forwarded emails.

## Requirements

### Phase 1: Core Email Receiving (1.5 hours)

- [ ] Set up SendGrid Inbound Parse webhook configuration
- [ ] Create `src/app/email_webhook.py` with webhook handler
- [ ] Implement user forwarding address generation (user-{uuid}@jobforge.com)
- [ ] Add database schema for `email_configs` and `training_emails` tables
- [ ] Create `/api/email/inbound` POST endpoint in `ui_server.py`
- [ ] Store raw emails in database with user association

### Phase 2: Email Classification (1 hour)

- [ ] Create `src/app/email_parser.py` module
- [ ] Implement `detect_email_type()` with pattern matching:
  - `job_listing`: LinkedIn/Indeed/Monster job alerts
  - `application_confirm`: Workday/Greenhouse/Lever receipts
  - `recruiter_outreach`: Personal emails with job offers
- [ ] Add email parsing for sender, subject, body, date
- [ ] Write comprehensive test suite for classification

### Phase 3: Job Extraction & Tracking (1 hour)

- [ ] Implement `extract_job_details()` to parse:
  - Company name (from domain or body)
  - Job title (from subject patterns)
  - Application URL (from body links)
  - Job description (from email content)
- [ ] Create jobs automatically from forwarded listings
- [ ] Match confirmation emails to existing tracked jobs
- [ ] Update job status to "applied" when confirmations matched
- [ ] Store emails in training pipeline (with user consent)

### Phase 4: UI & Documentation (0.5 hours)

- [ ] Add "Email Integration" section to settings page
- [ ] Display user's unique forwarding address
- [ ] Show email processing stats (emails received, jobs created, last sync)
- [ ] Create test suite with sample emails in `tests/fixtures/emails/`:
  - `linkedin_job_alert.eml`
  - `indeed_digest.eml`
  - `workday_confirmation.eml`
  - `greenhouse_receipt.eml`
  - `recruiter_outreach.eml`
- [ ] Write `docs/EMAIL_WEBHOOK_SETUP.md` with:
  - SendGrid setup instructions
  - Email forwarding rule templates
  - Troubleshooting guide

## Implementation Details

**Key Components**:
1. SendGrid Inbound Parse webhook (free tier: 100 emails/day)
2. Unique user forwarding addresses with UUID
3. Email parser with 3-type classification
4. Job creation from listings + status updates from confirmations
5. ML training data storage (encrypted, with consent)

**Environment Variables**:
```env
SENDGRID_API_KEY=your-key
SENDGRID_DOMAIN=jobforge.com
EMAIL_TRAINING_ENABLED=true
EMAIL_RETENTION_DAYS=90
```

**Security**:
- Validate forwarding address before processing
- Rate limit: 100 emails/day per user
- Strip sensitive data (SSN, credit cards) before storage
- Encrypt email content at rest

## Acceptance Criteria

- [ ] SendGrid webhook receives POST requests successfully
- [ ] User can generate unique forwarding address in UI
- [ ] Email classifier achieves >80% accuracy on test samples
- [ ] Creates jobs from LinkedIn/Indeed/Monster alerts
- [ ] Updates job status from Workday/Greenhouse/Lever confirmations
- [ ] Handles recruiter outreach emails (creates high-priority jobs)
- [ ] UI displays forwarding address and processing stats
- [ ] All tests pass with sample .eml files
- [ ] Documentation complete with setup guide
- [ ] Code follows project conventions (pytest, type hints, logging)
- [ ] Commits use [AI] tag with attribution footer

## AI MLOps Evaluation Metrics

This task measures:
1. **Implementation accuracy**: Code correctness, edge case handling
2. **Code quality**: Tests, documentation, conventions
3. **Architecture alignment**: Fits existing system, reuses components
4. **Time efficiency**: Completed within 3-4 hour estimate
5. **Functional correctness**: Webhooks work, parsing accurate, jobs created

## Related

- Closed PR #86 (wrong IMAP approach)
- RFC: `memory/tasks/rfc/email-webhook-integration.md`
- Similar pattern: `src/app/job_finder.py` (job discovery)
- Job tracker: `src/app/job_tracker.py` (status updates)

---

**AI-Task-Assignment**: @copilot
**Priority**: P1
**Estimated-Tokens**: 2-3 premium requests
