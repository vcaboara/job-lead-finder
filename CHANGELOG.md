# Changelog

All notable changes to the Job Lead Finder project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Enhanced Resume Upload** - Support for multiple file formats with improved security
  - Supported formats: `.txt`, `.md`, `.pdf`, `.docx`
  - Increased size limit: 5MB (previously 1MB)
  - Comprehensive malicious content detection:
    - Script pattern detection (JavaScript, VBScript, eval, exec)
    - Macro detection in DOCX files
    - Binary content detection (null bytes)
    - Excessive special character detection (>30% threshold)
    - Extremely long line detection (>10,000 chars)
  - PDF text extraction using `pypdf`
  - DOCX text extraction using `python-docx` with table support
  - Enhanced error messages with specific file size information
  - 18 comprehensive test cases covering all security scenarios

### Added
- **WeWorkRemotely Provider** - RSS-based job provider for remote positions
  - Searches 4 tech-focused RSS categories (back-end, front-end, full-stack, devops)
  - Expected performance: ~0.5s
  - Enabled by default
  - Comprehensive test coverage (6 test cases)
- **Round-Robin Provider Distribution** - MCPAggregator now uses round-robin selection
  - Ensures diversity by cycling through all available providers
  - Prevents single provider from dominating results
  - Test coverage: `test_provider_diversity_round_robin`
- **Modular Provider Architecture** - New `app/providers/` package structure
  - `MCPProvider` abstract base class for standardized provider interface
  - Individual provider modules for better maintainability
  - Comprehensive developer documentation in `providers/README.md`
  - Backward compatibility maintained via `providers/__init__.py`
- **Changelog API Endpoint** - `/api/changelog` endpoint for programmatic access to CHANGELOG.md
  - Returns changelog content as plain text
  - Useful for version tracking and automated documentation

### Security

- Upgraded XML parsing to use `defusedxml` library to prevent XXE attacks
- Added `defusedxml>=0.7.0` dependency

### Changed

- Query filtering now supports short tech terms (Go, R, UI, UX, C#, etc.)
- MCPAggregator deduplication strategy changed from simple concatenation to round-robin
- Refactored MCP providers from monolithic file to modular package structure

### Fixed

- Company name extraction in WeWorkRemotely RSS feed (was extracting "Headquarters:" instead of company name)
  - Now correctly parses company from title format: "CompanyName: Job Title"
  - Job title properly cleaned to remove company prefix

### Test Improvements

- Test isolation: Added mock for `WeWorkRemotelyMCP.is_available()` in `test_no_providers_available`

## [0.1.1] - 2025-12-01

### Added
- `/api/search/progress/{search_id}` - Real-time search progress endpoint
- Configurable score-based filtering with `min_score` parameter
- 90-second Gemini API timeout to prevent indefinite hangs
- 5-minute maximum search timeout
- Structured logging with timestamps throughout search pipeline
- Exception chaining across 8 error handlers

### Changed
- **CompanyJobs (Gemini) disabled by default** - Performance optimization (6min → 2-3s)
- Lazy % formatting for all logging calls (performance + consistency)
- Updated type hints to use modern Python 3.10+ syntax
- Consolidated `config_store.py` into `config_manager.py`

### Fixed
- Fixed `provider.query()` bug - replaced with `simple_gemini_query()`
- Test isolation issues - fresh test clients and config cleanup
- Cover letter generation test mock for Docker CI compatibility
- Multiple syntax errors and missing imports

### Documentation
- Added `STRATEGY.md` with comprehensive provider analysis
- Performance metrics and roadmap for future providers

## [0.1.0] - 2025-11-30

### Added
- Initial release with core job search functionality
- RemoteOK provider (API-based, ~0.13s)
- Remotive provider (API-based, ~1.0s)
- CompanyJobs provider (Gemini-based, slow)
- DuckDuckGo provider (HTML scraping)
- FastAPI web UI with resume upload
- Job tracking and status management
- Link validation with soft-404 detection
- Industry profile system (8 industries)
- Configuration management with persistent storage
- Blocked entities filtering (sites and employers)
- AI-powered job scoring and evaluation
- Docker support with CI/CD via GitHub Actions

---

## Version History Legend

### Categories
- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
- **Documentation**: Documentation changes

### Performance Baselines
- **RemoteOK**: ~0.13s
- **Remotive**: ~1.0s  
- **WeWorkRemotely**: ~0.5s
- **DuckDuckGo**: ~2-3s
- **CompanyJobs (Gemini)**: 90-325s (disabled by default)

### API Compatibility
This project follows semantic versioning:
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes
