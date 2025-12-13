# RFC: Inbound Email Webhook Integration

**Status**: Proposed
**Priority**: P1 Track 2 (Revised)
**Estimated Effort**: 3-4 hours
**Created**: 2025-12-10
**AI Task**: Yes - For AI MLOps evaluation

## Problem Statement

Users need a way to integrate job-related emails (LinkedIn notifications, Indeed alerts, company responses) into JobForge for:
1. **Automated job discovery** - Create tracked jobs from forwarded listings
2. **Application tracking** - Update status when users forward application confirmations
3. **ML training data** - Collect diverse job listing formats for model improvement
4. **Interest tracking** - Track jobs from first contact (email alert) through application

**Current limitation**: No secure way to ingest email data without requiring user credentials (which is a security/privacy concern).

## Proposed Solution

Implement an **inbound email webhook system** where each user gets a unique forwarding address (e.g., `user-abc123@jobforge.com`). Users set up email forwarding rules to send job-related emails to this address, and JobForge processes them automatically.

### Architecture

```
┌─────────────────┐
│  User's Email   │
│  (Gmail, etc.)  │
└────────┬────────┘
         │ Forward rule:
         │ from:linkedin.com → user-abc123@jobforge.com
         ▼
┌─────────────────┐
│  Email Service  │
│  (SendGrid/SES) │ ← Webhook on incoming email
└────────┬────────┘
         │ POST /api/email/inbound
         ▼
┌─────────────────┐
│  Email Parser   │
│  - Extract job  │
│  - Match user   │
│  - Parse fields │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Job Tracker / Training Pipeline    │
│  - Create job from listing          │
│  - Update status from confirmation  │
│  - Store for ML training            │
└─────────────────────────────────────┘
```

### Key Components

#### 1. Email Receiving Service

**Options**:
- **SendGrid Inbound Parse** (recommended for MVP)
  - Free tier: 100 emails/day
  - Simple webhook integration
  - Parses multipart emails automatically

- **AWS SES** (for production scale)
  - Pay-per-email ($0.10/1000)
  - Store in S3, trigger Lambda
  - More control, harder setup

- **Self-hosted SMTP** (future)
  - Full control
  - Requires mail server management

**MVP Choice**: SendGrid Inbound Parse

#### 2. User Email Address Management

```python
@dataclass
class UserEmailConfig:
    user_id: str
    forwarding_address: str  # user-{uuid}@jobforge.com
    created_at: datetime
    email_count: int = 0
    last_email_at: Optional[datetime] = None
    is_active: bool = True
```

**Address generation**:
```python
def create_user_forwarding_address(user_id: str) -> str:
    uuid = generate_short_uuid()  # e.g., "a3f9k2"
    return f"user-{uuid}@jobforge.com"
```

#### 3. Email Parser

Reuse parsing logic from closed PR #86, but adapt for:
- **Job listings** (LinkedIn, Indeed, Monster alerts)
- **Application confirmations** (Workday, Greenhouse, Lever receipts)
- **Recruiter outreach** (personalized emails from companies)

```python
class InboundEmailParser:
    def parse(self, email: EmailMessage) -> ParsedEmail:
        """Parse inbound email into structured data."""

    def detect_email_type(self, email: ParsedEmail) -> EmailType:
        """Classify: job_listing | application_confirm | recruiter_outreach"""

    def extract_job_details(self, email: ParsedEmail) -> Optional[JobDetails]:
        """Extract company, title, URL, description from email body."""

    def match_to_existing_job(self, email: ParsedEmail) -> Optional[str]:
        """Match to existing tracked job (for status updates)."""
```

**Email type detection patterns**:
- **Job listing**: "jobs you might be interested in", "new job alert", "recommended for you"
- **Application confirmation**: "application received", "thank you for applying", "we received your application"
- **Recruiter outreach**: personal sender, direct job offer, "I came across your profile"

#### 4. Job Creation/Update Logic

