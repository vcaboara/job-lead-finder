# Instructions to Merge PR #44

## Current Situation
- **PR #44** adds toast notifications and fixes CSS variables
- **Base branch**: `fix/panel-css-variables` has Worker/Resume panels not in `main`
- **Your main**: Has auto-discovery feature but lacks the UI panels PR #44 modifies

## Conflicts
The following elements in PR #44 don't exist in your current main:
- Worker logs panel (`#workerLogs`)
- Worker status indicators
- Resume upload panel
- These CSS variable references: `hsl(var(--success))`, `hsl(var(--destructive))`

## Resolution Options

### Option 1: Merge feature/resume-and-workers First (RECOMMENDED)

```powershell
# 1. Checkout main and pull latest
git checkout main
git pull origin main

# 2. Merge the feature branch that has Worker/Resume panels
git fetch origin feature/resume-and-workers
git merge origin/feature/resume-and-workers

# 3. Resolve any conflicts (likely minimal)
# 4. Test the UI

# 5. Now rebase PR #44's branch
git fetch origin copilot/fix-css-variables-add-toast-html
git checkout -b pr44-rebased origin/copilot/fix-css-variables-add-toast-html
git rebase main

# 6. Resolve conflicts and test
# 7. Push and update PR #44
```

### Option 2: Cherry-pick Toast System Only

If you want just the toast notifications without Worker/Resume panels:

```powershell
# Extract the toast-related changes from PR #44
git checkout main
git checkout -b feature/toast-notifications

# Manually add toast HTML before </main>:
```

Add this HTML before `</main>` tag in `src/app/templates/index.html`:

```html
<!-- Toast Notification -->
<div id="toast" class="toast hidden">
  <div class="toast-content">
    <div class="toast-message">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="toast-icon">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <span id="toastText">Job Tracked</span>
    </div>
    <button id="toastAction" class="toast-action">View in Tracker</button>
  </div>
</div>
```

Add this CSS in a `<style>` block:

```css
/* === Toast Notification === */
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  padding: 1rem 1.5rem;
  box-shadow: var(--shadow-xl);
  animation: slideInRight 0.3s ease-out;
  min-width: 300px;
}

.toast.hidden {
  display: none;
}

.toast-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.toast-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

.toast-icon {
  color: #22c55e;
  flex-shrink: 0;
}

.toast-action {
  background: var(--gradient-primary);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.toast-action:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-md);
}

@media (max-width: 768px) {
  .toast {
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
    min-width: auto;
  }
}
```

Add these JavaScript functions:

```javascript
function showToast(message, actionText, onAction) {
  const toast = document.getElementById('toast');
  const toastText = document.getElementById('toastText');
  const toastAction = document.getElementById('toastAction');

  toastText.textContent = message;
  toastAction.textContent = actionText;
  toast.classList.remove('hidden');

  // Set up action button
  toastAction.onclick = () => {
    if (onAction) onAction();
    hideToast();
  };

  // Auto-hide after 5 seconds
  setTimeout(hideToast, 5000);
}

function hideToast() {
  document.getElementById('toast').classList.add('hidden');
}
```

Update the `trackJob` function to use toast instead of status message:

```javascript
// Replace this line:
showStatus(`${job.title} added to tracker`, 'success');

// With this:
showToast('Job Tracked', 'View in Tracker', () => {
  const trackerTab = document.querySelector('.main-tab[data-panel="tracker"]');
  if (trackerTab) trackerTab.click();
});
```

## Testing After Merge

```powershell
# Start the UI server
docker compose up ui

# Test toast notifications:
# 1. Search for jobs
# 2. Click "Track" button on a job
# 3. Toast should appear bottom-right
# 4. Click "View in Tracker" - should switch to Tracker tab
# 5. Toast auto-dismisses after 5 seconds
```

## My Recommendation

Go with **Option 1** - merge `feature/resume-and-workers` first. This gives you:
- Worker status panel (useful for monitoring auto-discovery)
- Resume upload UI improvements
- Toast notifications
- Consistent codebase

The auto-discovery feature we just added will work great with the Worker panel UI!
