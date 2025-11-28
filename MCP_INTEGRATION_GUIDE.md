# MCP Integration Guide

## Current Status
The Gemini SDK includes `_mcp_utils` which suggests Model Context Protocol support is available. However, direct MCP integration for job search would require:

1. **LinkedIn MCP** - For accessing LinkedIn job postings
2. **DuckDuckGo MCP** - For web search capabilities
3. **Custom job board MCPs** - For specific platforms (Indeed, Dice, Monster, etc.)

## Why Current Approach Uses Gemini's google_search Tool
- Gemini 2.5 Flash has built-in `google_search` tool that can find real job postings
- The challenge is prompting it correctly to return specific job URLs (not career pages)
- We've enhanced the prompt to explicitly exclude generic pages

## Improved Filtering Strategy
The app now filters out:
- Generic career pages (`/careers`, `/jobs`, etc.)
- Job board search results
- 403/404 pages
- localhost links
- Pages without specific job IDs

## Future MCP Integration Options

### Option 1: LinkedIn MCP (if available)
```python
# Hypothetical integration
from mcp.linkedin import LinkedInJobSearchTool

linkedin_tool = LinkedInJobSearchTool(api_key=os.getenv("LINKEDIN_API_KEY"))
jobs = linkedin_tool.search(
    query="python developer remote",
    location="United States",
    limit=10
)
```

### Option 2: DuckDuckGo MCP
```python
# Hypothetical integration
from mcp.duckduckgo import DuckDuckGoSearchTool

ddg_tool = DuckDuckGoSearchTool()
results = ddg_tool.search(
    query="site:greenhouse.io OR site:lever.co python developer remote",
    limit=20
)
```

### Option 3: Job Board APIs
Direct integration with job board APIs would be more reliable:
- **Indeed API** - Requires partnership
- **LinkedIn Jobs API** - Requires LinkedIn Developer account
- **Dice API** - Available for developers
- **GitHub Jobs** - Free (but deprecated)
- **RemoteOK API** - Free for non-commercial use

## Recommended Next Steps

### Short Term (Immediate)
1. ✅ Enhanced Gemini prompt to avoid career pages
2. ✅ Improved link filtering
3. Test with different queries and adjust filters

### Medium Term
1. Add specific job board scrapers (using httpx + BeautifulSoup)
2. Implement retry logic when results are low quality
3. Add job board preference settings in UI

### Long Term
1. Investigate official MCP implementations for job platforms
2. Consider building custom MCPs for popular job boards
3. Add multi-source aggregation (combine Gemini + scrapers + APIs)

## Testing the Current Implementation
After rebuilding, test with queries like:
- "python remote developer with specific job postings"
- "senior software engineer [city] direct job links"
- Add negative keywords: "NOT /careers NOT /jobs"

The improved prompt and filtering should significantly reduce generic pages.
