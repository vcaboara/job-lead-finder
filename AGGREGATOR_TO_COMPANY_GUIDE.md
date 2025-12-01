# Using Aggregators to Find Direct Company Links

## Overview

This guide explains how to use job aggregators (RemoteOK, Remotive) for **discovery** while finding **direct company career page links** for applications. This hybrid approach gives you the best of both worlds:

- ✅ **Broad discovery** from aggregators (thousands of jobs indexed)
- ✅ **Direct applications** through company career pages (avoid aggregator friction)
- ✅ **Better hiring manager visibility** (applications come directly from company ATS)
- ✅ **Access to full job descriptions** for custom cover letters

## Why This Approach?

### The Problem with Pure Strategies

**Pure Aggregator Approach (RemoteOK/Remotive only):**
- ❌ Applications go through aggregator, not directly to company
- ❌ Hiring managers may not see aggregator applications promptly
- ❌ Missing company-specific application questions
- ❌ No direct company ATS tracking

**Pure Web Search Approach (Gemini/DuckDuckGo only):**
- ❌ Hallucinates fake job URLs (especially Microsoft, NVIDIA)
- ❌ Returns Google redirect URLs (vertexaisearch.cloud.google.com)
- ❌ Inconsistent results (0-300 jobs randomly)
- ❌ Soft-404 issues (links return HTTP 200 but show error pages)

**Pure Curated List Approach (Industry Profiles only):**
- ❌ Limited to companies you already know about
- ❌ No discovery of new/unknown companies
- ❌ Misses startups and smaller firms

### The Hybrid Solution

**Use Aggregators for Discovery → Find Direct Company Links for Application**

1. **Discover** jobs on RemoteOK/Remotive (reliable, comprehensive indexing)
2. **Extract** company name from aggregator listing
3. **Search** for direct company career page using CompanyJobs provider
4. **Apply** through company's ATS (Greenhouse, Lever, Workday, etc.)

## How It Works

### Job Tracking System

The system now automatically tracks every job you see with these states:

| Status           | Description                       |
| ---------------- | --------------------------------- |
| **New**          | Just discovered, not yet reviewed |
| **Applied**      | Application submitted             |
| **Interviewing** | In interview process              |
| **Rejected**     | Not selected / declined           |
| **Offer**        | Received offer                    |
| **Hidden**       | Don't want to see this job again  |

### Finding Direct Company Links

When you find a job on RemoteOK/Remotive, use the **"Find Direct Company Link"** feature:

```
Aggregator Job:
  Title: Senior Python Engineer
  Company: Acme Corp
  Link: https://remoteok.com/remote-jobs/123456

→ Click "Find Direct Company Link"

System searches for:
  "Senior Python Engineer at Acme Corp"

Returns:
  Company Link: https://jobs.acmecorp.com/careers/positions/456789
  Source: CompanyJobs (direct from company website)
```

### API Endpoints

**Track Job Status:**
```bash
POST /api/jobs/{job_id}/status
{
  "status": "applied",
  "notes": "Applied 2025-11-30, sent custom cover letter"
}
```

**Hide Unwanted Jobs:**
```bash
POST /api/jobs/{job_id}/hide
```

**Find Direct Company Link:**
```bash
POST /api/jobs/find-company-link/{job_id}

Response:
{
  "found": true,
  "company_link": "https://careers.company.com/job/12345",
  "job": { ... },
  "message": "Found direct link at Acme Corp"
}
```

**Generate Custom Cover Letter:**
```bash
POST /api/jobs/{job_id}/cover-letter
{
  "job_description": "Full job description text...",
  "resume_text": "Your resume (optional, uses resume.txt if omitted)"
}

Response:
{
  "cover_letter": "Dear Hiring Manager...",
  "job_title": "Senior Python Engineer",
  "company": "Acme Corp"
}
```

**Get All Tracked Jobs:**
```bash
GET /api/jobs/tracked?status=applied,interviewing&include_hidden=false

Response:
{
  "jobs": [
    {
      "job_id": "abc123def456",
      "title": "Senior Python Engineer",
      "company": "Acme Corp",
      "status": "applied",
      "notes": "Applied 2025-11-30",
      "company_link": "https://careers.acmecorp.com/456789",
      "applied_date": "2025-11-30T10:30:00Z",
      "first_seen": "2025-11-29T15:20:00Z",
      "last_updated": "2025-11-30T10:30:00Z"
    }
  ],
  "count": 1
}
```

