#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Real-time monitoring dashboard for autonomous development
.DESCRIPTION
    Shows live status of AI development activity, PRs, services, and tasks
#>

param(
    [int]$RefreshInterval = 10,
    [switch]$Detailed
)

function Show-Status {
    Clear-Host

    $timestamp = Get-Date -Format "HH:mm:ss"

    Write-Host "" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "       AUTONOMOUS DEVELOPMENT MONITOR - $timestamp" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan

    # Active Branches
    Write-Host ""
    Write-Host "ACTIVE WORK:" -ForegroundColor Yellow
    $branches = git branch | Select-String "auto/"
    if ($branches) {
        $branches | ForEach-Object { Write-Host "  🔧 $_" -ForegroundColor Green }
    } else {
        Write-Host "  ✨ No active branches" -ForegroundColor Gray
    }

    # Open PRs
    Write-Host ""
    Write-Host "OPEN PULL REQUESTS:" -ForegroundColor Yellow
    $prs = gh pr list --state open --json number,title,statusCheckRollup 2>$null | ConvertFrom-Json
    if ($prs) {
        foreach ($pr in $prs) {
            $status = "PENDING"
            if ($pr.statusCheckRollup) {
                $conclusion = $pr.statusCheckRollup[0].conclusion
                if ($conclusion -eq "SUCCESS") { $status = "PASS" }
                elseif ($conclusion -eq "FAILURE") { $status = "FAIL" }
            }
            $statusColor = if ($status -eq "PASS") { "Green" } elseif ($status -eq "FAIL") { "Red" } else { "Yellow" }
            Write-Host "  [$status] PR #$($pr.number): $($pr.title)" -ForegroundColor $statusColor
        }
    } else {
        Write-Host "  No open PRs" -ForegroundColor Gray
    }

    # TODO Tasks
    Write-Host ""
    Write-Host "TODO STATUS:" -ForegroundColor Yellow
    $pendingTasks = (Get-Content TODO.md | Select-String "- \[ \]").Count
    $completedTasks = (Get-Content TODO.md | Select-String "- \[x\]").Count
    $totalTasks = $pendingTasks + $completedTasks
    $progress = if ($totalTasks -gt 0) { [math]::Round(($completedTasks / $totalTasks) * 100) } else { 0 }

    Write-Host "  Total: $totalTasks | Completed: $completedTasks | Remaining: $pendingTasks" -ForegroundColor White
    Write-Host "  Progress: $progress% " -NoNewline
    Write-Host ("█" * [math]::Floor($progress / 5)) -ForegroundColor Green -NoNewline
    Write-Host ("░" * [math]::Floor((100 - $progress) / 5)) -ForegroundColor DarkGray

    # Next Task
    $nextTask = (Get-Content TODO.md | Select-String "- \[ \]" | Select-Object -First 1).ToString().Trim()
    if ($nextTask) {
        Write-Host ""
        Write-Host "  Next Task: " -NoNewline -ForegroundColor Cyan
        Write-Host ($nextTask -replace "- \[ \] ", "") -ForegroundColor White
    }

    # Services
    Write-Host ""
    Write-Host "SERVICES STATUS:" -ForegroundColor Yellow
    $services = @{
        'AI Monitor (9000)' = (Test-NetConnection localhost -Port 9000 -WarningAction SilentlyContinue).TcpTestSucceeded
        'Vibe Check (3000)' = (Test-NetConnection localhost -Port 3000 -WarningAction SilentlyContinue).TcpTestSucceeded
        'Main UI (8000)' = (Test-NetConnection localhost -Port 8000 -WarningAction SilentlyContinue).TcpTestSucceeded
    }

    foreach ($service in $services.GetEnumerator()) {
        $status = if ($service.Value) { "[RUNNING]" } else { "[STOPPED]" }
        $color = if ($service.Value) { "Green" } else { "Red" }
        Write-Host "  $status $($service.Key)" -ForegroundColor $color
    }

    # Recent Activity
    Write-Host ""
    Write-Host "RECENT AI ACTIVITY:" -ForegroundColor Yellow
    $recentCommits = git log --oneline --grep="\[AI\]" -3 2>$null
    if ($recentCommits) {
        $recentCommits | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No recent AI commits" -ForegroundColor Gray
    }

    # Detailed Mode
    if ($Detailed) {
        Write-Host ""
        Write-Host "MEMORY BANK STATUS:" -ForegroundColor Yellow
        $activeContext = Get-Content memory\tasks\active_context.md -Tail 5 -ErrorAction SilentlyContinue
        if ($activeContext) {
            Write-Host "  Last 5 lines from active_context.md:" -ForegroundColor Gray
            $activeContext | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        }
    }

    # Footer
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to exit | Refreshing every $RefreshInterval seconds" -ForegroundColor Gray
    Write-Host "Run with -Detailed for more info | View guide: docs/MONITORING_GUIDE.md" -ForegroundColor Gray
}

# Main loop
Write-Host "Starting Autonomous Development Monitor..." -ForegroundColor Green
Write-Host "Refresh interval: $RefreshInterval seconds" -ForegroundColor Gray
Start-Sleep 1

try {
    while ($true) {
        Show-Status
        Start-Sleep $RefreshInterval
    }
} catch {
    Write-Host ""
    Write-Host ""
    Write-Host "Monitor stopped." -ForegroundColor Yellow
}
