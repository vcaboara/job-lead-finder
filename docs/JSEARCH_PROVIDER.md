# JSearch Provider

The JSearch provider enables automated job discovery using the [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) on RapidAPI. JSearch aggregates real-time job listings from multiple sources including Indeed, LinkedIn, Glassdoor, and more.

## Features

- **Real-time job data** from multiple job boards
- **Automatic company extraction** from job listings
- **Tech stack detection** from job descriptions
- **Filtering options:**
  - Location (including remote-only)
  - Date posted (today, 3days, week, month)
  - Employment type (FULLTIME, CONTRACTOR, etc.)
- **Pagination** support for large result sets
- **Deduplication** of companies

## Setup

### 1. Get Your RapidAPI Key

1. Sign up at [RapidAPI](https://rapidapi.com)
2. Subscribe to [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
3. Copy your RapidAPI key

### 2. Add Key to Environment

Add your key to `.env` file:

```bash
RAPIDAPI_KEY=your_rapidapi_key_here
```

## Usage

### Command Line Test

Run the test script to try the provider:

```bash
# Basic search
python -m src.app.scripts.test_jsearch

# Custom search
python -m src.app.scripts.test_jsearch \
    --query "machine learning engineer" \
    --location "san francisco" \
    --limit 20 \
    --date-posted "3days"

# Remote jobs only
python -m src.app.scripts.test_jsearch \
    --query "full stack developer" \
    --remote-only \
    --limit 50
```

### Python API

```python
from src.app.discovery.providers import JSearchProvider

# Initialize provider (requires RAPIDAPI_KEY in environment)
provider = JSearchProvider()

# Discover companies
result = provider.discover_companies({
    "query": "python developer",
    "locations": ["remote", "new york"],
    "limit": 50,
    "date_posted": "week",
    "employment_types": ["FULLTIME"],
    "remote_jobs_only": False
})

print(f"Found {len(result.companies)} companies")

for company in result.companies:
    print(f"{company.name} - {company.website}")
    print(f"  Tech stack: {', '.join(company.tech_stack)}")
    print(f"  Locations: {', '.join(company.locations)}")
```

## Filter Options

### Query
Search query string (e.g., "python developer", "machine learning engineer")

### Locations
List of locations to search:
- `["remote"]` - Remote jobs only
- `["san francisco"]` - Specific city
- `["remote", "new york", "boston"]` - Multiple locations

### Limit
Maximum number of companies to return (default: 50, max: 1000)

### Date Posted
Filter by posting date:
- `"all"` - All time
- `"today"` - Posted today
- `"3days"` - Last 3 days
- `"week"` - Last week (default)
- `"month"` - Last month

### Employment Types
List of employment types:
- `"FULLTIME"` - Full-time positions
- `"CONTRACTOR"` - Contract positions
- `"PARTTIME"` - Part-time positions
- `"INTERN"` - Internships

### Remote Jobs Only
`True` to only return remote positions (boolean)

## Result Format

The provider returns a `DiscoveryResult` object containing:

```python
{
    "source": "jsearch",
    "companies": [
        {
            "name": "TechCorp Inc",
            "website": "https://techcorp.com",
            "careers_url": "https://techcorp.com/careers/apply/123",
            "industry": "tech",
            "size": "unknown",
            "locations": ["San Francisco"],
            "tech_stack": ["python", "aws", "docker"],
            "description": "...",
            "metadata": {
                "logo_url": "https://...",
                "job_title": "Senior Python Developer",
                "posted_date": "2024-01-15T10:30:00Z",
                "source_job_id": "job123"
            }
        }
    ],
    "total_found": 25,
    "timestamp": "2024-01-15T12:00:00Z",
    "metadata": {
        "query": "python developer in remote",
        "total_jobs_found": 25,
        "companies_returned": 25,
        "date_posted_filter": "week",
        "remote_only": False
    }
}
```

## Rate Limits

Rate limits depend on your RapidAPI subscription plan. Check your plan at [RapidAPI Dashboard](https://rapidapi.com/developer/billing).

## Supported Industries

Currently focuses on:
- Technology (TECH)
- Other (OTHER)

Industry detection will be expanded in future updates.

## Tech Stack Detection

The provider automatically extracts technologies mentioned in job descriptions and requirements:

- Languages: Python, JavaScript, TypeScript, Java, C++, Go, Rust
- Frameworks: React, Node.js
- Cloud: AWS, Azure, GCP
- DevOps: Docker, Kubernetes
- Databases: PostgreSQL, MongoDB, Redis
- Data: TensorFlow, PyTorch, Kafka

More technologies will be added based on usage patterns.

## Examples

### Find Remote Python Jobs

```python
result = provider.discover_companies({
    "query": "python developer",
    "locations": ["remote"],
    "limit": 30,
    "date_posted": "week",
    "remote_jobs_only": True
})
```

### Find Startups Hiring ML Engineers

```python
result = provider.discover_companies({
    "query": "machine learning engineer startup",
    "locations": ["san francisco", "new york"],
    "limit": 50,
    "date_posted": "3days"
})

# Filter for companies with AI/ML tech stack
ml_companies = [
    c for c in result.companies
    if any(tech in c.tech_stack for tech in ["tensorflow", "pytorch"])
]
```

### Track New Companies Daily

```python
from datetime import datetime

# Get today's new companies
result = provider.discover_companies({
    "query": "full stack developer",
    "locations": ["remote"],
    "date_posted": "today",
    "limit": 100
})

# Save to database or file
for company in result.companies:
    print(f"New: {company.name} - {company.careers_url}")
```

## Troubleshooting

### "RAPIDAPI_KEY environment variable is required"
- Make sure `RAPIDAPI_KEY` is in your `.env` file
- Verify the `.env` file is in the project root
- Try restarting your terminal/IDE

### "API error: 429 - Rate limit exceeded"
- You've hit your plan's rate limit
- Upgrade your plan or wait for limit reset
- Check [RapidAPI Dashboard](https://rapidapi.com/developer/billing)

### "No companies found"
- Try a broader search query
- Increase the date range (`"month"` instead of `"week"`)
- Remove location filters or try `["remote"]`

## Next Steps

1. **Integrate with Discovery Service** - Add to automated discovery pipeline
2. **Background Monitoring** - Set up scheduled discovery runs
3. **Company Database** - Save discovered companies to SQLite
4. **Notifications** - Alert when new companies are found

See [COMPANY_DISCOVERY_PLAN.md](../../../docs/COMPANY_DISCOVERY_PLAN.md) for the full roadmap.