## Workflow Example

### 1. Search with Aggregators Enabled

```bash
# In Web UI:
# - Enable RemoteOK and Remotive in Providers tab
# - Disable CompanyJobs if you only want aggregator discovery
# - Search for "remote python developer"

# Results include jobs from RemoteOK and Remotive
```

### 2. Review Results

Each job card shows:
- Title, Company, Location
- Job summary
- Score (if resume provided)
- Aggregator link (RemoteOK/Remotive)
- Status: "New"

### 3. Find Direct Company Link

For jobs you're interested in:
1. Click **"Find Direct Company Link"** button
2. System searches company's career page
3. Direct link is found and saved automatically
4. Both aggregator URL and company URL are now available

### 4. Generate Custom Cover Letter

1. Click **"Generate Cover Letter"** button
2. System uses:
   - Job description from aggregator
   - Your resume (from resume.txt)
   - Gemini AI to customize
3. Copy cover letter to clipboard
4. Use in company application

### 5. Track Application Progress

1. Update status to **"Applied"** after submitting
2. Add notes: interview dates, contacts, follow-ups
3. Mark as **"Interviewing"** when you get a response
4. Mark as **"Rejected"** or **"Offer"** based on outcome

### 6. Hide Unwanted Jobs

For jobs you're not interested in:
1. Click **"Hide"** button
2. Job won't appear in future searches
3. Review hidden jobs with `GET /api/jobs/tracked?include_hidden=true`

## Data Persistence

All job tracking data is stored in `job_tracking.json`:

```json
{
  "jobs": {
    "abc123def456": {
      "job_id": "abc123def456",
      "title": "Senior Python Engineer",
      "company": "Acme Corp",
      "location": "Remote",
      "summary": "We are looking for...",
      "link": "https://remoteok.com/remote-jobs/123456",
      "source": "RemoteOK",
      "status": "applied",
      "notes": "Applied 2025-11-30, recruiter: jane@acme.com",
      "company_link": "https://careers.acmecorp.com/456789",
      "applied_date": "2025-11-30T10:30:00Z",
      "first_seen": "2025-11-29T15:20:00Z",
      "last_updated": "2025-11-30T10:30:00Z"
    }
  },
  "last_updated": "2025-11-30T10:30:00Z"
}
```

**Important:** Add `job_tracking.json` to `.gitignore` to keep your job search data private!

## Best Practices

### For Discovery

1. **Enable Multiple Aggregators**: RemoteOK + Remotive for maximum coverage
2. **Use Broad Search Terms**: "python engineer" not "Senior Python Django Developer with Kubernetes"
3. **Set High Result Counts**: Request 20-50 jobs to account for filtering
4. **Review Daily**: New jobs posted frequently, early applications help

### For Applications

1. **Always Find Direct Links**: Better chance of being seen by hiring managers
2. **Customize Cover Letters**: Use the job description to highlight relevant experience
3. **Track Everything**: Notes help you remember details in interviews
4. **Update Status Promptly**: Keep your pipeline organized

### For Follow-ups

1. **Use Notes Field**: Store recruiter contacts, interview dates, technical topics
2. **Filter by Status**: `GET /api/jobs/tracked?status=interviewing` shows active interviews
3. **Review Rejected Jobs**: Learn patterns about what didn't work

## Technical Details

### Job ID Generation

Jobs are identified by hashing their link:
- **Primary**: SHA256 hash of job URL (first 16 chars)
- **Fallback**: SHA256 hash of `company::title` if no URL

This ensures the same job from multiple searches is tracked once.

### Hidden Job Filtering

During search, the system:
1. Fetches jobs from providers
2. Validates links (soft-404 detection, status codes)
3. Filters blocked sites/employers
4. **NEW:** Checks job_tracking.json for hidden jobs
5. Excludes hidden jobs from results
6. Automatically tracks new jobs as "new" status

### Company Link Discovery

The `POST /api/jobs/find-company-link/{job_id}` endpoint:
1. Gets job data from tracking database
2. Extracts company name
3. Searches using CompanyJobs provider (Gemini + google_search)
4. Filters results to exact company match
5. Returns first direct company career page link
6. Automatically saves to job tracking

**Note:** CompanyJobs may hallucinate or return Google redirects. Verify links before applying!

## Troubleshooting

### "No direct company links found"

