## MCP Providers Package

This directory contains modular job search providers following the MCP (Model Context Protocol) pattern.

### Structure

```
providers/
├── __init__.py              # Package exports and legacy compatibility
├── base.py                  # MCPProvider base class and utilities  
├── weworkremotely.py        # We Work Remotely RSS provider
├── remote_ok.py             # RemoteOK API provider (TODO)
├── remotive.py              # Remotive API provider (TODO)
└── README.md                # This file
```

### Adding a New Provider

1. **Create a new file** (e.g., `newsite.py`)

2. **Implement the provider class**:
```python
from typing import Any, Dict, List, Optional
from .base import MCPProvider, HTTPX_AVAILABLE

class NewSiteMCP(MCPProvider):
    def __init__(self):
        super().__init__("NewSite")
    
    def is_available(self) -> bool:
        # Check if provider can be used
        return HTTPX_AVAILABLE
    
    def search_jobs(
        self,
        query: str,
        count: int = 5,
        location: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        # Implement job search logic
        jobs = []
        # ... fetch and parse jobs ...
        return jobs[:count]
```

3. **Export from __init__.py**:
```python
from .newsite import NewSiteMCP

__all__ = [
    # ... existing exports ...
    "NewSiteMCP",
]
```

4. **Register in config_manager.py**:
```python
provider_map = {
    # ... existing providers ...
    "newsite": NewSiteMCP,
}
```

5. **Add tests** in `tests/test_mcp_providers.py`

6. **Update documentation** in README.md and CHANGELOG.md

### Provider Requirements

Each provider must:
- Inherit from `MCPProvider`
- Implement `search_jobs()` method
- Implement `is_available()` method
- Return job dicts with keys: `title`, `company`, `location`, `summary`, `link`, `source`
- Handle errors gracefully (return empty list on failure)
- Support query filtering
- Be fast (< 2 seconds for typical queries)

### Migration Status

- ✅ **WeWorkRemotelyMCP** - Fully migrated to modular structure
- ⏳ **RemoteOKMCP** - Still in mcp_providers.py
- ⏳ **RemotiveMCP** - Still in mcp_providers.py
- ⏳ **CompanyJobsMCP** - Still in mcp_providers.py
- ⏳ **DuckDuckGoMCP** - Still in mcp_providers.py
- ⏳ **LinkedInMCP** - Still in mcp_providers.py (deprecated)
- ⏳ **IndeedMCP** - Still in mcp_providers.py (deprecated)
- ⏳ **GitHubJobsMCP** - Still in mcp_providers.py (deprecated)

### Design Principles

1. **Single Responsibility**: Each provider in its own file
2. **No Dependencies**: Providers should be independent
3. **Fail Gracefully**: Return empty list, don't crash
4. **Fast by Default**: Optimize for speed (parallel requests, caching)
5. **Well Documented**: Clear docstrings and inline comments
6. **Easy to Test**: Mockable dependencies, clear interfaces
