# TODO: Brave Search MCP Integration

**Priority**: P2 (Enhancement)
**Complexity**: Low
**Estimated Time**: 1-2 hours

## Context

User discovered Brave Search API Free tier (2,000 requests/month):
- Screenshot: api.dashboard.search.brave.com/subscriptions
- Free tier includes: Web search, Goggles, News cluster, Videos, Images
- MCP server available for integration

## Tasks

### 1. Documentation Updates
- [ ] Add Brave Search to `docs/PROVIDERS.md`
  - Free tier details (2k req/month, $0.00)
  - Features: Web search, News, Videos, Images
  - API key setup instructions
  - Link to Brave Search API dashboard

- [ ] Update `docs/MCP_SERVICES.md` (if exists) or create
  - Brave Search MCP integration guide
  - Configuration example
  - Usage patterns for job search

### 2. Code Integration (Optional - Future Enhancement)
- [ ] Add Brave Search as discovery provider option
  - Similar to existing MCP providers
  - Use for company/job discovery
  - Potentially better than Google for fresh results

- [ ] Add to `src/app/mcp_providers.py` or separate module
  ```python
  class BraveSearchMCP(MCPProvider):
      """Brave Search provider via MCP."""
      # Free tier: 2k requests/month
      # Better privacy, no tracking
      # Good for company discovery
  ```

### 3. Configuration
- [ ] Add to `.env.example`:
  ```
  BRAVE_SEARCH_API_KEY=your_brave_api_key_here
  ```

- [ ] Add to `docker-compose.yml` MCP services section:
  ```yaml
  brave-search-mcp:
    # Configuration for Brave Search MCP
  ```

## Benefits

1. **Free tier**: 2k requests/month (generous for job search)
2. **Privacy**: No Google tracking
3. **Fresh results**: Good for discovering new companies/jobs
4. **MCP integration**: Easy to add via existing infrastructure

## Related

- PR #98: MCP services setup (Brave Search + Fetch)
- `docs/PROVIDERS.md`: Provider documentation
- `.github/copilot-instructions.md`: TODOs section

## References

- Brave Search API: https://api.dashboard.search.brave.com/
- Free tier: 1 request/second, 2,000 requests/month
- Available features: Web search, Goggles, News, Videos, Images
