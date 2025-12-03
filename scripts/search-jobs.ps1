#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Search for job leads via the job-lead-finder API
.DESCRIPTION
    Triggers a job search and displays results in a formatted table.
    Optionally saves results to a JSON file.
.PARAMETER Query
    Job search query (e.g., "python developer", "senior DevOps engineer")
.PARAMETER Count
    Number of job leads to find. Defaults to 10.
.PARAMETER ServerUrl
    Base URL of the server. Defaults to http://localhost:8000
.PARAMETER SaveTo
    Optional path to save results as JSON
.EXAMPLE
    .\search-jobs.ps1 -Query "python developer"
    .\search-jobs.ps1 -Query "DevOps engineer" -Count 20
    .\search-jobs.ps1 -Query "fullstack" -SaveTo "results.json"
#>

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$Query,
    
    [Parameter(Position=1)]
    [int]$Count = 10,
    
    [Parameter()]
    [string]$ServerUrl = "http://localhost:8000",
    
    [Parameter()]
    [string]$SaveTo = ""
)

Write-Host "🔍 Searching for: '$Query' (max $Count results)" -ForegroundColor Cyan
Write-Host "⏳ Please wait..." -ForegroundColor Yellow

try {
    $body = @{
        query = $Query
        num_leads = $Count
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 120  # 2 minute timeout for long searches
    
    $leadCount = $response.leads.Count
    Write-Host "`n✅ Found $leadCount job lead$(if($leadCount -ne 1){'s'})!" -ForegroundColor Green
    
    if ($leadCount -gt 0) {
        Write-Host "`n📋 Results:" -ForegroundColor White
        $response.leads | Format-Table -Property @(
            @{Label="Title"; Expression={$_.title}; Width=40},
            @{Label="Company"; Expression={$_.company}; Width=25},
            @{Label="Location"; Expression={$_.location}; Width=20},
            @{Label="Source"; Expression={$_.source}; Width=15}
        ) -AutoSize
        
        # Save if requested
        if ($SaveTo) {
            $response | ConvertTo-Json -Depth 10 | Out-File -FilePath $SaveTo -Encoding UTF8
            Write-Host "💾 Saved to: $SaveTo" -ForegroundColor Green
        }
        
        Write-Host "`n🔗 Full results saved to: leads.json" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "`n❌ Search failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Details: $($errorDetail.detail)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
    exit 1
}
