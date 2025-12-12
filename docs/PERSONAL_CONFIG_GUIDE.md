# Configuration Guide

## Web UI

Use the 5-tab configuration interface:
- **Industry**: Select profile (Tech, Finance, ESG, etc.)
- **Providers**: Enable/disable job sources
- **Location**: Set preferred locations
- **Search**: Result count, oversample multiplier
- **Blocked**: Hide specific sites/employers

## API

- `GET /api/job-config` - View current config
- `POST /api/job-config/search` - Update search params
- `GET /api/industry-profiles` - List available profiles
- `GET /api/industry-profile?name=esg` - Load specific profile

## File (config.json)

Direct editing for advanced users. Auto-reloaded on change.

**Key settings:**
- `default_count`: Jobs per search (default: 10)
- `oversample_multiplier`: How many to fetch before filtering (default: 10x)
- `blocked_entities`: Sites/employers to exclude
