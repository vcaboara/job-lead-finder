#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Autonomous development loop - monitors TODO.md and triggers Cline
.DESCRIPTION
    Runs in background, checks for incomplete TODO items, and triggers Cline
    to work on them autonomously with auto-commit and auto-PR enabled.
#>

param(
    [int]$CheckInterval = 300,  # Check every 5 minutes
    [string]$TodoPath = "TODO.md",
    [switch]$DryRun
)

function Get-NextTask {
    $content = Get-Content $TodoPath -Raw
    $pattern = '- \[ \] (.+)'

    if ($content -match $pattern) {
        return $matches[1]
    }
    return $null
}

function Is-ClineRunning {
    # Check if Cline is currently processing (look for active git branches or processes)
    $activeBranches = git branch | Select-String "auto/" | Measure-Object
    return $activeBranches.Count -gt 0
}

function Start-ClineTask {
    param([string]$Task)

    Write-Host "🤖 Starting autonomous development for: $Task" -ForegroundColor Cyan

    $prompt = @"
Read TODO.md and work on this task autonomously:

Task: $Task

Instructions:
1. Read Memory Bank files from .claude/settings.json
2. Follow workflow in .claude/settings.json
3. Implement with tests
4. Auto-commit changes (autoCommit: true)
5. Auto-create PR with [AI] tag (autoPR: true)
6. Update Memory Bank when complete

Execute autonomously with no approval required (terminalCommands: false).
"@

    if ($DryRun) {
        Write-Host "DRY RUN - Would start Cline with prompt:" -ForegroundColor Yellow
        Write-Host $prompt
        return
    }

    # Trigger Cline via VS Code command (requires VS Code CLI)
    # Alternative: Write to a file that Cline watches
    $promptFile = ".ai-tasks/current-task.md"
    New-Item -ItemType Directory -Force -Path (Split-Path $promptFile) | Out-Null
    Set-Content -Path $promptFile -Value $prompt

    Write-Host "✅ Task prompt written to $promptFile" -ForegroundColor Green
    Write-Host "📝 Cline will pick this up automatically" -ForegroundColor Green
}

Write-Host @"
╔══════════════════════════════════════════╗
║   Autonomous Development Loop Started    ║
╚══════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  - Check interval: $CheckInterval seconds"
Write-Host "  - TODO path: $TodoPath"
Write-Host "  - Auto-commit: ENABLED"
Write-Host "  - Auto-PR: ENABLED"
Write-Host "  - Terminal approval: DISABLED (fully autonomous)"
Write-Host ""

$iteration = 0
while ($true) {
    $iteration++
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Iteration $iteration - Checking for tasks..." -ForegroundColor Gray

    # Check if Cline is already working
    if (Is-ClineRunning) {
        Write-Host "⏳ Cline is currently working on a task, waiting..." -ForegroundColor Yellow
        Start-Sleep -Seconds $CheckInterval
        continue
    }

    # Get next task
    $nextTask = Get-NextTask

    if ($null -eq $nextTask) {
        Write-Host "✨ No pending tasks found in TODO.md" -ForegroundColor Green
        Write-Host "💤 Sleeping for $CheckInterval seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds $CheckInterval
        continue
    }

    # Start Cline on the task
    Start-ClineTask -Task $nextTask

    # Wait before checking again
    Write-Host "⏱️  Waiting $CheckInterval seconds before next check..." -ForegroundColor Gray
    Start-Sleep -Seconds $CheckInterval
}
