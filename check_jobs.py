from app.job_tracker import JobTracker
import json
from pathlib import Path

t = JobTracker()
print(f"Tracking file: {t.tracking_file}")
print(f"File exists: {t.tracking_file.exists()}")
if t.tracking_file.exists():
    with open(t.tracking_file) as f:
        raw_data = json.load(f)
        print(f"Raw jobs in file: {len(raw_data.get('jobs', {}))}")

print(f"Loaded jobs in tracker: {len(t.jobs)}")
print(f"Total jobs: {len(jobs := t.get_all_jobs(include_hidden=False))}")
print(f"Jobs with links: {sum(1 for j in jobs if j.get('company_link'))}")
print(
    f"Jobs needing links: {sum(1 for j in jobs if not j.get('company_link') and j.get('source') != 'CompanyJobs')}")

print("\nJob details:")
for j in jobs:
    print(
        f"  - {j.get('company')} ({j.get('source')}) - has_link: {bool(j.get('company_link'))}")
