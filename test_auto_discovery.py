#!/usr/bin/env python3
"""Test script for automated job discovery feature.

This script:
1. Uploads a sample resume
2. Triggers auto-discovery manually
3. Checks the status and shows discovered jobs
"""

import time
from pathlib import Path

import httpx

API_BASE = "http://localhost:8000"


def test_auto_discovery():
    """Test the automated job discovery workflow."""
    print("=" * 60)
    print("Testing Automated Job Discovery")
    print("=" * 60)
    print()

    # Step 1: Upload a sample resume
    print("Step 1: Uploading sample resume...")
    sample_resume = """
John Doe
Senior Software Engineer

PROFESSIONAL SUMMARY:
Experienced software engineer with 5+ years building scalable web applications.
Passionate about Python, cloud infrastructure, and developer tools.

TECHNICAL SKILLS:
- Languages: Python, JavaScript, TypeScript, SQL
- Frameworks: Django, FastAPI, React, Node.js
- Databases: PostgreSQL, Redis, MongoDB
- Cloud: AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes
- Tools: Git, GitHub Actions, Jenkins, Terraform

EXPERIENCE:

Senior Software Engineer | TechCorp Inc. | 2021 - Present
- Built microservices architecture using FastAPI and Docker
- Implemented CI/CD pipelines with GitHub Actions
- Led team of 4 engineers on cloud migration project
- Technologies: Python, FastAPI, PostgreSQL, AWS, Docker

Software Engineer | StartupCo | 2019 - 2021
- Developed REST APIs using Django and Django REST Framework
- Optimized database queries reducing response time by 60%
- Implemented Redis caching layer for high-traffic endpoints
- Technologies: Python, Django, PostgreSQL, Redis, AWS

EDUCATION:
BS Computer Science | State University | 2019
"""

    # Save resume to file for upload
    resume_path = Path("test_resume.txt")
    resume_path.write_text(sample_resume.strip())

    try:
        with httpx.Client(timeout=30.0) as client:
            # Upload resume
            with open(resume_path, "rb") as f:
                files = {"file": ("resume.txt", f, "text/plain")}
                response = client.post(f"{API_BASE}/api/upload/resume", files=files)

            if response.status_code == 200:
                print("✓ Resume uploaded successfully")
            else:
                print(f"✗ Failed to upload resume: {response.text}")
                return
            print()

            # Step 2: Check auto-discovery status
            print("Step 2: Checking auto-discovery status...")
            response = client.get(f"{API_BASE}/api/auto-discover/status")
            status = response.json()

            print(f"  Resume uploaded: {status['resume_uploaded']}")
            print(f"  Resume size: {status['resume_size_bytes']} bytes")
            print(f"  Worker running: {status['worker_running']}")
            print(f"  Auto-discovery enabled: {status['auto_discovery_enabled']}")
            print(f"  Total tracked jobs: {status['total_tracked_jobs']}")
            print(f"  Jobs added (24h): {status['jobs_added_last_24h']}")

            if status.get("next_discovery_time"):
                print(f"  Next scheduled run: {status['next_discovery_time']}")
            print()

            if not status["worker_running"]:
                print("⚠ Warning: Background worker is not running!")
                print("  Start it with: docker compose up worker")
                print()
                print("  For testing without worker, trigger discovery manually (next step)")
                print()

            # Step 3: Manually trigger auto-discovery
            print("Step 3: Triggering auto-discovery manually...")
            response = client.post(f"{API_BASE}/api/auto-discover/trigger")

            if response.status_code == 200:
                result = response.json()
                print(f"✓ {result['message']}")
                print(f"  Note: {result.get('note', '')}")
            elif response.status_code == 503:
                print("✗ Worker not running - starting inline test instead...")
                print()
                test_inline_discovery()
                return
            else:
                print(f"✗ Failed to trigger: {response.text}")
                return
            print()

            # Step 4: Wait a bit and check for new jobs
            print("Step 4: Waiting for discovery to complete...")
            print("  (This may take 2-5 minutes depending on API response times)")
            print()

            for i in range(6):  # Wait up to 60 seconds, checking every 10
                time.sleep(10)
                print(f"  Checking... ({(i+1)*10}s)")

                response = client.get(f"{API_BASE}/api/auto-discover/status")
                status = response.json()

                if status["jobs_added_last_24h"] > 0:
                    print(f"\n✓ Found {status['jobs_added_last_24h']} new jobs!")
                    break
            else:
                print("\n⚠ Discovery still in progress or no high-scoring jobs found")
                print("  Check worker logs: docker compose logs worker --tail 50")

            print()

            # Step 5: Show tracked jobs
            print("Step 5: Showing tracked jobs...")
            response = client.get(f"{API_BASE}/api/jobs/tracked")
            tracked = response.json()

            if tracked:
                print(f"\n  Total tracked jobs: {len(tracked)}")
                print("\n  Recent jobs:")
                for job in tracked[:5]:  # Show first 5
                    score = job.get("score", "N/A")
                    print(f"\n  - {job['title']}")
                    print(f"    Company: {job['company']}")
                    print(f"    Location: {job.get('location', 'N/A')}")
                    print(f"    Score: {score}")
                    print(f"    Link: {job.get('link', 'N/A')}")
                    if len(tracked) > 5:
                        print(f"\n  ... and {len(tracked) - 5} more jobs")
            else:
                print("  No jobs tracked yet")
                print("  Note: Only jobs with score ≥ 60 are auto-tracked")

    finally:
        # Cleanup
        if resume_path.exists():
            resume_path.unlink()

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)


def test_inline_discovery():
    """Test discovery directly without background worker."""
    print("Testing auto-discovery inline (without worker)...")
    print()

    import asyncio
    import sys

    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))

    from app.background_scheduler import BackgroundScheduler

    scheduler = BackgroundScheduler()

    async def run_discovery():
        await scheduler.discover_jobs_from_resume()

    print("Running discovery...")
    asyncio.run(run_discovery())
    print("\nDiscovery complete! Check tracked jobs in the UI.")


if __name__ == "__main__":
    print("\nMake sure the UI server is running:")
    print("  docker compose up ui")
    print("\nOptionally start the worker (for scheduled discovery):")
    print("  docker compose up worker")
    print()

    try:
        test_auto_discovery()
    except httpx.ConnectError:
        print("\n✗ Error: Could not connect to API server")
        print("  Make sure the server is running: docker compose up ui")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
