# Development Scripts

Utility scripts to streamline job-lead-finder development workflow.

## Quick Start

```powershell
# Run this once to set up aliases
.\scripts\dev-setup.ps1

# Reload your PowerShell profile
. $PROFILE
```

## Scripts

### `dev-setup.ps1`
Sets up PowerShell aliases for development. Run once per machine.

**Usage:**
```powershell
.\scripts\dev-setup.ps1
```

### `upload-resume.ps1`
Upload a resume file to the API.

**Usage:**
```powershell
.\scripts\upload-resume.ps1                          # Uploads resume.txt
.\scripts\upload-resume.ps1 my-resume.pdf           # Upload specific file
.\scripts\upload-resume.ps1 resume.docx http://localhost:8080  # Custom server

# After setup, use alias:
jl-upload my-resume.pdf
```

**Supported formats:** `.txt`, `.md`, `.pdf`, `.docx`

### `search-jobs.ps1`
Search for job leads via API.

**Usage:**
```powershell
.\scripts\search-jobs.ps1 "python developer"        # Basic search
.\scripts\search-jobs.ps1 "DevOps engineer" 20      # Get 20 results
.\scripts\search-jobs.ps1 "fullstack" -SaveTo results.json  # Save results

# After setup, use alias:
jl-search "python developer"
jl-search "senior DevOps" 15
```

### `reload-ui.ps1`
Restart the UI Docker container.

**Usage:**
```powershell
.\scripts\reload-ui.ps1            # Simple reload
.\scripts\reload-ui.ps1 -Logs      # Show logs after reload
.\scripts\reload-ui.ps1 -Follow    # Follow logs (Ctrl+C to stop)

# After setup, use alias:
jl-reload
jl-reload -Logs
```

## Aliases Reference

After running `dev-setup.ps1`, you'll have these shortcuts:

### Git Shortcuts
- `gco <branch>` - Checkout branch
- `gcb <branch>` - Create and checkout new branch
- `gaa` - Add all changes
- `gcm "message"` - Commit with message
- `gp` - Push to remote
- `gpu` - Push and set upstream
- `gs` - Status
- `gd` - Diff
- `gl` - Log (last 10 commits)
- `gpl` - Pull

### GitHub CLI
- `ghpr <base> <title> <body>` - Create PR
- `ghprl` - List PRs
- `ghprv [number]` - View PR
- `ghprc` - Check PR status

### Testing
- `jl-test [args]` - Run pytest
- `jl-cov [args]` - Run with coverage report

### Docker
- `jl-up` - Start containers
- `jl-down` - Stop containers
- `jl-logs` - View UI logs
- `jl-ps` - List containers

### Project Tools
- `jl-upload [file]` - Upload resume
- `jl-search "query" [count]` - Search jobs
- `jl-reload [-Logs]` - Reload UI
- `jl-cd` - Navigate to project root

## Examples

### Typical Development Workflow

```powershell
# 1. Create feature branch
gcb feature/new-feature

# 2. Make changes...

# 3. Test locally
jl-test tests/test_my_feature.py

# 4. Reload UI to see changes
jl-reload -Logs

# 5. Test the API
jl-upload my-resume.pdf
jl-search "python developer" 10

# 6. Commit and push
gaa
gcm "feat: add new feature"
gpu

# 7. Create PR
ghpr main "feat: New feature" "Description here"
```

### Quick Testing Session

```powershell
# Start fresh
jl-down
jl-up

# Upload test resume
jl-upload test-resume.txt

# Search and save results
jl-search "senior developer" 20 -SaveTo test-results.json

# Check logs if issues
jl-logs
```

## Troubleshooting

**Aliases not working?**
```powershell
# Reload your profile
. $PROFILE

# Or re-run setup
.\scripts\dev-setup.ps1
```

**Scripts can't find files?**
```powershell
# Make sure you're in the project root
jl-cd

# Or use full paths
C:\Users\vcabo\job-lead-finder\scripts\upload-resume.ps1
```

**Docker errors?**
```powershell
# Check Docker is running
docker ps

# Restart containers
jl-down
jl-up
```
