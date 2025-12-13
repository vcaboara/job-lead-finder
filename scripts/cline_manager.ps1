# Cline Manager - Automation utilities for Cline-based development
# Usage: .\scripts\cline_manager.ps1 [command]

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'status', 'next-task', 'stop', 'config')]
    [string]$Command = 'start'
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host $msg -ForegroundColor Red }

# Check if Cline is installed
function Test-ClineInstalled {
    $extensions = code --list-extensions
    return $extensions -match "saoudrizwan.claude-dev"
}

# Get next task from TODO.md
function Get-NextTask {
    $todoPath = "TODO.md"
    if (-not (Test-Path $todoPath)) {
        Write-Error "TODO.md not found!"
        return $null
    }

    $content = Get-Content $todoPath -Raw
    $lines = Get-Content $todoPath

    # Find first unchecked task in Immediate or High Priority
    $inImmediateOrHigh = $false
    foreach ($line in $lines) {
        if ($line -match "^## (Immediate|High Priority)") {
            $inImmediateOrHigh = $true
            continue
        }
        if ($line -match "^## (Medium|Low)") {
            $inImmediateOrHigh = $false
        }
        if ($inImmediateOrHigh -and $line -match "^- \[ \] (.+)") {
            return $matches[1]
        }
    }

    return $null
}

# Check service status
function Get-ServiceStatus {
    Write-Info "`n🔍 Checking services..."

    $services = @{
        "PR Monitor" = "job-lead-finder-pr-monitor-1"
        "Vibe Check MCP" = "vibe-check-mcp-mcp-server-1"
        "Vibe Kanban" = "job-lead-finder-vibe-kanban-mcp-1"
    }

    foreach ($service in $services.GetEnumerator()) {
        $status = docker ps --filter "name=$($service.Value)" --format "{{.Status}}" 2>$null
        if ($status) {
            Write-Success "✅ $($service.Key): Running"
        } else {
            Write-Warning "⚠️  $($service.Key): Not running"
        }
    }
}

# Start Cline with task
function Start-ClineWithTask {
    param([string]$task)

    if (-not (Test-ClineInstalled)) {
        Write-Error "Cline extension not installed!"
        Write-Info "Install from: https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev"
        exit 1
    }

    Write-Info "`n🚀 Starting Cline automated development...`n"

    # Check services
    Get-ServiceStatus

    # Get next task
    if (-not $task) {
        $task = Get-NextTask
    }

    if ($task) {
        Write-Success "`n📋 Next task: $task`n"

        # Create Cline prompt file
        $prompt = @"
Read TODO.md and work on the following task autonomously:

**Task**: $task

**Instructions**:
1. Read Memory Bank files from .claude/settings.json
2. Follow the workflow defined in .claude/settings.json
3. Implement the task with tests
4. Update Memory Bank when complete
5. Create a PR with [AI] tag when done

Follow all guidelines in .claude/settings.json for autonomous execution.
"@

        $prompt | Set-Content -Path ".cline-task.txt" -Encoding UTF8

        Write-Info "📝 Task prompt saved to .cline-task.txt"
        Write-Info "`n🎯 Next steps:"
        Write-Host "  1. Open Cline in VS Code (Ctrl+Shift+P -> 'Cline: Open')" -ForegroundColor White
        Write-Host "  2. Paste the following into Cline chat:" -ForegroundColor White
        Write-Host "`n" -NoNewline
        Write-Host $prompt -ForegroundColor Yellow
        Write-Host "`n"
        Write-Success "Cline will work autonomously with maxIterations=50"

    } else {
        Write-Warning "⚠️  No unchecked tasks found in TODO.md (Immediate or High Priority)"
    }
}

# Show Cline configuration
function Show-ClineConfig {
    Write-Info "`n⚙️  Cline Configuration"
    Write-Info "========================`n"

    if (Test-Path ".claude/settings.json") {
        $config = Get-Content ".claude/settings.json" -Raw | ConvertFrom-Json

        Write-Host "Autonomous Mode: " -NoNewline
        if ($config.autonomousMode.enabled) {
            Write-Success "✅ Enabled"
        } else {
            Write-Warning "⚠️  Disabled"
        }

        Write-Host "Max Iterations: " -NoNewline
        Write-Host $config.autonomousMode.maxIterations -ForegroundColor Cyan

        Write-Host "Auto Commit: " -NoNewline
        if ($config.autonomousMode.autoCommit) {
            Write-Success "✅ Yes"
        } else {
            Write-Host "No" -ForegroundColor Gray
        }

        Write-Host "Auto PR: " -NoNewline
        if ($config.autonomousMode.autoPR) {
            Write-Success "✅ Yes"
        } else {
            Write-Host "No" -ForegroundColor Gray
        }

        Write-Info "`nTask Sources:"
        foreach ($source in $config.taskSources) {
            Write-Host "  - $($source.path) (priority: $($source.priority))" -ForegroundColor Cyan
        }

        Write-Info "`nMCP Servers:"
        foreach ($server in $config.mcpServers.PSObject.Properties) {
            Write-Host "  - $($server.Name): $($server.Value.url)" -ForegroundColor Cyan
        }
    } else {
        Write-Error ".claude/settings.json not found!"
    }
}

# Main command router
switch ($Command) {
    'start' {
        Start-ClineWithTask
    }
    'next-task' {
        $task = Get-NextTask
        if ($task) {
            Write-Success "📋 Next task: $task"
        } else {
            Write-Warning "No unchecked tasks found in Immediate or High Priority"
        }
    }
    'status' {
        Get-ServiceStatus
        Write-Info "`n📋 Next task:"
        $task = Get-NextTask
        if ($task) {
            Write-Host "  $task" -ForegroundColor Cyan
        } else {
            Write-Host "  No unchecked tasks in Immediate/High Priority" -ForegroundColor Gray
        }
    }
    'config' {
        Show-ClineConfig
    }
    'stop' {
        Write-Warning "`n⚠️  Note: Cline runs in VS Code - close the Cline panel to stop"
        Write-Info "To stop services: docker compose stop"
    }
}
