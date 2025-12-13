# Cline Auto-Development Service
# Automatically feeds tasks from TODO.md to Cline without manual intervention

param(
    [int]$CheckInterval = 300,  # Check every 5 minutes
    [string]$TodoPath = "TODO.md"
)

$ErrorActionPreference = "Continue"

Write-Host "Cline Auto-Dev Service Starting..." -ForegroundColor Cyan
Write-Host "Check Interval: $CheckInterval seconds" -ForegroundColor Gray
Write-Host "Watching: $TodoPath" -ForegroundColor Gray
Write-Host ""

function Get-NextTask {
    $lines = Get-Content $TodoPath -ErrorAction SilentlyContinue
    if (-not $lines) { return $null }

    $inPriority = $false
    foreach ($line in $lines) {
        if ($line -match "^## (Immediate|High Priority)") {
            $inPriority = $true
            continue
        }
        if ($line -match "^## (Medium|Low)") { break }
        if ($inPriority -and $line -match "^- \[ \] (.+)") {
            return $matches[1]
        }
    }
    return $null
}

function Send-TaskToCline {
    param([string]$Task)

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

    # Create task file for Cline to pick up
    $taskFile = ".ai-tasks/current-task.md"
    Set-Content -Path $taskFile -Value $prompt -Force

    # Trigger Cline via VS Code CLI
    try {
        # Open Cline and it will auto-load the task file
        code --command "cline.plusButtonClicked" 2>$null
        return $true
    }
    catch {
        Write-Host "Failed to trigger Cline: $_" -ForegroundColor Red
        return $false
    }
}

function Test-ClineRunning {
    # Check if there's an active Cline task
    $activeTaskFile = ".ai-tasks/current-task.md"
    if (Test-Path $activeTaskFile) {
        $content = Get-Content $activeTaskFile -Raw
        # If file is recent (modified in last hour), assume Cline is working
        $lastWrite = (Get-Item $activeTaskFile).LastWriteTime
        $age = (Get-Date) - $lastWrite
        return ($age.TotalHours -lt 1)
    }
    return $false
}

$lastTask = $null

while ($true) {
    try {
        # Check if Cline is already working
        if (Test-ClineRunning) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Cline is working on a task..." -ForegroundColor Yellow
            Start-Sleep -Seconds $CheckInterval
            continue
        }

        # Get next task
        $nextTask = Get-NextTask

        if ($nextTask -and $nextTask -ne $lastTask) {
            Write-Host ""
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] New task detected: $nextTask" -ForegroundColor Green
            Write-Host "Sending to Cline..." -ForegroundColor Cyan

            if (Send-TaskToCline -Task $nextTask) {
                Write-Host "✓ Task sent to Cline successfully" -ForegroundColor Green
                $lastTask = $nextTask
            }
            else {
                Write-Host "✗ Failed to send task to Cline" -ForegroundColor Red
            }
        }
        elseif (-not $nextTask) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] No pending tasks in TODO.md" -ForegroundColor Gray
        }
        else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Waiting for task completion..." -ForegroundColor Gray
        }

    }
    catch {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }

    Start-Sleep -Seconds $CheckInterval
}
