# TODO: UI Job Tracking Improvements

**Priority**: P1 (High - User requested)
**Issue**: #147
**Complexity**: Medium
**Estimated Time**: 2-3 hours
**Auto-PR**: true
**Auto-Commit**: true

## Objective

Enhance job tracking UI with bulk actions, filtering, and CSV export capabilities.

## Context

- UI server: `src/app/ui_server.py`
- Templates: `src/app/templates/tracked_jobs.html`
- Current features: View jobs, mark as applied (one at a time)
- Need: Bulk operations, date/status filters, data export

## Tasks

### 1. Bulk Actions
- [ ] Add checkboxes to job listing table
- [ ] Implement "Select All" functionality
- [ ] Add "Bulk Mark as Applied" button
- [ ] Add "Bulk Delete" button
- [ ] Update API endpoint `/api/jobs/update-status` to handle multiple job IDs (accept array)
- [ ] Add new endpoint `/api/jobs/bulk-delete` for bulk deletion

### 2. Filtering
- [ ] Add date range picker for `applied_date` (start and end date inputs)
- [ ] Add status dropdown filter (saved, applied, interviewing, rejected)
- [ ] Add company name search box (text input with debounce)
- [ ] Implement filter logic: filters work together (AND logic)
- [ ] Update UI to show active filters with clear buttons
- [ ] Add `/api/jobs/tracked` query parameters: `?status=applied&company=Google&date_from=2025-01-01&date_to=2025-12-31`

### 3. CSV Export
- [ ] Add "Export to CSV" button
- [ ] Create `/api/jobs/export-csv` endpoint
- [ ] Include columns: company, title, location, salary, status, applied_date, notes
- [ ] Respect current filters (export filtered results)
- [ ] Proper CSV formatting with headers using Python `csv` module
- [ ] Set correct Content-Type and Content-Disposition headers

## Implementation Details

### Backend Changes (src/app/ui_server.py)

```python
@app.route("/api/jobs/bulk-update", methods=["POST"])
def bulk_update_jobs():
    """Update status for multiple jobs."""
    data = request.json
    job_ids = data.get("job_ids", [])
    status = data.get("status")
    
    for job_id in job_ids:
        tracker.update_status(job_id, status)
    
    return jsonify({"success": True, "count": len(job_ids)})

@app.route("/api/jobs/export-csv")
def export_jobs_csv():
    """Export filtered jobs to CSV."""
    # Get filters from query params
    status = request.args.get("status")
    company = request.args.get("company")
    # ... apply filters
    
    jobs = tracker.get_all_jobs(status_filter=status, include_hidden=False)
    
    # Create CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=['company', 'title', 'location', 'salary', 'status', 'applied_date', 'notes'])
    writer.writeheader()
    writer.writerows(jobs)
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=jobs.csv'
    return response
```

### Frontend Changes (src/app/templates/tracked_jobs.html)

- Add checkboxes: `<input type="checkbox" class="job-checkbox" data-job-id="{{ job.id }}">`
- Add filter inputs at top of table
- Add bulk action buttons
- Add JavaScript for:
  - Select all/none functionality
  - Filter submission with debounce (300ms)
  - CSV export with current filters
  - Bulk update API calls

## Acceptance Criteria

- [ ] Bulk select/deselect all jobs works
- [ ] Bulk mark as applied updates multiple jobs
- [ ] Date range filter works correctly
- [ ] Status dropdown filters job list
- [ ] Company name search filters in real-time (debounced)
- [ ] CSV export downloads filtered results with proper filename
- [ ] All existing functionality still works
- [ ] Mobile-responsive design maintained
- [ ] Tests added for new endpoints

## Testing

1. Run existing tests: `pytest tests/test_ui_server.py tests/test_job_tracker.py`
2. Add new tests for bulk operations and CSV export
3. Manual testing:
   - Select multiple jobs and bulk mark as applied
   - Filter by status, company, date range
   - Export filtered results to CSV
   - Verify CSV opens correctly in Excel/Google Sheets

## Expected Outcome

- Feature branch created: `feat/ui-job-tracking-improvements`
- PR opened with `[AI]` tag referencing issue #147
- All tests passing
- Code follows existing patterns in codebase

## References

- Issue: https://github.com/vcaboara/job-lead-finder/issues/147
- Flask CSV Response: https://flask.palletsprojects.com/en/2.3.x/patterns/streaming/
- Current job tracker: `src/app/job_tracker.py`
