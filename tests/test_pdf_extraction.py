"""Integration tests for PDF extraction quality validation.

This test validates that PDF extraction produces clean, searchable text.
"""
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.ui_server import app


def test_pdf_extraction_quality(create_test_pdf):
    """Test that PDF extraction produces clean, searchable text."""
    client = TestClient(app)
    
    # Create resume with known content
    resume_text = """John Doe
Senior Python Developer
john.doe@example.com

EXPERIENCE
Python Developer at Tech Company (2020-2023)
- Developed REST APIs using FastAPI and Django
- Implemented CI/CD pipelines with Jenkins and Docker
- Managed PostgreSQL databases and Redis cache

SKILLS
Python, FastAPI, Django, Docker, Jenkins, PostgreSQL, Redis, Git
"""
    
    # Upload as PDF
    pdf_content = create_test_pdf(resume_text)
    files = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    resp = client.post("/api/upload/resume", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    extracted = data["resume"]
    
    # Validate extraction quality
    # Key terms should be present (case insensitive)
    key_terms = ["python", "fastapi", "django", "docker", "jenkins"]
    found_terms = [term for term in key_terms if term.lower() in extracted.lower()]
    
    # At least 80% of key terms should be extracted
    success_rate = len(found_terms) / len(key_terms) * 100
    assert success_rate >= 80, f"Only {success_rate:.1f}% of key terms extracted"
    
    # Should not have excessive spaces (3+ consecutive)
    import re
    excessive_spaces = len(re.findall(r'   +', extracted))
    assert excessive_spaces < 10, "Too many excessive space sequences"


def test_pdf_vs_text_resume_extraction(create_test_pdf):
    """Compare PDF extraction vs text resume to ensure quality."""
    client = TestClient(app)
    
    # Sample resume text
    resume_text = """Vincent Caboara
Senior Software Engineer
vcaboara@gmail.com

EXPERIENCE
Configuration Build Engineer at Sony Interactive Entertainment
- Design, deploy and manage CI/CD systems (Jenkins)
- Python, Docker/Compose cross platform support

SKILLS
- Python, Docker, Jenkins, CI/CD, Git, DevOps
"""

    # Upload text resume
    files_txt = {"file": ("resume.txt", BytesIO(resume_text.encode()), "text/plain")}
    resp_upload_txt = client.post("/api/upload/resume", files=files_txt)
    assert resp_upload_txt.status_code == 200
    txt_resume = resp_upload_txt.json()["resume"]
    
    # Upload same content as PDF
    pdf_content = create_test_pdf(resume_text)
    files_pdf = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    resp_upload_pdf = client.post("/api/upload/resume", files=files_pdf)
    assert resp_upload_pdf.status_code == 200
    pdf_resume = resp_upload_pdf.json()["resume"]
    
    # Compare key terms presence
    key_terms = [
        "Vincent Caboara",
        "Software Engineer",
        "Sony Interactive Entertainment",
        "Jenkins",
        "Docker",
        "Python"
    ]
    
    txt_found = sum(1 for term in key_terms if term.lower() in txt_resume.lower())
    pdf_found = sum(1 for term in key_terms if term.lower() in pdf_resume.lower())
    
    # PDF should extract at least 90% of the key terms that text has
    if txt_found > 0:
        pdf_success_rate = (pdf_found / txt_found) * 100
        assert pdf_success_rate >= 90, f"PDF only extracted {pdf_success_rate:.1f}% of key terms"
    
    # Check for encoding issues
    bad_chars = ['â€"', 'â€™', 'â€œ', 'â€']
    bad_chars_found = sum(1 for char in bad_chars if char in pdf_resume)
    assert bad_chars_found == 0, "PDF has encoding issues"


@patch('app.job_finder.generate_job_leads')
def test_cli_search_with_resume(mock_generate_leads):
    """Test CLI search with resume parameter (mocked API)."""
    import subprocess
    import sys
    from pathlib import Path
    
    # Mock API response to avoid rate limiting
    mock_generate_leads.return_value = [
        {
            "title": "Python Developer",
            "company": "Tech Corp",
            "link": "https://example.com/job1",
            "location": "Remote"
        }
    ]
    
    # Create a test resume file
    resume_text = "Senior Python Developer with 5 years experience"
    Path("test_resume.txt").write_text(resume_text, encoding="utf-8")
    
    try:
        # Run CLI search
        result = subprocess.run(
            [
                sys.executable, "-m", "app.main", "find",
                "-q", "python developer",
                "--resume", resume_text,
                "-n", "3"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should complete successfully
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Output should mention jobs
        output = result.stdout.lower()
        assert "job" in output or "lead" in output or "found" in output
        
    finally:
        # Cleanup
        if Path("test_resume.txt").exists():
            Path("test_resume.txt").unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
