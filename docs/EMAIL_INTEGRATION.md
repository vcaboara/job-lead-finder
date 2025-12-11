# Email Integration

Automated job application tracking via email monitoring.

## Features

- **IMAP Integration**: Connect to Gmail, Outlook, or any IMAP email server
- **Automatic Tracking**: Monitors sent folder for job applications
- **Smart Matching**: Links sent emails to tracked jobs
- **Auto-Update Status**: Changes job status to "applied" when email sent
- **Email Parsing**: Extracts company name, job title, and application URLs

## Setup

### 1. Configure Email Credentials

Add to your `.env` file:

```env
# Email Integration
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
IMAP_SERVER=imap.gmail.com  # Optional, defaults to Gmail
```

### 2. Gmail App Password (Recommended)

For Gmail users, use an [App Password](https://myaccount.google.com/apppasswords):

1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password for "Mail"
4. Use the 16-character password in `.env`

**Why?** App passwords are more secure and bypass 2FA prompts.

### 3. Outlook Configuration

For Outlook/Office 365:

```env
EMAIL_ADDRESS=your.email@outlook.com
EMAIL_PASSWORD=your-password
IMAP_SERVER=outlook.office365.com
```

## Usage

### Test Connection

```bash
python -m app.cli_email test
```

**Output**:
```
2025-12-10 18:45:00 - INFO - Testing connection to imap.gmail.com...
2025-12-10 18:45:01 - INFO - Connected to imap.gmail.com
2025-12-10 18:45:01 - INFO - ✓ Connection successful
```

### Check Recent Sent Emails

```bash
# Last 7 days (default)
python -m app.cli_email check

# Last 30 days
python -m app.cli_email check --days 30
```

**Output**:
```
============================================================
Date: 2025-12-08 14:30:00
Subject: Application for Senior Python Developer
To: careers@techcorp.com
Company: Techcorp
Job Title: Senior Python Developer
Application URL: https://techcorp.com/apply/123
```

### Sync Job Status from Emails

```bash
# Sync last 7 days
python -m app.cli_email sync

# Sync last 14 days
python -m app.cli_email sync --days 14
```

**Output**:
```
2025-12-10 18:45:00 - INFO - Syncing job status from last 7 days...
2025-12-10 18:45:02 - INFO - Fetched 5 emails
2025-12-10 18:45:02 - INFO - Updated job abc123 to 'applied'
2025-12-10 18:45:02 - INFO - Updated job def456 to 'applied'

Sync Results:
  Emails checked: 5
  Jobs updated: 2
  Jobs not found: 3
```

## Programmatic Usage

### Basic Example

```python
from app.email_integration import EmailConfig, EmailIntegration

config = EmailConfig(
    imap_server="imap.gmail.com",
    email_address="your@email.com",
    password="your-password"
)

integration = EmailIntegration(config)

# Connect and sync
if integration.connect():
    stats = integration.auto_update_job_status(days=7)
    print(f"Updated {stats['jobs_updated']} jobs")
    integration.disconnect()
```

### Environment-Based Config

```python
from app.email_integration import (
    EmailIntegration,
    create_email_config_from_env
)

config = create_email_config_from_env()
if config:
    integration = EmailIntegration(config)
    # Use integration...
```

## How It Works

### 1. Email Fetching

- Connects to IMAP server
- Selects sent mail folder (tries common names)
- Fetches emails from last N days
- Parses email headers and body

### 2. Information Extraction

From each email, extracts:
- **Company Name**: From recipient domain or email body
- **Job Title**: From subject line patterns
- **Application URL**: From email body (job board links)

### 3. Job Matching

Matches emails to tracked jobs by:
1. **Company name** (exact match)
2. **Job title** (substring match)
3. **Application URL** (URL match)

### 4. Status Update

For matched jobs:
- Updates status to `"applied"`
- Adds note with application date
- Logs update for confirmation

## Email Patterns Recognized

### Subject Lines

```
"Application for Senior Python Developer"
"Senior Developer - Job Application"
"Senior Developer Position"
"Application: Senior Python Developer"
```

### Company Extraction

```
careers@techcorp.com → "Techcorp"
jobs@acme-corp.com → "Acme-corp"
"application at Acme Corp" → "Acme Corp"
```

### URL Recognition

Job board domains recognized:
- greenhouse.io
- lever.co
- workday.com
- taleo.net
- careers.*
- jobs.*

## Scheduled Automation

### Add to Background Scheduler

Edit `src/app/background_scheduler.py`:

```python
from app.email_integration import (
    EmailIntegration,
    create_email_config_from_env
)

async def sync_job_applications():
    """Sync job applications from email."""
    config = create_email_config_from_env()
    if not config:
        return

    integration = EmailIntegration(config)
    stats = integration.auto_update_job_status(days=7)
    logger.info(f"Email sync: {stats['jobs_updated']} jobs updated")

# Add to scheduler
scheduler.add_job(
    sync_job_applications,
    trigger=IntervalTrigger(hours=6),
    id='email_sync',
    replace_existing=True
)
```

### Add to docker-compose.yml

Already included in worker service - just add environment variables:

```yaml
worker:
  environment:
    - EMAIL_ADDRESS=${EMAIL_ADDRESS}
    - EMAIL_PASSWORD=${EMAIL_PASSWORD}
    - IMAP_SERVER=${IMAP_SERVER}
```

## Troubleshooting

### Connection Failures

**Gmail "Less secure app" error**:
- Use App Password instead of account password
- Enable IMAP in Gmail settings

**Outlook authentication error**:
- Check if Modern Authentication is enabled
- Use app-specific password if 2FA enabled

### No Emails Found

**Wrong folder**:
- Gmail: Uses `[Gmail]/Sent Mail`
- Outlook: Uses `Sent Items`
- Custom: Check your email provider's folder names

**Date filter too restrictive**:
- Increase `--days` parameter
- Check email dates are within range

### Jobs Not Matching

**Company name mismatch**:
- Tracked job: "TechCorp Inc."
- Email domain: "techcorp.com"
- Solution: Update tracked job company name

**URL mismatch**:
- Job tracked via aggregator (Indeed/LinkedIn)
- Email sent to direct company URL
- Solution: Add direct URL to job's `company_link` field

## Security Best Practices

1. **Use App Passwords**: Never use your main account password
2. **Secure .env**: Add `.env` to `.gitignore` (already done)
3. **Rotate Credentials**: Change passwords periodically
4. **Read-Only Access**: Email integration only reads sent folder
5. **Local Processing**: Email content processed locally, not sent to AI

## API Reference

### EmailConfig

```python
@dataclass
class EmailConfig:
    imap_server: str          # IMAP server hostname
    email_address: str        # Your email address
    password: str             # Email password or app password
    port: int = 993          # IMAP port (default: 993 for SSL)
    use_ssl: bool = True     # Use SSL/TLS encryption
    folder: str = "INBOX"    # Folder to monitor (not used currently)
```

### ParsedEmail

```python
@dataclass
class ParsedEmail:
    subject: str                      # Email subject
    from_addr: str                    # Sender address
    to_addr: str                      # Recipient address
    date: datetime                    # Send date
    body: str                         # Email body text
    company_name: Optional[str]       # Extracted company name
    job_title: Optional[str]          # Extracted job title
    application_url: Optional[str]    # Extracted application URL
```

### EmailIntegration

```python
class EmailIntegration:
    def connect(self) -> bool:
        """Connect to email server."""

    def disconnect(self):
        """Disconnect from email server."""

    def fetch_recent_sent_emails(self, days: int = 7) -> List[ParsedEmail]:
        """Fetch recent sent emails."""

    def match_emails_to_jobs(
        self, emails: List[ParsedEmail]
    ) -> List[Tuple[ParsedEmail, Optional[str]]]:
        """Match emails to tracked jobs."""

    def auto_update_job_status(self, days: int = 7) -> Dict[str, int]:
        """Auto-update job status from emails."""
```

## Limitations

- **Sent emails only**: Does not monitor inbox (received emails)
- **Recent only**: Fetches emails from last N days (default: 7)
- **Best-effort matching**: May not match all emails to jobs
- **IMAP only**: Requires IMAP access (most providers support it)
- **Text parsing**: May miss jobs with unusual email formats

## Future Enhancements

- [ ] Inbox monitoring for interview invitations
- [ ] Parse rejection emails and auto-update status
- [ ] Email templates for job applications
- [ ] Bulk email sending for outreach
- [ ] Rich HTML email composition
- [ ] Attachment handling (cover letters, resumes)
- [ ] OAuth authentication support
- [ ] Exchange/EWS protocol support

## Related Documentation

- [Job Tracking](PROVIDERS.md) - Job tracking system
- [Background Tasks](../src/app/background_scheduler.py) - Scheduled automation
- [Configuration](PERSONAL_CONFIG_GUIDE.md) - Environment setup
