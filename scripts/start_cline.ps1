# Cline Manager - Simple automation starter
# Usage: .\scripts\start_cline.ps1

param([string]$Task)

Write-Host "`nStarting Cline Auto-Development" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Get next task from TODO.md
if (-not $Task) {
    $lines = Get-Content "TODO.md"
    $inPriority = $false
    foreach ($line in $lines) {
        if ($line -match "^## (Immediate|High Priority)") {
            $inPriority = $true
            continue
        }
        if ($line -match "^## (Medium|Low)") { break }
        if ($inPriority -and $line -match "^- \[ \] (.+)") {
            $Task = $matches[1]
            break
        }
    }
}

if ($Task) {
    Write-Host "Next Task: " -NoNewline -ForegroundColor Yellow
    Write-Host $Task -ForegroundColor White

    # Create prompt for Cline
    $prompt = @"
Read TODO.md and work on this task autonomously:

Task: $Task

Instructions:
1. Read Memory Bank files from .claude/settings.json
2. Follow workflow in .claude/settings.json
3. Implement with tests
4. Update Memory Bank when complete
5. Create PR with [AI] tag

Follow autonomous execution guidelines in .claude/settings.json.
"@

    Write-Host "`n--- Copy this into Cline ---" -ForegroundColor Green
    Write-Host $prompt -ForegroundColor Yellow
    Write-Host "--- End of prompt ---`n" -ForegroundColor Green

    Write-Host "Open Cline: Ctrl+Shift+P -> 'Cline: Open'" -ForegroundColor Cyan
} else {
    Write-Host "No unchecked tasks found in TODO.md" -ForegroundColor Red
}