```python
async def handle_inbound_email(email_data: dict):
    # 1. Identify user from forwarding address
    user_id = get_user_from_address(email_data['to'])

    # 2. Parse email
    parsed = parser.parse(email_data)
    email_type = parser.detect_email_type(parsed)

    # 3. Handle based on type
    if email_type == EmailType.JOB_LISTING:
        job = parser.extract_job_details(parsed)
        if job:
            tracker.create_job(user_id, job, source="email_forward")
            training_pipeline.store(parsed, label="job_listing")

    elif email_type == EmailType.APPLICATION_CONFIRM:
        existing_job = parser.match_to_existing_job(parsed)
        if existing_job:
            tracker.update_status(existing_job, "applied", applied_date=parsed.date)
        training_pipeline.store(parsed, label="application_confirm")

    elif email_type == EmailType.RECRUITER_OUTREACH:
        job = parser.extract_job_details(parsed)
        if job:
            tracker.create_job(user_id, job, source="recruiter_email", priority=True)
        training_pipeline.store(parsed, label="recruiter_outreach")
```

#### 5. ML Training Pipeline

Store all forwarded emails (with user consent) for:
- Improving job detail extraction
- Training email classifier
- Understanding job listing variations
- Building resume-job matching models

```python
@dataclass
class TrainingEmail:
    email_id: str
    user_id: str
    raw_email: str
    parsed_data: dict
    email_type: EmailType
    extracted_job: Optional[JobDetails]
    validation_status: str  # pending | validated | rejected
    created_at: datetime
```

### API Endpoints

```python
# Webhook endpoint (called by SendGrid)
POST /api/email/inbound
Body: multipart/form-data with email content
Response: 200 OK

# User management
POST /api/user/email/setup
Response: {"forwarding_address": "user-abc123@jobforge.com"}

GET /api/user/email/stats
Response: {
    "forwarding_address": "user-abc123@jobforge.com",
    "emails_processed": 42,
    "jobs_created": 15,
    "last_email_at": "2025-12-09T10:30:00Z"
}

POST /api/user/email/disable
Response: 200 OK (stops processing emails)
```

### Security & Privacy

1. **Address validation**: Only process emails to valid user addresses
2. **Rate limiting**: Max 100 emails/day per user (prevent abuse)
3. **Content filtering**: Strip sensitive data (SSN, credit cards) before storage
4. **User consent**: Explicit opt-in for ML training data collection
5. **Data retention**: Configurable (default: 90 days for training data)
6. **Encryption**: Store email content encrypted at rest

### User Experience

**Setup Flow**:
1. User clicks "Enable Email Integration" in settings
2. System generates unique forwarding address: `user-a3f9k2@jobforge.com`
3. Show instructions for setting up forwarding rules:
   - Gmail: Settings → Forwarding → Add address
   - Outlook: Rules → Forward to
4. User forwards job emails manually or via auto-rule
5. Jobs appear automatically in tracker

**Example Forwarding Rules**:
- Forward all emails from `linkedin.com` containing "job" → `user-a3f9k2@jobforge.com`
- Forward emails from `indeed.com` → `user-a3f9k2@jobforge.com`
- Forward emails containing "application received" → `user-a3f9k2@jobforge.com`

## Implementation Plan

### Phase 1: Core Email Receiving (1.5 hours)
- [ ] Set up SendGrid account and inbound parse webhook
- [ ] Create `/api/email/inbound` endpoint
- [ ] Implement user forwarding address generation
- [ ] Basic email parsing (sender, subject, body)
- [ ] Store raw emails in database

### Phase 2: Email Classification (1 hour)
- [ ] Implement `detect_email_type()` with pattern matching
- [ ] Add support for common job platforms (LinkedIn, Indeed, Monster)
- [ ] Create test suite with sample emails
- [ ] Validate classification accuracy

### Phase 3: Job Extraction & Tracking (1 hour)
- [ ] Extract job details from listings (company, title, URL)
- [ ] Create jobs from forwarded listings
- [ ] Match confirmation emails to existing jobs
- [ ] Update job status from confirmations

