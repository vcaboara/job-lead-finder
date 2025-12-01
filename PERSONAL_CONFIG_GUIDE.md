# Personal Configuration Guide

This guide shows where to edit your personal job search settings.

## Quick Reference

| Setting                     | Location                | How to Edit                                                                                |
| --------------------------- | ----------------------- | ------------------------------------------------------------------------------------------ |
| **Industry Profile**        | Web UI → Industry tab   | Select from dropdown (tech, finance, healthcare, gaming, ecommerce, automotive, aerospace) |
| **Job Providers**           | Web UI → Providers tab  | Toggle switches to enable/disable CompanyJobs, RemoteOK, Remotive, DuckDuckGo, etc.        |
| **Location Preferences**    | Web UI → Location tab   | Set default location, toggle remote/hybrid/onsite preferences                              |
| **Blocked Sites/Companies** | Web UI → Blocked tab    | Add employers or sites to exclude from results                                             |
| **Resume**                  | Web UI → Resume section | Upload `.txt`, `.pdf`, or `.docx` file                                                     |
| **System Instructions**     | `config.json`           | Edit `system_instructions` field (instructions for AI evaluation)                          |

## Configuration Files

### `config.json` (Root Directory)
Your main configuration file. Created automatically with defaults.

```json
{
  "system_instructions": "Your custom instructions for AI job matching",
  "blocked_entities": [
    {"type": "site", "value": "example.com"},
    {"type": "employer", "value": "Bad Company Inc"}
  ],
  "industry_profile": "tech",
  "location": {
    "default_location": "United States",
    "prefer_remote": true,
    "allow_hybrid": true,
    "allow_onsite": false
  },
  "providers": {
    "companyjobs": {"enabled": true, "name": "CompanyJobs"},
    "remoteok": {"enabled": true, "name": "RemoteOK"},
    "remotive": {"enabled": true, "name": "Remotive"},
    "duckduckgo": {"enabled": false, "name": "DuckDuckGo"}
  },
  "search": {
    "default_count": 5,
    "oversample_multiplier": 5,
    "enable_ai_ranking": true
  }
}
```

**What each field does:**
- `system_instructions`: Custom prompt instructions for AI when evaluating job matches (e.g., "I prefer startups over enterprises")
- `blocked_entities`: Sites and employers to exclude from results
- `industry_profile`: Which industry profile to use (determines company list and search keywords)
- `location`: Default location and work arrangement preferences
- `providers`: Which job sources to use (enable/disable each provider)
- `search`: Search parameters (result count, AI ranking settings)

### `resume.txt` (Root Directory)
Your resume text for job matching. Upload via Web UI or create manually.

**Supported formats:**
- `.txt`: Plain text
- `.pdf`: Extracted automatically
- `.docx`: Extracted automatically

**Tips:**
- Include skills, technologies, and experience level
- AI uses this to evaluate job relevance
- Can be uploaded via Web UI Resume section

## Web UI Configuration Tabs

Open http://localhost:8000 and click the **Configuration** section to access:

### 1. Industry Tab
Select your target industry to customize company lists and search keywords.

**Available Profiles:**
- **Tech**: Apple, Microsoft, NVIDIA, Google, Amazon, cloud/AI companies (excludes Musk/Zuckerberg companies)
- **Finance**: JPMorgan, Goldman Sachs, Stripe, PayPal, Robinhood, trading firms
- **Healthcare**: Epic Systems, Medtronic, Pfizer, UnitedHealth, digital health companies
- **Gaming**: Epic Games, Valve, Riot Games, Unity, Nintendo, PlayStation
- **E-commerce**: Amazon, Shopify, eBay, Etsy, Instacart
- **Automotive**: Tesla, GM, Ford, Rivian, Waymo (includes electric/autonomous)
- **Aerospace**: SpaceX, Blue Origin, Boeing, Northrop Grumman, Lockheed Martin

**Each profile includes:**
- Curated company list (20-40 companies)
- Industry-specific search keywords
- Preferred locations
- Company exclusions

### 2. Providers Tab
Enable/disable job sources with toggle switches.

**Available Providers:**
- **CompanyJobs**: Direct company career pages via Google search (RECOMMENDED)
- **RemoteOK**: Remote job board aggregator
- **Remotive**: Remote job listings
- **DuckDuckGo**: General web search for jobs
- **GitHub Jobs**: GitHub's job board (when available)
- **LinkedIn**: LinkedIn job listings (requires authentication)
- **Indeed**: Indeed job board

**Tips:**
- CompanyJobs finds listings on actual company career sites (best quality)
- RemoteOK and Remotive are good for remote-first positions
- Disable providers that return low-quality results

### 3. Location Tab
Set your location preferences.

**Settings:**
- **Default Location**: Where you want to work (e.g., "San Francisco", "Remote", "United States")
- **Prefer Remote**: Prioritize remote positions
- **Allow Hybrid**: Include hybrid (remote + office) roles
- **Allow Onsite**: Include fully onsite positions

### 4. Blocked Tab
Exclude specific sites or employers from results.

**How to Block:**
1. Enter site domain (e.g., `example.com`) or employer name (e.g., `Bad Company Inc`)
2. Select type (Site or Employer)
3. Click "Add to Block List"

**Examples:**
- Block aggregator sites: `indeed.com`, `monster.com`
- Block specific companies: `Meta`, `Amazon`
- Block recruiting sites: `dice.com`, `cybercoders.com`

## Advanced: Editing Configuration Programmatically

### Via API (when UI is running)

**Get current config:**
```powershell
curl http://localhost:8000/api/config
```

**Update industry profile:**
```powershell
curl -X POST "http://localhost:8000/api/industry-profile?profile=finance"
```

**Enable/disable provider:**
```powershell
curl -X POST "http://localhost:8000/api/job-config/provider/companyjobs?enabled=true"
```

**Update location preferences:**
```powershell
curl -X POST "http://localhost:8000/api/job-config/location" `
  -H "Content-Type: application/json" `
  -d '{"default_location": "New York", "prefer_remote": false, "allow_onsite": true}'
```

**Add blocked entity:**
```powershell
curl -X POST "http://localhost:8000/api/config/block-entity/site/example.com"
```

### Via CLI

Edit `config.json` directly with any text editor, then restart the UI:
```powershell
notepad config.json
docker-compose restart ui
```

## Best Practices

1. **Start with Industry Profile**: Select your industry first, then customize providers and location
2. **Enable CompanyJobs**: Best quality results from direct company career pages
3. **Upload Resume**: AI uses it to rank jobs by relevance
4. **Block Aggregators**: Add `indeed.com`, `linkedin.com` to blocked sites if you only want direct company listings
5. **Use System Instructions**: Add custom matching criteria (e.g., "Prefer startups", "Must have 401k")
6. **Test Search**: Run a search and refine settings based on results quality

## Troubleshooting

**Q: Changes not taking effect?**
- Web UI saves immediately - no restart needed
- Manual `config.json` edits require UI restart: `docker-compose restart ui`

**Q: Where is my data stored?**
- `config.json`: Configuration settings
- `resume.txt`: Your resume text
- `leads.json`: Last search results
- All files in workspace root directory

**Q: How do I reset to defaults?**
```powershell
Remove-Item config.json, resume.txt, leads.json -ErrorAction SilentlyContinue
docker-compose restart ui
```

**Q: Can I create custom industry profiles?**
- Yes! Edit `src/app/industry_profiles.py` and add your profile to `INDUSTRY_PROFILES` dict
- Requires rebuilding container: `docker-compose build ui`
