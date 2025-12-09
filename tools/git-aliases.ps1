# Git Aliases and Helper Functions for PowerShell
# Source this file in your PowerShell profile or run it in your session

# Delete all local branches except main (safe - only deletes merged branches)
function git-clean-branches {
    git branch | Where-Object { $_ -notmatch 'main|\*' } | ForEach-Object { git branch -d $_.Trim() }
}

# Delete all local branches except main (force - deletes even unmerged branches)
function git-clean-branches-force {
    git branch | Where-Object { $_ -notmatch 'main|\*' } | ForEach-Object { git branch -D $_.Trim() }
}

# Preview what branches would be deleted
function git-list-branches-to-clean {
    git branch | Where-Object { $_ -notmatch 'main|\*' } | ForEach-Object { $_.Trim() }
}

# Usage:
# git-list-branches-to-clean    # Preview branches that would be deleted
# git-clean-branches             # Delete merged branches (safe)
# git-clean-branches-force       # Delete all branches including unmerged (dangerous)
