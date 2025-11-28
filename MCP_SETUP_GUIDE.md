# MCP Setup Guide for Docker Desktop

This guide walks you through setting up Model Context Protocol (MCP) servers for job searching using Docker Desktop.

## What is MCP?

Model Context Protocol (MCP) is a standardized interface that allows AI applications to connect to external data sources. Instead of relying on web search APIs (like Gemini's google_search), MCP provides direct, structured access to job boards like LinkedIn, Indeed, and GitHub.

## Benefits of MCP Approach

- **Multiple Data Sources**: Aggregate jobs from LinkedIn, Indeed, GitHub simultaneously
- **Structured Data**: Get clean, parsed job data (no web scraping needed)
- **Higher Rate Limits**: Each MCP has its own rate limits
- **Better Quality**: Direct from job boards, not search engine results
- **Reliability**: No quota exhaustion like Gemini free tier (250 req/day)

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (included with Docker Desktop)
3. Account credentials for job boards (LinkedIn, etc.)

## Setup Steps

### 1. Configure Environment Variables

Copy the example MCP environment file:

```powershell
Copy-Item .env.mcp.example .env.mcp
```

Edit `.env.mcp` with your credentials:

```env
# LinkedIn credentials (required for LinkedIn MCP)
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# OR use session cookie (more secure)
LINKEDIN_SESSION_COOKIE=your_session_cookie_here

# Indeed API key (optional - public search may work without it)
INDEED_API_KEY=

# GitHub token (optional - for higher rate limits)
GITHUB_TOKEN=ghp_your_token_here
```

**Security Note**: Never commit `.env.mcp` to git. It's already in `.gitignore`.

### 2. Start MCP Servers

Using Docker Compose:

```powershell
docker-compose -f docker-compose.mcp.yml up -d
```

This starts three MCP servers:
- **LinkedIn MCP**: `http://localhost:3000`
- **Indeed MCP**: `http://localhost:3001`
- **GitHub Jobs MCP**: `http://localhost:3002`

### 3. Verify MCP Servers are Running

Check health status:

```powershell
# Check all containers
docker-compose -f docker-compose.mcp.yml ps

# Test LinkedIn MCP
curl http://localhost:3000/health

# Test Indeed MCP
curl http://localhost:3001/health

# Test GitHub MCP
curl http://localhost:3002/health
```

Expected response: `{"status": "ok"}` or similar

### 4. View MCP Logs

If any MCP fails to start:

```powershell
# View all logs
docker-compose -f docker-compose.mcp.yml logs

# View specific MCP logs
docker-compose -f docker-compose.mcp.yml logs linkedin-mcp
docker-compose -f docker-compose.mcp.yml logs indeed-mcp
docker-compose -f docker-compose.mcp.yml logs github-jobs-mcp
```

### 5. Using MCPs in Docker Desktop UI

Docker Desktop provides a built-in MCP interface:

1. Open **Docker Desktop**
2. Go to **Containers** tab
3. You should see three running containers:
   - `linkedin-mcp`
   - `indeed-mcp`
   - `github-jobs-mcp`
4. Click on each to view logs, stats, and configuration

## How the Application Uses MCPs

The job search application now aggregates jobs from all available MCPs:

1. **User searches** for "python developer"
2. **Application queries** each MCP in parallel:
   - LinkedIn MCP returns 5 jobs
   - Indeed MCP returns 5 jobs
   - GitHub MCP returns 5 jobs
3. **Deduplication** removes duplicate job postings
4. **Filtering** applies your block list and quality checks
5. **Results** display with source attribution (LinkedIn, Indeed, GitHub)

## Configuration Options

### Jobs Per MCP

In `.env.mcp`, set how many jobs to request from each source:

```env
JOBS_PER_MCP=5
```

### Location Filtering

```env
DEFAULT_LOCATION=United States
```

### Enable/Disable Specific MCPs

Edit `docker-compose.mcp.yml` to comment out MCPs you don't want:

```yaml
# services:
#   # Disable LinkedIn MCP
#   # linkedin-mcp:
#   #   ...
```

## Troubleshooting

### LinkedIn MCP Authentication Issues

If LinkedIn MCP fails to authenticate:

1. **Use session cookie instead of password**:
   - Log into LinkedIn in your browser
   - Open DevTools (F12) → Application → Cookies
   - Copy the `li_at` cookie value
   - Set `LINKEDIN_SESSION_COOKIE=<cookie_value>` in `.env.mcp`

2. **Check for 2FA**:
   - LinkedIn 2FA may block password authentication
   - Session cookie method bypasses this

### MCP Server Not Responding

```powershell
# Restart specific MCP
docker-compose -f docker-compose.mcp.yml restart linkedin-mcp

# Restart all MCPs
docker-compose -f docker-compose.mcp.yml restart
```

### Rate Limiting

If you hit rate limits:

1. **LinkedIn**: Session cookie auth usually has higher limits
2. **GitHub**: Use a personal access token (`GITHUB_TOKEN`)
3. **Indeed**: API key may provide higher limits

### Viewing Real-Time Logs

```powershell
# Follow logs for all MCPs
docker-compose -f docker-compose.mcp.yml logs -f

# Follow logs for specific MCP
docker-compose -f docker-compose.mcp.yml logs -f linkedin-mcp
```

## Stopping MCP Servers

```powershell
# Stop all MCP servers
docker-compose -f docker-compose.mcp.yml down

# Stop and remove volumes
docker-compose -f docker-compose.mcp.yml down -v
```

## Integration with Main Application

The main job search app automatically detects and uses available MCPs:

1. **Fallback behavior**: If no MCPs are available, falls back to Gemini (if configured)
2. **Partial availability**: Uses whatever MCPs are running (e.g., only LinkedIn)
3. **Automatic detection**: Health checks determine which MCPs to query

## Next Steps

1. Start the main application: `docker-compose up`
2. Navigate to `http://localhost:8080`
3. Search for jobs - results will come from all available MCPs
4. Jobs will be tagged with their source (LinkedIn, Indeed, GitHub)

## Custom MCP Servers

To add custom job board MCPs:

1. Add service to `docker-compose.mcp.yml`
2. Create provider class in `src/app/mcp_providers.py`
3. Add to `MCPAggregator` providers list

Example:

```python
class CustomJobBoardMCP(MCPProvider):
    def __init__(self):
        super().__init__("CustomBoard")
        self.mcp_server_url = os.getenv("CUSTOM_MCP_URL", "http://localhost:3003")
    # ... implement search_jobs and is_available
```

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Docker Desktop MCP Support](https://docs.docker.com/desktop/features/mcp/)
- [LinkedIn MCP Documentation](https://github.com/modelcontextprotocol/servers/tree/main/src/linkedin)
- [GitHub MCP Documentation](https://github.com/modelcontextprotocol/servers/tree/main/src/github)

## Support

For issues with:
- **MCP Setup**: Check Docker Desktop logs and MCP server documentation
- **Job Search**: Check application logs in `logs/` folder
- **Authentication**: Refer to job board API documentation
