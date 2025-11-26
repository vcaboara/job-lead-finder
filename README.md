# Job Lead Finder — Minimal Starter

This repository is a minimal starter for a modular job-finding + evaluation tool.

Key features:
- Minimal CLI: `src/app/main.py`
- Gemini provider template: `src/app/gemini_provider.py`
- Dockerfile for deterministic builds
- GitHub Actions CI workflow to build and run tests

To build and run locally:

1. Create virtualenv and install:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e .
```

2. Run health check:

```powershell
python -m app.main health
```

3. Run a sample search:

```powershell
python -m app.main search -q python -s Python Docker
```

To enable Gemini provider, set `GOOGLE_API_KEY` and install optional extras:

```powershell
pip install .[gemini]
$env:GOOGLE_API_KEY = '...'
```

**App Reference**

- **Module**: `app.main`
	- `format_resume(skills, roles, locations, text=None)` -> `str`
		- Build a short resume summary used by providers.
	- `fetch_jobs(query)` -> `list[dict]`
		- Minimal built-in job fetcher (sample/hard-coded). Replace with real sources.
	- `run_search(args)` -> exit code
		- Orchestrates fetching jobs, selecting an evaluation provider (mock or Gemini), and prints JSON results.
	- `main()` / CLI
		- Commands:
			- `health` : print `ok` and exit 0.
			- `search` : evaluate jobs for a query.
				- Flags:
					- `--query, -q` (required): query string to search job titles/descriptions.
					- `--skills, -s` (optional): list of skills to use for basic scoring (default: `Python Docker`).
					- `--roles, -r` (optional): desired roles (default: `Engineer`).
					- `--locations, -l` (optional): desired locations (default: `Remote`).
					- `--provider, -p` (optional): `mock` (default) or `gemini` — selects evaluator.
					- `--resume` : optional free-text resume to include in evaluation prompt.

**Docker & CI**

- The GitHub Actions CI builds a Docker image using the repository `Dockerfile`, passing `INSTALL_TEST_DEPS=true`, and runs `pytest` inside the container. This ensures CI runs in the exact same environment as local Docker runs.
- `docker-compose.yml` builds the same image locally and mounts the repository into `/app` so you can iterate without rebuilding.

Examples (local Docker usage):

Build the image locally (same as CI):

```powershell
docker build --tag job-starter-ci --build-arg INSTALL_TEST_DEPS=true .
```

Run tests in Docker (same as CI):

```powershell
docker run --rm job-starter-ci pytest -q
```

Run the health command inside Docker:

```powershell
docker run --rm job-starter-ci python -m app.main health
```

Run interactively with docker-compose (container stays running):

```powershell
docker compose up -d --build
docker compose run --rm app pytest -q
docker compose run --rm app python -m app.main search -q python -s Python Docker
docker compose down
```

Notes:
- Deleting the `venv` will not remove any source changes; your code and the added files are committed to the repository and included in the `archive/` backup.
- To enable the real Gemini provider, set `GOOGLE_API_KEY` and install extras: `pip install .[gemini]`.

Full CLI help

Top-level help (run `python -m app.main -h`):

```text
usage: job-starter [-h] {search,health,help} ...

positional arguments:
	{search,health,help}
		help                Show full help or help for a specific subcommand

options:
	-h, --help            show this help message and exit
```

`search` subcommand help (run `python -m app.main help search`):

```text
usage: job-starter search [-h] --query QUERY [--skills [SKILLS ...]] [--roles [ROLES ...]] [--locations [LOCATIONS ...]] [--provider {mock,gemini}]
													[--resume RESUME]

options:
	-h, --help            show this help message and exit
	--query, -q QUERY
	--skills, -s [SKILLS ...]
	--roles, -r [ROLES ...]
	--locations, -l [LOCATIONS ...]
	--provider, -p {mock,gemini}
	--resume RESUME       Optional free-text resume to include in evaluation
```

Local Python (no install)

If you prefer to run the CLI locally without installing the package into a virtualenv, set `PYTHONPATH` so Python can find the `src/` package:

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m app.main health
```

Or (POSIX):

```bash
PYTHONPATH=src python -m app.main health
```

