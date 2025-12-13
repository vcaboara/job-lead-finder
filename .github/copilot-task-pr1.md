# GitHub Copilot Workspace Task

## Objective
Fix CSS variable references in Resume and Worker panels to make content visible, and add missing toast notification HTML.

## Context
The template uses CSS custom properties like `hsl(var(--primary))` but these variables are not defined in `:root`, causing invisible content in Resume and Worker panels. Need to replace with actual hex color values.

## Files to Modify
- `src/app/templates/index.html`

## Tasks

### Task 1: Replace CSS Variables in Resume Panel
**Location:** Lines ~1040-1075 (Resume Panel section with id="main-panel-resume")

Replace the following CSS variable references with actual color values:

**Color Mappings:**
- `hsl(var(--primary))` → `#3b82f6` (blue)
- `hsl(var(--muted-foreground))` → `#94a3b8` (gray)
- `hsl(var(--success))` → `#22c55e` (green)
- `hsl(var(--border))` → `#334155` (dark gray)
- `hsl(var(--muted))` → `#1e293b` (dark background)

**Specific Changes:**
1. Find all SVG elements with `stroke="hsl(var(--primary))"` and replace with `stroke="#3b82f6"`
2. Find all color styles with `color: hsl(var(--muted-foreground))` and replace with `color: #94a3b8`
3. Find all color styles with `color: hsl(var(--success))` and replace with `color: #22c55e`
4. Find border colors `border: 2px dashed hsl(var(--border))` and replace with `border: 2px dashed #334155`
5. Find background colors with `hsl(var(--muted))` and replace with `#1e293b`

### Task 2: Replace CSS Variables in Worker Panel
**Location:** Lines ~1076-1100 (Worker Panel section with id="main-panel-worker")

Apply the same color replacements as Task 1 to the Worker panel section.

### Task 3: Add Missing Toast Notification HTML
**Location:** Before the closing `</main>` tag (around line 1101)

Add this HTML structure:

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

**Placement:**
Insert this HTML between the closing `</div>` of the container div and the closing `</main>` tag.

## Verification Steps

After making changes, verify:

1. **Resume Panel:**
   - Search for remaining instances of `hsl(var(` in the Resume panel section
   - Confirm upload button SVG has `stroke="#3b82f6"`
   - Confirm textarea placeholder color is `#94a3b8`
   - Confirm any success indicators use `#22c55e`

2. **Worker Panel:**
   - Search for remaining instances of `hsl(var(` in the Worker panel section
   - Confirm heading colors are using hex values
   - Confirm log container background uses `#1e293b`

3. **Toast Element:**
   - Confirm `<div id="toast" class="toast">` exists before `</main>`
   - Confirm all child elements (toastTitle, toastMessage, toastActions) are present

## Expected Outcome

All Resume and Worker panel content should be visible with proper colors:
- Upload buttons and icons: blue (#3b82f6)
- Help text and labels: gray (#94a3b8)
- Success messages: green (#22c55e)
- Borders: dark gray (#334155)
- Background sections: dark (#1e293b)
- Toast notification HTML ready for JavaScript to populate

## Important Notes

- DO NOT change any JavaScript code
- DO NOT change any class names
- DO NOT change any ID attributes
- ONLY replace CSS variable references with hex color values
- ONLY add the toast HTML structure (no CSS or JavaScript changes)
- Keep all existing HTML structure intact
- Maintain all existing whitespace and indentation

## Search Patterns to Find Issues

Use these regex patterns to find remaining problems:
- `hsl\(var\(--[^)]+\)\)` - Finds any remaining CSS variable references
- `stroke="hsl\(var` - Finds SVG stroke colors needing replacement
- `color:\s*hsl\(var` - Finds text colors needing replacement
- `background:\s*hsl\(var` - Finds background colors needing replacement
