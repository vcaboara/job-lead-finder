# Email Webhook Setup Guide

This guide walks you through setting up inbound email integration for automated job tracking via SendGrid Inbound Parse.

## Overview

The email webhook integration allows you to:
- **Forward job alerts** from LinkedIn, Indeed, Monster to automatically create tracked jobs
- **Forward application confirmations** from Workday, Greenhouse, Lever to update job status
- **Forward recruiter emails** to track high-priority opportunities
- **Build ML training data** from diverse job listing formats

## Architecture

```
┌─────────────────┐
│  Your Email     │
│  (Gmail, etc.)  │
└────────┬────────┘
         │ Forwarding rule
         ▼
┌─────────────────┐
│  SendGrid       │ ← Inbound Parse webhook
│  Inbound Parse  │
└────────┬────────┘
         │ POST /api/email/inbound
         ▼
┌─────────────────┐
│  JobForge       │
│  Email Parser   │
│  Job Tracker    │
└─────────────────┘
```

## Prerequisites

1. **SendGrid Account** (free tier works for MVP)
   - Sign up at https://sendgrid.com/
   - Free tier: 100 emails/day
   
2. **Domain or Subdomain** for receiving emails
   - Option 1: Use SendGrid's domain (e.g., `jobforge.sendgrid.net`)
   - Option 2: Configure your own subdomain (e.g., `email.jobforge.com`)

3. **JobForge Instance** with public URL
   - Running on Railway, Heroku, or other platform
   - HTTPS endpoint accessible (required by SendGrid)

## Setup Steps

### 1. Configure SendGrid Inbound Parse

#### Step 1: Log into SendGrid

1. Go to https://app.sendgrid.com/
2. Navigate to **Settings** → **Inbound Parse**

#### Step 2: Add Inbound Parse Webhook

1. Click **Add Host & URL**
2. Fill in the form:

   **Domain:**
   - If using SendGrid's domain: Select `sendgrid.net` from dropdown
   - If using your own: Enter your subdomain (e.g., `email.jobforge.com`)
   
   **Subdomain:** (optional if using SendGrid domain)
   - Leave blank for SendGrid domain
   - Or specify subdomain prefix
   
   **Destination URL:**
   ```
   https://your-jobforge-instance.railway.app/api/email/inbound
   ```
   
   **Check Spam:** ✓ Enabled (recommended)
   
   **Send Raw:** ✗ Disabled (we parse the body)

3. Click **Add**

#### Step 3: Verify DNS (if using custom domain)

If using your own domain, add MX record:

```
Type: MX
Host: email (or your subdomain)
Value: mx.sendgrid.net
Priority: 10
```

Wait for DNS propagation (usually 5-30 minutes).

### 2. Generate Your Forwarding Address

#### Option A: Via UI (once UI is implemented)

1. Go to JobForge settings
2. Click "Email Integration"
3. Click "Generate Forwarding Address"
4. Copy your unique address: `user-abc123@jobforge.sendgrid.net`

#### Option B: Via API

```bash
curl -X POST https://your-jobforge-instance.railway.app/api/email/setup \
  -H "Content-Type: application/json" \
  -d '{"user_id": "your-user-id"}'
```

Response:
```json
{
  "forwarding_address": "user-abc123@jobforge.sendgrid.net"
}
```

### 3. Set Up Email Forwarding Rules

Now configure your email client to forward job-related emails to your JobForge address.

#### Gmail Forwarding Rules

1. Go to **Settings** → **See all settings** → **Filters and Blocked Addresses**
2. Click **Create a new filter**

**For LinkedIn job alerts:**
```
From: jobs-noreply@linkedin.com
OR
From: jobs@linkedin.com
Subject: (jobs OR opportunities)
```
→ Forward to: `user-abc123@jobforge.sendgrid.net`

**For Indeed alerts:**
```
From: noreply@indeed.com
Subject: (job alert OR daily alert)
```
→ Forward to: `user-abc123@jobforge.sendgrid.net`

**For Workday confirmations:**
```
From: *@myworkdayjobs.com
Subject: application
```
→ Forward to: `user-abc123@jobforge.sendgrid.net`

**For Greenhouse confirmations:**
```
From: no-reply@greenhouse.io
Subject: application
```
→ Forward to: `user-abc123@jobforge.sendgrid.net`

**For recruiter outreach (careful with this one):**
```
Subject: opportunity
NOT from: (*@linkedin.com OR *@indeed.com OR *@myworkdayjobs.com)
```
→ Forward to: `user-abc123@jobforge.sendgrid.net`

#### Outlook/Office 365 Forwarding Rules

1. Go to **Settings** → **Mail** → **Rules**
2. Click **Add new rule**

Example rule:
```
IF:
  From contains "jobs@linkedin.com"
  OR Subject contains "job alert"
THEN:
  Forward to user-abc123@jobforge.sendgrid.net
```

### 4. Test the Integration

#### Send Test Email

Forward a job alert or send a test email to your forwarding address:

```bash
# Example test via SendGrid's test interface
curl -X POST https://your-jobforge-instance.railway.app/api/email/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user-abc123@jobforge.sendgrid.net",
    "from": "jobs@linkedin.com",
    "subject": "5 new jobs for Software Engineer",
    "text": "Here are jobs you might be interested in:\n\nSenior Software Engineer at Google\nhttps://www.linkedin.com/jobs/view/123456",
    "html": "<html>...</html>"
  }'
```

