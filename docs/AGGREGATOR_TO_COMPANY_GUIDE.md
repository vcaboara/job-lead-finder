# Aggregator-to-Company Workflow Guide

## Quick Start

Use job aggregators (RemoteOK, Remotive) for **discovery**, then find **direct company links** for applications.

**Why?** Aggregators have broad coverage but direct applications through company ATSes get better visibility.

## Job Tracking

Every job is automatically tracked with states: `new`, `applied`, `interviewing`, `rejected`, `offer`, `hidden`.

## Key API Endpoints

### Track & Manage Jobs
- `GET /api/jobs/tracked?status=applied` - List jobs by status
- `POST /api/jobs/{job_id}/status` - Update status: `{"status": "applied", "notes": "..."}`
- `POST /api/jobs/{job_id}/hide` - Hide unwanted jobs from future searches

### Find Company Links
- `POST /api/jobs/find-company-link/{job_id}` - Auto-discover direct career page from aggregator listing
- `POST /api/jobs/{job_id}/company-link` - Manually set: `{"company_link": "https://..."}`

### Generate Cover Letters
- `POST /api/jobs/{job_id}/cover-letter` - Create custom cover letter
  ```json
  {
    "job_description": "Full job posting text...",
    "resume_text": "Your resume..."
  }
  ```

## Workflow Example

1. **Search** for jobs (auto-tracked as "new")
2. **Find company link**: `POST /api/jobs/find-company-link/{job_id}`
3. **Generate cover letter**: `POST /api/jobs/{job_id}/cover-letter`
4. **Apply** through company career page
5. **Update status**: `POST /api/jobs/{job_id}/status` with `"applied"`

## Troubleshooting

**"No company link found"** - Aggregator job may not have enough info, or company doesn't have public careers page. Manually set link if known.

**"Invalid job_id"** - Job wasn't tracked yet. Search/view it first to create tracking entry.

**Cover letter generic** - Provide full job description text, not just summary. Include your complete resume for personalization.

## Configuration

- **UI**: Set industry profile (ESG, Tech, Finance, etc.) in web interface
- **API**: `GET /api/job-config` to view, `POST /api/job-config/search` to update
- **File**: Edit `config.json` directly for advanced settings
