# UI Improvements TODO

This document tracks needed UI/UX improvements after reverting the incomplete lovable.dev redesign.

## Current Status
✅ **Working:** All core functionality is operational
- Search Jobs tab displays results
- Track button adds jobs to tracker with toast notification
- Tracker tab shows tracked jobs with status management
- Resume tab has upload dropzone and textarea
- Worker tab shows background worker status
- Settings modal works
- Theme toggle works
- Non-blocking search (can switch tabs during search)

❌ **Reverted:** lovable.dev design implementation was incomplete and caused multiple panels to break

## High Priority Fixes

### 1. Resume Panel Visibility Issues
**Problem:** Resume panel content may not be fully visible due to CSS variable references
**Files:** `src/app/templates/index.html`
**Changes Needed:**
- Replace all `hsl(var(--primary))` with actual color values (e.g., `#3b82f6`)
- Replace all `hsl(var(--muted-foreground))` with `#94a3b8`
- Replace all `hsl(var(--success))` with `#22c55e`
- Replace background gradients using CSS variables with rgba values
- Ensure dropzone border uses solid color `#334155` not `hsl(var(--border))`

**Testing:**
- Click Resume tab
- Verify upload dropzone is visible with dashed border
- Verify "Drop your resume here" text is visible
- Verify textarea is visible with placeholder text
- Verify Pro Tips section has visible gradient background

### 2. Worker Panel Content
**Problem:** Worker panel may have similar CSS variable issues
**Files:** `src/app/templates/index.html`
**Changes Needed:**
- Fix all color references in Worker panel section
- Ensure status indicators use solid colors
- Fix log display text colors

### 3. Toast Notification Missing HTML
**Problem:** Toast notification HTML element was removed during revert
**Files:** `src/app/templates/index.html`
**Fix:** Add before `</main>` closing tag:
```html
<!-- Toast Notification -->
<div id="toast" class="toast">
    <div class="toast-content">
        <div>
            <div id="toastTitle" class="toast-title"></div>
            <div id="toastMessage" class="toast-message"></div>
        </div>
        <div id="toastActions" class="toast-actions"></div>
    </div>
</div>
```

## Medium Priority Improvements

### 4. Enhanced Search Experience
**Current:** Basic form with immediate results
**Desired:** Hero section with quick search chips
**Changes:**
- Add hero section with gradient title "Find Your Perfect Role"
- Add quick search chips (Remote Engineer, Product Manager, etc.)
- Improve search button styling with gradient
- Add visual feedback during search

### 5. Job Card Enhancements
**Current:** Basic card layout
**Desired:** Modern card design with better visual hierarchy
**Changes:**
- Add match score color coding (green ≥80%, yellow ≥60%, gray <60%)
- Add hover effects with subtle lift animation
- Improve spacing and typography
- Add company link button with icon

### 6. Tracker Panel Improvements
**Current:** Basic list view
**Desired:** Kanban-style with stats dashboard
**Changes:**
- Add stats overview cards (Saved, Applied, Interviewing, Offer, Rejected)
- Color-code stats cards to match status
- Improve job card design in tracker
- Add inline status dropdown
- Add notes toggle with textarea

## Low Priority / Future Enhancements

### 7. Loading States
**Current:** Status message
**Desired:** Better loading indicators
**Changes:**
- Animated spinner for search
- Skeleton cards while loading
- Progress indication for multi-step operations

### 8. Empty States
**Current:** Simple text message
**Desired:** Helpful empty states with CTAs
**Changes:**
- Search: "Ready to find your next role" with magnifying glass icon
- Tracker: "No tracked jobs yet" with CTA to search
- Resume: Prominent upload prompt when empty

### 9. Responsive Design
**Current:** Desktop-focused
**Desired:** Mobile-responsive
**Changes:**
- Mobile menu for navigation tabs
- Responsive grid for job cards
- Touch-friendly buttons and inputs
- Adjust spacing for mobile viewports

### 10. Accessibility
**Current:** Basic HTML semantics
**Desired:** Full WCAG AA compliance
**Changes:**
- Add ARIA labels to interactive elements
- Ensure keyboard navigation works
- Add focus indicators
- Test with screen readers
- Improve color contrast ratios

## Implementation Strategy

### Phase 1: Critical Fixes (Do First)
1. Fix Resume panel CSS variables → Make panel fully visible
2. Fix Worker panel CSS variables → Ensure content displays
3. Add toast notification HTML → Make Track button work
4. Test all panels work after fixes

### Phase 2: Core UX Improvements
1. Enhanced search experience (hero + chips)
2. Job card enhancements (colors, animations)
3. Tracker stats dashboard
4. Better loading states

### Phase 3: Polish & Accessibility
1. Empty states with helpful CTAs
2. Responsive design for mobile
3. Accessibility improvements
4. Animation polish

## Testing Checklist

After each change, verify:
- [ ] All tabs switch correctly (Search, Tracker, Resume, Worker)
- [ ] Search returns results and displays them
- [ ] Track button shows toast and adds to tracker
- [ ] Tracker shows jobs with editable status
- [ ] Resume upload dropzone is visible and functional
- [ ] Worker status loads and displays
- [ ] Settings modal opens and saves
- [ ] Theme toggle switches between light/dark
- [ ] No console errors in browser DevTools
- [ ] All text is readable (no white-on-white or black-on-black)

## Notes

- **CSS Variables:** The current template uses CSS custom properties (e.g., `var(--primary)`) but they may not be defined in `:root`, causing invisible content
- **Container Rebuilds:** Always run `docker compose build ui && docker compose up -d` after HTML changes
- **Browser Cache:** Hard refresh (Ctrl+F5) needed to see changes
- **Debug Logging:** Tab switching has console.log statements for debugging - remove before production
- **Incremental Changes:** Make one change at a time and test thoroughly before moving to next item