### Phase 4: UI & Documentation (0.5 hours)
- [ ] Add "Email Integration" section to settings
- [ ] Display forwarding address and stats
- [ ] Write setup guide with screenshots
- [ ] Add email forwarding rule templates

## Testing Strategy

### Test Cases

1. **Job listing emails**:
   - LinkedIn job alert with 5 listings
   - Indeed daily digest
   - Monster recommended jobs
   - Expected: Create 5 tracked jobs with correct details

2. **Application confirmations**:
   - Workday "Application Submitted" email
   - Greenhouse "Thank you" email
   - Lever receipt
   - Expected: Match to existing job, update status to "applied"

3. **Recruiter outreach**:
   - Personal email from recruiter with job details
   - Expected: Create high-priority tracked job

4. **Edge cases**:
   - Email with no recognizable job
   - Duplicate forwarded email
   - Malformed email content
   - Expected: Graceful handling, log for review

### Sample Emails

Collect real examples:
```
tests/fixtures/emails/
├── linkedin_job_alert.eml
├── indeed_digest.eml
├── workday_confirmation.eml
├── recruiter_outreach.eml
└── spam_email.eml
```

## Metrics for AI MLOps Evaluation

Track the following to evaluate AI assistant performance:

1. **Implementation accuracy**:
   - Does the code correctly handle email parsing?
   - Are edge cases covered?
   - Is error handling robust?

2. **Code quality**:
   - Follows project conventions?
   - Proper testing coverage?
   - Documentation complete?

3. **Architecture alignment**:
   - Fits existing system design?
   - Reuses existing components appropriately?
   - Maintainable and extensible?

4. **Time efficiency**:
   - Completed within 3-4 hour estimate?
   - Minimal back-and-forth needed?

5. **Functional correctness**:
   - Successfully receives webhooks?
   - Parses common email formats?
   - Creates/updates jobs correctly?

## Success Criteria

- ✅ SendGrid webhook receiving emails
- ✅ User can generate forwarding address
- ✅ System correctly classifies 3 email types
- ✅ Creates jobs from LinkedIn/Indeed alerts
- ✅ Updates status from application confirmations
- ✅ Stores emails for ML training (with consent)
- ✅ UI shows forwarding address and stats
- ✅ Documentation with setup instructions
- ✅ Test suite with sample emails passes

## Future Enhancements

1. **Smart filtering**: Learn which emails are useful vs spam
2. **Email templates**: Send outreach emails via the system
3. **Response tracking**: Track replies from companies
4. **Calendar integration**: Create reminders from interview emails
5. **Multi-address support**: Different addresses for different sources
6. **Email analytics**: Track which sources generate best leads

## Dependencies

- SendGrid account (free tier sufficient for MVP)
- Database schema update (add `email_configs` and `training_emails` tables)
- Environment variables: `SENDGRID_API_KEY`, `SENDGRID_DOMAIN`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Email parsing errors | Jobs not created | Extensive test suite, fallback to manual review |
| Spam/abuse | System overload | Rate limiting, user validation |
| Privacy concerns | User distrust | Clear consent, encryption, data retention policy |
| SendGrid limits | Service disruption | Plan upgrade path to AWS SES |
| False job matches | Status updates wrong job | Conservative matching (require 2+ fields match) |

## Questions for Implementation

1. Should we support reply-to functionality (send emails via JobForge)?
2. What's the data retention policy for training emails?
3. Should we show email preview in UI before creating job?
4. Enable/disable per email source (e.g., only LinkedIn)?

## Related Documents

- Closed PR #86: Original IMAP approach (wrong direction)
- `docs/PROVIDERS.md`: Job discovery providers
- `memory/docs/architecture.md`: System architecture
- `memory/tasks/tasks_plan.md`: P1 Track 2 definition

---

**AI Implementation Note**: This RFC is designed for AI MLOps to implement autonomously as a test of capabilities. Success will be measured against the metrics above.
