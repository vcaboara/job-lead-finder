# Job Lead Finder: Implemented Features & TODOs

## Implemented Features

### Core Functionality
- **FastAPI UI server** with REST endpoints for search, config, resume upload, block list, and health check
- **Single-page web UI** (HTML/JS) for job search, resume upload, config management, and results display
- **Gemini AI integration** (via `google-generativeai` or legacy `google.genai`) for real job search and evaluation
- **Fallback local search** if Gemini API key is missing or provider unavailable
- **Resume upload**: supports .txt and .md files, with size/type/UTF-8 validation and injection scanning
- **Resume paste**: textarea allows manual paste/edit
- **Block list management**: add/remove blocked sites and employers via UI and API
- **Link validation**: checks job links, annotates with status/warning/error
- **Filtering**: excludes jobs with blocked sites/employers, 403/404 links, localhost, and search-result URLs
- **Auto-evaluate**: if resume is present, jobs are scored against it automatically
- **Config persistence**: config.json, resume.txt, and uploads/ are gitignored
- **Multi-stage Dockerfile**: builder installs all deps, runtime is slim with only venv and app
- **Comprehensive tests**: 113 passing tests for endpoints, config, search, upload, and validation
- **Logs**: Gemini response logs and diagnostics written to `logs/` folder

### UI Features
- **Search form**: query, resume upload/paste, result count
- **Results panel**: shows job cards with title, company, location, summary, score, reasoning, and link
- **Progress/status indicator**: shows search status and errors
- **Config panel**: block list management, link validator
- **Responsive layout**: works on desktop and mobile

### Security & Validation
- **Injection scanning**: system instructions, resume, and block list entries are scanned for prompt injection patterns
- **File validation**: resume uploads limited to 1MB, .txt/.md, UTF-8 only
- **Link validation**: checks for valid URLs, annotates with status/warning/error
- **Generic page filtering**: excludes /careers, /jobs, and other non-specific job pages
- **Search result filtering**: excludes job board search result pages
- **Status filtering**: excludes 403 Forbidden and 404 Not Found pages

### DevOps & Packaging
- **Multi-stage Dockerfile**: builder+runtime for smaller images
- **docker-compose.yml**: separate `app` and `ui` services, environment variable support
- **.env support**: for API keys
- **.gitignore**: excludes config.json, resume.txt, uploads/

## Known Issues / Limitations
- **Job count may be less than requested**: after filtering invalid/blocked/bad links/generic pages, only valid jobs are shown
- **List may disappear**: if all jobs are filtered out, no results are shown
- **Gemini google_search may return career pages**: we filter these but the model needs better prompting
- **No PDF/DOCX resume support yet**: only .txt/.md
- **No image upload/preview yet**
- **No advanced search options (location, salary, etc.)**
- **No direct MCP integration yet**: LinkedIn and DuckDuckGo MCPs not yet integrated (see MCP_INTEGRATION_GUIDE.md)

## TODOs
- [ ] **Add PDF/DOCX resume support**: extract text from PDF/DOCX files using pdfplumber and python-docx; update Dockerfile and tests
- [ ] **Plan smaller images feature**: implement image uploads with size/type limits and preview; defer until core is stable
- [ ] **Improve Gemini prompt**: encourage model to return only real job postings with direct links
- [ ] **Handle empty results gracefully**: show a message if all jobs are filtered out
- [ ] **Advanced filtering**: allow user to block more link patterns (e.g., search-result URLs)
- [ ] **User feedback for bad links**: show warnings for excluded jobs
- [ ] **Optional: add OCR for image resumes**
- [ ] **Optional: add advanced search filters (location, salary, etc.)**

---

This document summarizes the current functionality and open tasks for the Job Lead Finder project. Use it to compare with other AI job search implementations or to plan future improvements.
