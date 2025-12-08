# Test Runner Script - Fast Test Workflows
# Usage: .\test.ps1 [fast|unit|smoke|all|cov|profile]

param(
    [Parameter(Position=0)]
    [ValidateSet('fast', 'unit', 'smoke', 'all', 'cov', 'profile', 'watch')]
    [string]$Mode = 'fast'
)

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

switch ($Mode) {
    'fast' {
        Write-Host "🚀 Running CHANGED tests only (fastest)" -ForegroundColor Green
        python -m pytest --picked --maxfail=1 --ff
    }
    'unit' {
        Write-Host "⚡ Running UNIT tests only (no I/O)" -ForegroundColor Cyan
        python -m pytest -m unit -n auto --maxfail=3
    }
    'smoke' {
        Write-Host "💨 Running SMOKE test (failed first, stop at first failure)" -ForegroundColor Yellow
        python -m pytest --ff --maxfail=1 -x
    }
    'all' {
        Write-Host "🔍 Running FULL test suite (all tests)" -ForegroundColor Magenta
        python -m pytest -m "" --slow
    }
    'cov' {
        Write-Host "📊 Running tests with COVERAGE" -ForegroundColor Blue
        python -m pytest --cov=src/app --cov-report=term-missing --cov-report=html
    }
    'profile' {
        Write-Host "⏱️ Profiling SLOWEST tests" -ForegroundColor DarkYellow
        python -m pytest --durations=20 --durations-min=1.0 -v
    }
    'watch' {
        Write-Host "👀 Watch mode - rerun on file changes" -ForegroundColor DarkGreen
        Write-Host "Install pytest-watch: pip install pytest-watch" -ForegroundColor Gray
        ptw -- --maxfail=1 --ff
    }
}

Write-Host "`nTest mode: $Mode" -ForegroundColor White
