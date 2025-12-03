#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reload the job-lead-finder UI server
.DESCRIPTION
    Restarts the Docker container running the UI server.
    Optionally shows logs after restart.
.PARAMETER Logs
    Show logs after reloading (last 20 lines)
.PARAMETER Follow
    Follow logs continuously after reload (Ctrl+C to stop)
.EXAMPLE
    .\reload-ui.ps1
    .\reload-ui.ps1 -Logs
    .\reload-ui.ps1 -Follow
#>

param(
    [switch]$Logs,
    [switch]$Follow
)

Write-Host "🔄 Reloading UI server..." -ForegroundColor Yellow

try {
    # Restart the UI container
    docker compose restart ui | Out-Null
    
    # Wait for container to be healthy
    Start-Sleep -Seconds 2
    
    # Check if container is running
    $containerStatus = docker compose ps ui --format json | ConvertFrom-Json
    
    if ($containerStatus.State -eq "running") {
        Write-Host "✅ UI server reloaded successfully!" -ForegroundColor Green
        Write-Host "📊 View at: http://localhost:8000" -ForegroundColor Cyan
        
        if ($Follow) {
            Write-Host "`n📜 Following logs (Ctrl+C to stop)..." -ForegroundColor Yellow
            docker compose logs ui --follow
        } elseif ($Logs) {
            Write-Host "`n📜 Recent logs:" -ForegroundColor Yellow
            docker compose logs ui --tail 20
        }
    } else {
        Write-Host "⚠️  Container restarted but may not be healthy" -ForegroundColor Yellow
        Write-Host "   Status: $($containerStatus.State)" -ForegroundColor Yellow
        Write-Host "   Run with -Logs to see what happened" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Failed to reload: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Make sure Docker is running and containers are started" -ForegroundColor Yellow
    exit 1
}
