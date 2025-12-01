# Link Validation Issues and Fixes

## Problem: Invalid Job Links from CompanyJobsMCP

### Issue Description
All Microsoft job links (and potentially other companies) were showing as valid but actually led to 404 error pages.

**Example:**
- URL: `https://careers.microsoft.com/v2/job-search/job/1149870/sdet-python-cloud-automation`
- HTTP Status: `200 OK`
- Final URL: `https://careers.microsoft.com/v2/global/en/errorPages/404.html`
- **Problem**: Returns 200 instead of 404, fooling validation

### Root Causes

1. **Gemini Hallucination**: CompanyJobsMCP uses Gemini with `google_search` tool to find jobs. Gemini was generating plausible-looking but fake job URLs that don't actually exist.

2. **Soft 404 Pattern**: Many career sites (Microsoft, etc.) return HTTP 200 for non-existent pages but redirect to error pages like `/404`, `/errorPages/404.html`, `/not-found`, etc.

3. **Validation Too Lenient**: Original validation only checked HTTP status codes, didn't detect redirects to error pages.

## Fixes Implemented

### 1. Soft-404 Detection (link_validator.py)

Added detection for "soft 404s" - pages that return 200 but redirect to error pages:

```python
# Detect "soft 404s" - sites that return 200 but redirect to error pages
final_url_lower = str(final_url).lower()
is_soft_404 = any(
    pattern in final_url_lower
    for pattern in [
        "/404",
        "/error",
        "/not-found",
        "/notfound",
        "/page-not-found",
        "/errorpages/404",
        "/errors/404",
    ]
)

# Mark as invalid if it's a soft 404
valid = (200 <= status_code < 400 or status_code == 403) and not is_soft_404
```

**Result**: Fake Microsoft URLs now correctly marked as `valid=false` with `error="soft 404 detected"`

### 2. Improved Gemini Prompt (mcp_providers.py)

Updated CompanyJobsMCP prompt to explicitly prevent hallucination:

**Before:**
```python
search_prompt = (
    f"Find {count} {query} job postings directly on company career pages "
    f"(like {companies_str}). "
    f"Use the google_search tool to find jobs on official career sites. "
)
```

**After:**
```python
search_prompt = (
    f"Use the google_search tool to find {count} REAL {query} job postings "
    f"currently listed on company career pages (like {companies_str}). "
    f"CRITICAL: Only return jobs you actually found via google_search. "
    f"DO NOT make up or hallucinate job URLs. "
    f"DO NOT generate fake job IDs or paths. "
    f"Each job MUST have a real, working URL from an actual search result. "
    # ...
    f"IMPORTANT: Use only real URLs from your search results. "
    f"If you cannot find enough real jobs, return fewer results."
)
```

**Result**: Gemini now instructed to only return jobs it actually finds, not generate plausible-looking URLs

### 3. Previous Fixes (Already Implemented)

- **Increased Timeout**: 5s → 10s for slower company career sites
- **Removed 403 from Excluded Statuses**: Sites that return 403 are now treated as "soft valid" (link exists, just blocked)
- **Timeout Errors Non-Blocking**: Don't filter out timeout errors, let user decide

## Testing

### Before Fixes
```
_process_and_filter_leads: 75 raw leads, 75 after blocking filter
_process_and_filter_leads: 15 passed validation.
Filtered: {'invalid_link:None': 56, 'excluded_status:403': 4}
```
- Only 15/75 leads passed (20%)
- 56 filtered as "invalid" (many were just slow/timeout)
- 4 filtered as 403 (actually valid, just blocked bots)

### After Fixes (Expected)
```
_process_and_filter_leads: 75 raw leads, 75 after blocking filter
_process_and_filter_leads: 45+ passed validation.
Filtered: {'soft 404 detected': 20, 'invalid_link:...': 10}
```
- More leads pass validation (60%+)
- Soft 404s properly detected and filtered
- Fewer false negatives from timeouts/403s

### Manual Test - Soft 404 Detection
```powershell
docker exec job-lead-finder-ui-1 python -c "
from app.link_validator import validate_link
import json
result = validate_link('https://careers.microsoft.com/v2/job-search/job/1149870/sdet-python-cloud-automation', timeout=10, verbose=True)
print(json.dumps(result, indent=2))
"
```

**Output:**
```
link_validator: https://careers.microsoft.com/v2/job-search/job/1149870/... -> 200 (valid=False, soft_404=True)
{
  "valid": false,
  "status_code": 200,
  "final_url": "https://careers.microsoft.com/v2/global/en/errorPages/404.html",
  "error": "soft 404 detected",
  "warning": "soft 404 (redirected to error page)"
}
```

✅ **Correctly identifies fake URL as invalid**

## Known Limitations

### 1. Gemini May Still Hallucinate
Despite improved prompts, Gemini may still generate fake jobs. The soft-404 detection catches most cases, but some sites may have different error page patterns.

**Workaround**: If you see invalid links:
- Block specific companies via Web UI → Blocked tab
- Disable CompanyJobs provider if quality is low
- Use RemoteOK/Remotive instead (real job boards, no hallucination)

### 2. Some Career Sites Block Bots
Sites like LinkedIn, Indeed may return 403 or require JavaScript/cookies. These are now treated as "soft valid" but may not be directly accessible.

**Workaround**:
- Copy URL and open in browser manually
- The job likely exists even if bot validation fails

### 3. Timeout-Heavy Sites
Some company sites (especially large enterprises) are very slow and may timeout during validation.

**Current Behavior**: Timeout errors are NOT filtered out, so you'll see them in results
**If This Is Annoying**: Can adjust timeout or filtering logic in `ui_server.py` line ~335

## Recommendations

### For Best Results

1. **Use Multiple Providers**: Enable both CompanyJobs and RemoteOK/Remotive for redundancy
2. **Check Link Validity**: Results now show `link_valid` field - focus on those marked `true`
3. **Report Soft 404s**: If you see links marked as soft 404 that are actually valid, report the URL pattern
4. **Manual Verification**: For high-value jobs, always verify links in browser before applying

### To Disable CompanyJobs (If Too Many Invalid Links)

**Via Web UI:**
1. Open http://localhost:8000
2. Click **Configuration** → **Providers** tab
3. Toggle **CompanyJobs** to OFF
4. Save

**Via config.json:**
```json
{
  "providers": {
    "companyjobs": {"enabled": false, "name": "CompanyJobs"}
  }
}
```

## Future Improvements

- Add content-based validation (fetch page HTML, check for job-related keywords)
- Add company-specific error page patterns (e.g., `careers.google.com/error`)
- Implement job URL verification via APIs when available
- Cache validation results to avoid re-checking same URLs
- Add user feedback mechanism to improve detection patterns
