# Start Cline Auto-Development Service
# Runs in background and automatically feeds tasks to Cline

$servicePath = "$PSScriptRoot\cline_autodev_service.ps1"
$jobName = "ClineAutoDev"

# Check if already running
$existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Cline AutoDev service is already running" -ForegroundColor Yellow
    Write-Host "Job ID: $($existing.Id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To view output: Receive-Job -Name $jobName -Keep" -ForegroundColor Cyan
    Write-Host "To stop: Stop-Job -Name $jobName; Remove-Job -Name $jobName" -ForegroundColor Cyan
    exit 0
}

# Start as background job
Write-Host "Starting Cline Auto-Development Service..." -ForegroundColor Cyan
$job = Start-Job -Name $jobName -FilePath $servicePath -ArgumentList 300

Write-Host "✓ Service started successfully" -ForegroundColor Green
Write-Host "Job ID: $($job.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  View output:  Receive-Job -Name $jobName -Keep" -ForegroundColor White
Write-Host "  Stop service: Stop-Job -Name $jobName; Remove-Job -Name $jobName" -ForegroundColor White
Write-Host "  Check status: Get-Job -Name $jobName" -ForegroundColor White
Write-Host ""
Write-Host "The service will automatically:" -ForegroundColor Cyan
Write-Host "  • Monitor TODO.md for new tasks" -ForegroundColor Gray
Write-Host "  • Send tasks to Cline automatically" -ForegroundColor Gray
Write-Host "  • Check every 5 minutes" -ForegroundColor Gray
Write-Host "  • No manual copy/paste needed" -ForegroundColor Gray
