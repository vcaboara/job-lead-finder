# Theme Color Fix Needed

## Issue
Current dark theme is **too light** compared to actual lovable.dev reference:
- Reference: https://resume-quest-06.lovable.app/
- Screenshot shows background is nearly black (~hsl(222 47% 6%) or darker)

## Current Values (TOO LIGHT)
```css
--background: 222 47% 11%;  /* Should be darker */
--card: 217 33% 17%;        /* Should be darker */
```

## Target Values (From lovable.dev screenshot)
```css
--background: 222 47% 6%;   /* Much darker, almost black */
--card: 217 33% 12%;        /* Darker cards */
```

## Files to Update
- `src/app/templates/index.html`
- `src/app/templates/dashboard.html`
- `src/app/templates/nav.html`
- `src/app/ai_monitor_ui.py`

## Decision
- [ ] Fix in current PR #71
- [ ] Create new PR for color correction
- [ ] Leave as-is (11% is more visible, even if not exact match)
