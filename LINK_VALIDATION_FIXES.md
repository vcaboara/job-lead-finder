# Link Validation Improvements

## Soft-404 Detection

Links returning HTTP 200 but showing error pages (e.g., `/404`, `/error`, `/not-found`) are now detected and marked invalid.

## Anti-Hallucination

CompanyJobs provider instructs Gemini to only return real URLs from search results, reducing fake job postings.

## Known Limitations

- Some company career pages require login/cookies
- Soft-404 patterns may vary by site
- HTTP 403 treated as "soft-valid" (may be accessible in browser)
