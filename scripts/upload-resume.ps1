#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Upload a resume file to the job-lead-finder API
.DESCRIPTION
    Uploads resume files (txt, md, pdf, docx) to the local server.
    Supports format validation and provides detailed error messages.
.PARAMETER ResumePath
    Path to the resume file. Defaults to resume.txt in current directory.
.PARAMETER ServerUrl
    Base URL of the server. Defaults to http://localhost:8000
.EXAMPLE
    .\upload-resume.ps1
    .\upload-resume.ps1 -ResumePath "my-resume.pdf"
    .\upload-resume.ps1 -ResumePath "resume.docx" -ServerUrl "http://localhost:8080"
#>

param(
    [Parameter(Position=0)]
    [string]$ResumePath = "resume.txt",
    
    [Parameter(Position=1)]
    [string]$ServerUrl = "http://localhost:8000"
)

# Validate file exists
if (-not (Test-Path $ResumePath)) {
    Write-Host "❌ Error: File not found: $ResumePath" -ForegroundColor Red
    exit 1
}

# Validate file extension
$validExtensions = @('.txt', '.md', '.pdf', '.docx')
$extension = [System.IO.Path]::GetExtension($ResumePath).ToLower()
if ($extension -notin $validExtensions) {
    Write-Host "❌ Error: Invalid file type. Allowed: $($validExtensions -join ', ')" -ForegroundColor Red
    exit 1
}

Write-Host "📄 Uploading: $ResumePath" -ForegroundColor Cyan

try {
    $file = Get-Item $ResumePath
    
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $fileContent = [System.IO.File]::ReadAllBytes($file.FullName)
    
    # Build multipart body
    $LF = "`r`n"
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$($file.Name)`"",
        "Content-Type: application/octet-stream",
        "",
        [System.Text.Encoding]::UTF8.GetString($fileContent),
        "--$boundary--"
    )
    $body = $bodyLines -join $LF
    
    # Make request
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/upload/resume" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    
    Write-Host "✅ Resume uploaded successfully!" -ForegroundColor Green
    Write-Host "📊 File: $($response.filename)" -ForegroundColor White
    Write-Host "📦 Size: $($response.size_bytes) bytes" -ForegroundColor White
    Write-Host "📝 Text: $($response.text_length) characters" -ForegroundColor White
    
} catch {
    Write-Host "❌ Upload failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   Details: $($errorDetail.detail)" -ForegroundColor Yellow
    }
    exit 1
}
