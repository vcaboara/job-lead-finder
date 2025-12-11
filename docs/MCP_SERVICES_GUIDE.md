# MCP Services Guide

This project uses Model Context Protocol (MCP) servers to enhance AI capabilities.

## Available MCP Services

### 1. Vibe Check MCP (Port 3000)
- **Type**: Custom HTTP MCP Server
- **Purpose**: Code validation and quality checks
- **Configuration**: HTTP endpoint at http://localhost:3000
- **Status**: ✅ Fully configured

### 2. Brave Search MCP (stdio)
- **Type**: Official MCP Server (stdio-based)
- **Purpose**: High-quality search via Brave API
- **Package**: `@modelcontextprotocol/server-brave-search`
- **Requirements**: `BRAVE_API_KEY` environment variable
- **Status**: ⚠️ Requires stdio configuration (not HTTP)

### 3. Fetch MCP (stdio)
- **Type**: Official MCP Server (stdio-based)
- **Purpose**: Standardized web scraping
- **Package**: `@modelcontextprotocol/server-fetch`
- **Status**: ⚠️ Requires stdio configuration (not HTTP)

## Important: MCP Protocol Types

### HTTP-based MCP (Custom Servers)
These servers expose HTTP endpoints and can be accessed via URL:
- **vibe-check-mcp**: Custom implementation with HTTP API

### stdio-based MCP (Official Servers)
These servers communicate via standard input/output:
- **brave-search-mcp**: Official MCP server
- **fetch-mcp**: Official MCP server

## Configuration for AI Assistants

### For Claude Desktop (Cline/Roo Code)

Edit `~/.config/claude-desktop/config.json` (Linux/Mac) or `%APPDATA%\Claude\config.json` (Windows):

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "brave-search-mcp"
      ],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key_here"
      }
    },
    "fetch": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "fetch-mcp"
      ]
    }
  }
}
```

### For VS Code (GitHub Copilot)

MCP support in VS Code is limited. The official MCP servers (brave-search, fetch) use stdio and won't work with the HTTP configuration in `.vscode/settings.json`.

**Alternative**: Use the Python tools instead:
- `tools/search_engine.py` for search
- `tools/web_scraper.py` for web scraping

## Docker Compose Configuration

### Current Configuration (Needs Update)

The current docker-compose.yml runs MCP servers as long-running services with port mappings:

```yaml
brave-search-mcp:
  image: node:20-alpine
  ports:
    - "3002:3002"  # ⚠️ Won't work - MCP uses stdio, not HTTP
```

### Recommended Configuration

MCP servers should be invoked on-demand, not as long-running services:

```yaml
# Remove from default 'docker compose up' by using profiles
brave-search-mcp:
  image: node:20-alpine
  profiles: ["tools"]  # Only start when explicitly requested
  environment:
    - BRAVE_API_KEY=${BRAVE_API_KEY}
  working_dir: /app
  command: npx -y @modelcontextprotocol/server-brave-search
  stdin_open: true
  tty: true
```

## Usage Examples

### Using Brave Search MCP

```bash
# Start the service for stdio communication
docker compose run --rm brave-search-mcp

# Or use directly with npx (if Node.js installed locally)
npx @modelcontextprotocol/server-brave-search
```

### Using Fetch MCP

```bash
# Start the service for stdio communication
docker compose run --rm fetch-mcp

# Or use directly with npx
npx @modelcontextprotocol/server-fetch
```

### Using Python Tools (Alternative)

For immediate use without MCP configuration:

```bash
# Search with Brave API (via Python)
python tools/search_engine.py "your search query"

# Scrape websites
python tools/web_scraper.py https://example.com
```

## API Keys Required

### BRAVE_API_KEY
- **Purpose**: Powers brave-search-mcp
- **Get Key**: https://brave.com/search/api/
- **Free Tier**: 2,000 queries/month
- **Add to**: `.env` file

```bash
# In .env
BRAVE_API_KEY=your_brave_api_key_here
```

## Troubleshooting

### MCP Server Not Responding

**Issue**: MCP servers show as running but don't respond

**Cause**: Official MCP servers use stdio, not HTTP. Port mappings don't work.

**Solution**: 
1. Use `docker compose run` instead of `docker compose up`
2. Configure in Claude Desktop config with stdio
3. Or use Python tools as alternative

### Port Already in Use

**Issue**: Ports 3002 or 3003 conflict

**Cause**: Previous services not stopped

**Solution**:
```bash
docker compose down
docker compose up -d
```

### No BRAVE_API_KEY

**Issue**: Brave Search MCP fails with auth error

**Solution**: 
1. Get API key from https://brave.com/search/api/
2. Add to `.env`: `BRAVE_API_KEY=your_key`
3. Restart services: `docker compose restart brave-search-mcp`

## Next Steps

1. **Test MCP Integration**: Configure Claude Desktop with stdio MCP servers
2. **Update Docker Config**: Add profiles to prevent auto-start
3. **Document Workflows**: Create examples of using MCP tools in AI workflows
4. **Health Checks**: Add validation scripts for MCP connectivity

## References

- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Server Brave Search](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)
- [MCP Server Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- [Claude Desktop MCP Configuration](https://docs.anthropic.com/claude/docs/model-context-protocol)