#### Check Stats

```bash
curl https://your-jobforge-instance.railway.app/api/email/stats?user_id=your-user-id
```

Response:
```json
{
  "forwarding_address": "user-abc123@jobforge.sendgrid.net",
  "emails_processed": 1,
  "last_email_at": "2024-12-11T10:30:00Z",
  "is_active": true
}
```

#### Verify Job Creation

Check your JobForge dashboard:
- New jobs from LinkedIn/Indeed alerts should appear in "New" status
- Application confirmations should update existing jobs to "Applied" status
- Recruiter emails should appear with "HIGH PRIORITY" note

## Email Classification

JobForge automatically classifies emails into three types:

### 1. Job Listings
**Sources:** LinkedIn, Indeed, Monster, Glassdoor, etc.

**Actions:**
- Creates new job in "New" status
- Extracts: company name, job title, URL, description
- Confidence threshold: >50%

**Example patterns:**
- "10 new jobs matching..."
- "Daily job alert"
- "Jobs you might be interested in"

### 2. Application Confirmations
**Sources:** Workday, Greenhouse, Lever, Jobvite, etc.

**Actions:**
- Matches to existing job by URL or company+title
- Updates status to "Applied"
- Adds confirmation timestamp to notes
- Creates new job in "Applied" status if no match

**Example patterns:**
- "Application received"
- "Thank you for applying"
- "We received your application"

### 3. Recruiter Outreach
**Sources:** Direct emails from recruiters

**Actions:**
- Creates new job with "HIGH PRIORITY" flag
- Adds recruiter contact info to notes
- Marks for immediate review

**Example patterns:**
- "I came across your profile"
- "Interested in discussing"
- "Opportunity that might interest you"

## Troubleshooting

### Emails Not Arriving

1. **Check SendGrid logs:**
   - Go to SendGrid dashboard → Activity
   - Look for inbound parse events
   - Check for errors

2. **Verify DNS:**
   ```bash
   nslookup -type=mx email.jobforge.com
   ```
   Should return `mx.sendgrid.net`

3. **Check webhook URL:**
   - Must be HTTPS
   - Must be publicly accessible
   - Test with `curl -X POST https://your-url/api/email/inbound`

### Emails Arriving But Not Processed

1. **Check application logs:**
   ```bash
   # View recent logs
   railway logs
   # or
   heroku logs --tail
   ```

2. **Verify forwarding address:**
   ```bash
   curl https://your-jobforge-instance.railway.app/api/email/stats?user_id=your-user-id
   ```

3. **Test email classification:**
   - Check confidence scores in logs
   - Verify email patterns match expected format

### Jobs Not Being Created

1. **Check confidence threshold:**
   - Default minimum: 0.5 (50%)
   - Low confidence emails are skipped
   - Check logs for "Low confidence" messages

2. **Verify email format:**
   - Compare with sample .eml files in `tests/fixtures/emails/`
   - Check that URLs are being extracted

## Security Considerations

1. **Forwarding Address Security:**
   - Addresses are randomly generated (e.g., `user-abc123`)
   - Not guessable without access to your account
   - Can be disabled anytime

2. **Email Privacy:**
   - Emails are stored locally in `data/inbox/`
   - Only metadata is extracted for job tracking
   - Original email content is preserved

3. **Spam Protection:**
   - SendGrid spam filtering is enabled
   - Only emails matching your forwarding rules are processed
   - Unknown email types are skipped

## Advanced Configuration

### Environment Variables

```bash
# .env file
SENDGRID_DOMAIN=jobforge.sendgrid.net  # Your SendGrid domain
```

### Custom Domain Setup

For production, use your own domain:

1. Add DNS records:
   ```
   Type: MX
   Host: email
   Value: mx.sendgrid.net
   Priority: 10
   ```

2. Update `.env`:
   ```
   SENDGRID_DOMAIN=email.yourdomain.com
   ```

3. Update SendGrid Inbound Parse webhook with new domain

### Rate Limiting

SendGrid free tier: 100 emails/day

For higher volume:
- Upgrade SendGrid plan
- Or implement email queuing
- Or use AWS SES (pay-per-email)

## API Reference

### POST /api/email/setup
Generate forwarding address for user.

**Request:**
```bash
curl -X POST /api/email/setup?user_id=user123
```

**Response:**
```json
{
  "forwarding_address": "user-abc123@jobforge.sendgrid.net"
}
```

### GET /api/email/stats
Get email statistics for user.

**Request:**
```bash
curl /api/email/stats?user_id=user123
```

**Response:**
```json
{
  "forwarding_address": "user-abc123@jobforge.sendgrid.net",
  "emails_processed": 42,
  "last_email_at": "2024-12-11T10:30:00Z",
  "is_active": true
}
```

### POST /api/email/inbound
Webhook endpoint for SendGrid (internal use).

**Request:** SendGrid Inbound Parse format
**Response:** Processing result

## Support

For issues or questions:
1. Check logs: `railway logs` or `heroku logs`
2. Review test fixtures: `tests/fixtures/emails/*.eml`
3. Run tests: `pytest tests/test_email_*.py -v`
4. Open issue on GitHub

## Next Steps

Once email integration is working:
1. Monitor email classification accuracy
2. Adjust confidence thresholds if needed
3. Add more email patterns for other job boards
4. Implement ML training data pipeline
5. Add UI for managing forwarding rules

---

**Last Updated:** 2024-12-11
**Version:** 1.0