**Causes:**
- Company doesn't have public career page
- Company uses only aggregators for hiring
- Gemini couldn't find the right page
- Company name mismatch (e.g., "Acme Corp" vs "Acme Corporation")

**Solutions:**
1. Search company website manually
2. Check LinkedIn company page for "Jobs" tab
3. Google: `site:company.com careers`
4. Use aggregator link as fallback

### "Found link but it's another aggregator"

**Causes:**
- CompanyJobs filtering missed it (new aggregator site)
- Company redirects to aggregator

**Solutions:**
- Add aggregator to blocked sites
- Report issue (we'll add to filter list)

### "Cover letter generation failed"

**Causes:**
- No `GEMINI_API_KEY` in environment
- Gemini API quota exceeded
- No resume.txt file

**Solutions:**
1. Set `GEMINI_API_KEY` in `.env`
2. Wait for quota reset (250 requests/day free tier)
3. Upload resume via UI or create `resume.txt`

## Example Workflow: ESG Company Search

```bash
# 1. Configure ESG industry profile
#    Web UI → Configuration → Industry → Select "ESG & Sustainability"

# 2. Enable aggregators for discovery
#    Web UI → Configuration → Providers → Enable RemoteOK, Remotive

# 3. Search for sustainability roles
#    Query: "climate tech renewable energy sustainability"
#    Count: 20

# 4. Results include:
#    - Jobs from RemoteOK/Remotive (aggregators)
#    - Jobs from CompanyJobs (direct company links)

# 5. For each interesting aggregator job:
#    a. Click "Find Direct Company Link"
#    b. System searches: "Climate Tech Engineer at Tesla Energy"
#    c. Returns: https://www.tesla.com/careers/search/job/12345
#    d. Automatically saved to tracking

# 6. Generate custom cover letter:
#    a. Click "Generate Cover Letter"
#    b. System uses job description + resume
#    c. Gemini creates customized letter
#    d. Copy and paste into application

# 7. Track application:
#    a. Update status to "Applied"
#    b. Add note: "Applied 2025-11-30, emphasized solar experience"
#    c. Set reminder to follow up in 1 week
```

## Future Enhancements

**Potential additions** (not yet implemented):

- [ ] **UI Components**: Status dropdown, hide button, find link button on job cards
- [ ] **Bulk Operations**: Hide all jobs from specific company
- [ ] **Export**: Download tracked jobs as CSV
- [ ] **Calendar Integration**: Add interview dates to Google Calendar
- [ ] **Email Notifications**: Remind about follow-ups
- [ ] **Application Templates**: Save cover letter templates
- [ ] **Company Research**: Auto-fetch company info (funding, size, culture)
- [ ] **Salary Data**: Integrate Glassdoor/Levels.fyi data

## Learning MCP Development

As discussed, building **custom MCP servers** for direct ATS integration (Greenhouse, Lever, Workday) would be an excellent way to:

1. **Understand LLM Tool Calling**: How Gemini uses JSON schemas to invoke functions
2. **Learn MCP Protocol**: Server/client architecture, transport layers
3. **Practice API Integration**: Real-world ATS APIs (OAuth, pagination, rate limiting)
4. **Debug AI Behavior**: See when tools fail and how to make them robust
5. **Build Useful Tools**: Direct company integrations > web scraping

**Recommended starting point:**
- Build a **Greenhouse MCP server** (many companies use Greenhouse ATS)
- Their API is well-documented: https://developers.greenhouse.io/
- Supports job search by company, department, location
- Returns structured job data (no parsing needed)

This would eliminate aggregators AND web search hallucinations entirely!

---

## Summary

**The hybrid approach (Aggregators → Company Links) solves the discovery problem:**

| Approach               | Discovery   | Reliability | Direct Application |
| ---------------------- | ----------- | ----------- | ------------------ |
| **Aggregators Only**   | ✅ Excellent | ✅ Very Good | ❌ No               |
| **Web Search Only**    | ✅ Good      | ❌ Poor      | ✅ Yes              |
| **Curated Lists Only** | ❌ Limited   | ✅ Excellent | ✅ Yes              |
| **Hybrid (This)**      | ✅ Excellent | ✅ Good      | ✅ Yes              |

**Next steps:**
1. Use aggregators for broad discovery
2. Find direct company links for serious applications
3. Track everything to stay organized
4. Consider building custom MCP servers for ultimate reliability

Good luck with your job search! 🚀
