# Dashboard Service Status Resolution

## Issue Summary
Dashboard showed monitoring services as "Stopped" despite Docker containers running and responding to requests.

## Root Cause Analysis

### Original Health Check Logic
```javascript
async function checkServiceStatus(url, statusElementId) {
    try {
        const response = await fetch(url, { signal: controller.signal });
        // Only 200 OK = Running
        statusElement.textContent = 'Running';
    } catch (error) {
        // ANY error = Stopped
        statusElement.textContent = 'Stopped';
    }
}
```

**Problem:** This logic treats ALL non-200 responses as "Stopped", including:
- 404 responses (service IS running, just no route at root)
- Network timeouts (service doesn't exist)
- Connection refused (service crashed)

### Service-Specific Behavior

| Service | Port | Root GET Response | Docker Status | Dashboard Status (Before) |
|---------|------|-------------------|---------------|---------------------------|
| UI | 8000 | 200 OK | Running | ✓ Running |
| AI Monitor | 9000 | 200 OK | Running | ✓ Running |
| Vibe Check MCP | 3000 | 404 Not Found | Running | ✗ Stopped (FALSE) |
| Kanban | 3001 | Connection timeout | Not deployed | ✗ Stopped (CORRECT) |

**Key Finding:** Vibe Check MCP service returns `404 Not Found` for root GET requests because:
1. MCP (Model Context Protocol) services typically only respond to POST requests
2. 404 is a valid response indicating the server IS running, just no route exists
3. This is NOT the same as connection refused or timeout

## Solution Implemented

### Updated Health Check Logic
```javascript
async function checkServiceStatus(url, statusElementId, accept404 = false) {
    try {
        const response = await fetch(url, { signal: controller.signal });

        // 200 OK = service is running
        // 404 for MCP services = server responding, just no root route
        if (response.ok || (accept404 && response.status === 404)) {
            statusElement.textContent = 'Running';
            statusElement.className = 'service-status running';
        } else {
            statusElement.textContent = 'Stopped';
            statusElement.className = 'service-status stopped';
        }
    } catch (error) {
        // Network error, timeout, connection refused = truly stopped
        statusElement.textContent = 'Stopped';
        statusElement.className = 'service-status stopped';
    }
}

// Updated call for MCP service
checkServiceStatus('http://localhost:3000', 'vibe-status', true); // accept404=true
```

### Changes Made
1. Added `accept404` parameter to health check function
2. Accept 404 responses as "Running" for MCP services
3. Updated Vibe Check MCP status check to pass `accept404=true`
4. Restarted UI service to apply changes

## Expected Outcomes

### Before Fix
- UI (8000): ✓ Running
- AI Monitor (9000): ✓ Running
- Vibe Check MCP (3000): ✗ Stopped (INCORRECT - service is running)
- Kanban (3001): ✗ Stopped (CORRECT - service not deployed)

### After Fix
- UI (8000): ✓ Running
- AI Monitor (9000): ✓ Running
- Vibe Check MCP (3000): ✓ Running (FIXED - 404 accepted)
- Kanban (3001): ✗ Stopped (CORRECT - service not deployed)

## Service Details

### AI Monitor (Port 9000)
- **Status**: Running ✓
- **Root Route**: Returns 200 OK with HTML dashboard
- **API Endpoint**: `/api/metrics` returns JSON with usage stats
- **Current Data**: All counters at 0 (no API calls recorded yet)
- **Dashboard Check**: GET http://localhost:9000 → 200 OK

### Vibe Check MCP (Port 3000)
- **Status**: Running ✓ (was showing as Stopped)
- **Root Route**: Returns 404 Not Found (no root GET route)
- **Purpose**: MCP (Model Context Protocol) service for AI interactions
- **Expected Behavior**: Only responds to POST requests per MCP protocol
- **Dashboard Check**: GET http://localhost:3000 → 404 (now accepted as "Running")

### Kanban (Port 3001)
- **Status**: Not deployed ✗
- **Root Route**: Connection timeout
- **Reason**: Service not in docker-compose.yml yet
- **TODO**: Deploy via autonomous executor (track-1-gemini.md task, P1 priority)
- **Dashboard Check**: GET http://localhost:3001 → Timeout (correctly shows "Stopped")

## Why Services Show No Data

### AI Monitor Shows All Zeros
The AI Monitor service IS working correctly, but shows zero metrics because:
1. **No API calls recorded yet**: Service tracks Gemini/Copilot/Ollama usage
2. **Need actual usage**: Run job searches, AI queries to populate metrics
3. **Data persists**: Once usage occurs, metrics will update

### How to Populate Data
```python
# Option 1: Run actual job searches
uv run python -m src.app.main search --query "Python developer"

# Option 2: Trigger AI queries
uv run python tools/llm_api.py --prompt "test" --provider gemini

# Option 3: Manual API calls
from src.app.ai_monitor_ui import AIResourceMonitor
m = AIResourceMonitor()
m.record_gemini_usage(5)
m.record_copilot_usage(10)
```

## Future Improvements

### Option A: Add Dedicated Health Endpoints
Add `/health` routes to all services that return proper health status:
```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "vibe-check-mcp"}
```

**Benefits:**
- Explicit health check contract
- Can include service-specific health metrics
- Standard practice for containerized services

**Tradeoffs:**
- Requires code changes to each service
- Need to maintain health check logic

### Option B: Use Docker Health Checks
Define health checks in `docker-compose.yml`:
```yaml
vibe-check-mcp:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
    interval: 30s
    timeout: 5s
    retries: 3
```

**Benefits:**
- Docker manages health status
- Dashboard can query Docker API
- Standardized health checking

**Tradeoffs:**
- Requires docker-compose changes
- Dashboard needs Docker API access

### Option C: Service-Specific Endpoints (Current)
Point dashboard to endpoints that exist:
```javascript
checkServiceStatus('http://localhost:9000/api/metrics', 'monitor-status');
```

**Benefits:**
- No service code changes needed
- Uses existing functional endpoints

**Tradeoffs:**
- Dashboard needs to know each service's API structure
- Less standardized

## Verification Steps

1. **Check Dashboard**: Visit http://localhost:8000/dashboard
   - UI: Should show "Running" ✓
   - AI Monitor: Should show "Running" ✓
   - Vibe Check MCP: Should show "Running" ✓ (FIXED)
   - Kanban: Will show "Stopped" ✗ (expected until deployed)

2. **Verify Container Status**: `docker ps`
   - All 7 containers should be "Up"
   - Ports 8000, 9000, 3000 exposed

3. **Test Services Directly**:
   ```powershell
   # UI
   Invoke-WebRequest http://localhost:8000 -UseBasicParsing
   # Expected: 200 OK

   # AI Monitor
   Invoke-WebRequest http://localhost:9000/api/metrics -UseBasicParsing
   # Expected: 200 OK with JSON metrics

   # Vibe Check MCP
   Invoke-WebRequest http://localhost:3000 -UseBasicParsing
   # Expected: 404 Not Found (but service IS running)

   # Kanban
   Invoke-WebRequest http://localhost:3001 -UseBasicParsing
   # Expected: Connection timeout (service not deployed)
   ```

4. **Populate AI Monitor with Data**:
   ```powershell
   # Run a job search to generate Gemini API usage
   uv run python -m src.app.main search --query "Python developer" --count 5

   # Check metrics updated
   Invoke-WebRequest http://localhost:9000/api/metrics | ConvertFrom-Json
   ```

## Related Documentation
- [Vibe Check MCP Documentation](../VIBE_CHECK_MCP.md) (if exists)
- [AI Resource Monitor Documentation](../AI_RESOURCE_MONITOR.md) (if exists)
- [Kanban Deployment Task](../.ai-tasks/track-1-gemini.md)
- [Docker Services Overview](../README.md#docker-services)

## Troubleshooting

### Dashboard Still Shows "Stopped"
1. Hard refresh browser (Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Verify UI service restarted: `docker compose logs ui --tail 20`
4. Test service endpoints directly (see Verification Steps)

### Metrics Not Updating
1. Check AI Monitor logs: `docker logs job-lead-finder-ai-monitor-1 --tail 50`
2. Verify API calls are being made (run job searches)
3. Check if metrics file exists and has write permissions
4. Test API endpoint: `Invoke-WebRequest http://localhost:9000/api/metrics`

### Service Container Not Running
1. Check container status: `docker ps -a`
2. View container logs: `docker logs <container-name> --tail 50`
3. Check for port conflicts: `netstat -ano | findstr ":<port>"`
4. Restart specific service: `docker compose restart <service-name>`
5. Rebuild if needed: `docker compose up -d --build <service-name>`

## Commit Message
```
[AI] fix: Accept 404 as "Running" for MCP service health checks

The dashboard incorrectly showed Vibe Check MCP as "Stopped" because
it returned 404 for root GET requests. MCP services are POST-only by
protocol design, so 404 is a valid response indicating the server IS
running.

Changes:
- Add accept404 parameter to checkServiceStatus()
- Accept 404 responses as "Running" for MCP services
- Update Vibe Check MCP status check to pass accept404=true
- Document root cause analysis and solution

Fixes: Dashboard showing false "Stopped" status for running services
---
AI-Generated-By: GitHub Copilot (Claude Sonnet 4.5)
```
