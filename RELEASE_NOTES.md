# Release v0.2.1

Date: 2025-11-26

This release packages the current working state of the Job Lead Finder project and includes a screenshot of the UI first-run.

Highlights
- FastAPI web UI at `http://localhost:8000` (see `artifacts/first_run.png`).
- Job search powered by Gemini + google_search tool.
- Persistent leads saved to `leads.json`.
- Job evaluation (0-100) against a provided resume, with detailed reasoning.

Included artifacts
- `artifacts/first_run.png` — screenshot of the UI showing a successful search and evaluations.
- `leads.json` — persisted results from test run.

Notes
- To reproduce the run locally use Docker Compose: `docker compose up ui` and then run a search from the UI.
- Remember to set `GEMINI_API_KEY` in your environment before running searches that require the Gemini API.

How to push this release

After reviewing the commit locally, push commits and tags to the remote:

```powershell
# Push commits
git push origin HEAD
# Push tags
git push origin v0.2.1
```

Thank you — this release is intended to be included in demonstrations and application portfolios to show how the tool was used to find and evaluate job listings.