"""Integration tests comparing search results with PDF vs text resumes.

This test validates that PDF extraction quality is good enough to produce
similar search results as plain text resumes.
"""
import json
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ui_server import app

# Try to import PDF library
try:
    from pypdf import PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


@pytest.fixture(autouse=True)
def cleanup_files():
    """Clean up test files."""
    yield
    for file in [Path("resume.txt"), Path("leads.json")]:
        if file.exists():
            file.unlink()


def create_test_pdf(text: str) -> bytes:
    """Create a PDF from text for testing.
    
    Args:
        text: Text content to put in PDF
        
    Returns:
        PDF bytes
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Write text to PDF (simple line-by-line)
    y_position = 750
    for line in text.split('\n')[:50]:  # Max 50 lines to fit on page
        if y_position < 50:  # Don't go off page
            break
        can.drawString(50, y_position, line)
        y_position -= 15
    
    can.save()
    return packet.getvalue()


@pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not installed")
def test_pdf_vs_text_resume_extraction():
    """Compare PDF extraction vs text resume to ensure quality.
    
    This validates that PDF extraction produces the same content as plain text.
    Note: This test focuses on extraction quality, not search results, since
    search requires API calls that may be rate-limited.
    """
    client = TestClient(app)
    
    # Sample resume text
    resume_text = """Vincent Caboara
Senior Software Engineer
vcaboara@gmail.com

EXPERIENCE
Configuration Build Engineer at Sony Interactive Entertainment
- Design, deploy and manage CI/CD systems (Jenkins)
- Integrate source control systems (Git) and automated test frameworks
- Configure build and test infrastructure on Windows, Linux, PlayStation
- Python, Docker/Compose cross platform support

Sr. Software/Automation Engineer CI/CD at Viasat Inc
- Development pipelines that build, lint, test and deploy docker images
- Airflow DAGs and tasks to generate artifacts and reports
- Python: create scripts to automate data collection
- Docker: created makefile targets for local development

SKILLS
- Python, Docker, Jenkins, CI/CD, Git, Linux, Windows
- DevOps, Automation, Build Systems
"""

    # Test 1: Upload text resume
    files_txt = {"file": ("resume.txt", BytesIO(resume_text.encode()), "text/plain")}
    resp_upload_txt = client.post("/api/upload/resume", files=files_txt)
    assert resp_upload_txt.status_code == 200
    txt_data = resp_upload_txt.json()
    txt_resume = txt_data["resume"]
    
    print(f"\n=== TEXT RESUME ===")
    print(f"Length: {len(txt_resume)} chars")
    print(f"First 150 chars: {txt_resume[:150]}")
    
    # Test 2: Upload same content as PDF
    pdf_content = create_test_pdf(resume_text)
    files_pdf = {"file": ("resume.pdf", BytesIO(pdf_content), "application/pdf")}
    resp_upload_pdf = client.post("/api/upload/resume", files=files_pdf)
    assert resp_upload_pdf.status_code == 200
    
    # Verify PDF was extracted
    pdf_data = resp_upload_pdf.json()
    assert "resume" in pdf_data
    pdf_resume = pdf_data["resume"]
    
    print(f"\n=== PDF EXTRACTION ===")
    print(f"Original length: {len(resume_text)} chars")
    print(f"Extracted length: {len(pdf_resume)} chars")
    print(f"First 150 chars: {pdf_resume[:150]}")
    
    # Compare key terms presence
    key_terms = [
        "Vincent Caboara",
        "Software Engineer",
        "Sony Interactive Entertainment",
        "CI/CD",
        "Jenkins",
        "Docker",
        "Python",
        "Viasat",
        "DevOps"
    ]
    
    txt_found = sum(1 for term in key_terms if term.lower() in txt_resume.lower())
    pdf_found = sum(1 for term in key_terms if term.lower() in pdf_resume.lower())
    
    print(f"\n=== KEY TERMS COMPARISON ===")
    print(f"Total key terms: {len(key_terms)}")
    print(f"Text resume found: {txt_found}/{len(key_terms)}")
    print(f"PDF resume found: {pdf_found}/{len(key_terms)}")
    
    # PDF should extract at least 90% of the key terms that text has
    if txt_found > 0:
        pdf_success_rate = (pdf_found / txt_found) * 100
        print(f"PDF extraction success rate: {pdf_success_rate:.1f}%")
        assert pdf_success_rate >= 90, f"PDF only extracted {pdf_success_rate:.1f}% of key terms"
    
    # Check for quality issues
    import re
    
    # Should not have excessive spaces (3+ consecutive)
    excessive_spaces_txt = len(re.findall(r'   +', txt_resume))
    excessive_spaces_pdf = len(re.findall(r'   +', pdf_resume))
    
    print(f"\n=== QUALITY CHECKS ===")
    print(f"Excessive spaces - Text: {excessive_spaces_txt}, PDF: {excessive_spaces_pdf}")
    
    # PDF should have minimal excessive spaces (our cleaning should fix this)
    assert excessive_spaces_pdf < 10, f"PDF has {excessive_spaces_pdf} excessive space sequences"
    
    # Should not have encoding issues
    bad_chars = ['â€"', 'â€™', 'â€œ', 'â€']
    bad_chars_found = sum(1 for char in bad_chars if char in pdf_resume)
    print(f"Bad encoding chars in PDF: {bad_chars_found}")
    assert bad_chars_found == 0, "PDF has encoding issues"
    
    print(f"\n✓ PDF extraction quality validated!")


@pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not installed")  
def test_pdf_extraction_quality():
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
    print(f"\n=== EXTRACTION QUALITY ===")
    print(f"Extracted text:\n{extracted[:300]}")
    
    # Key terms should be present (case insensitive)
    key_terms = ["python", "fastapi", "django", "docker", "jenkins"]
    found_terms = []
    missing_terms = []
    
    for term in key_terms:
        if term.lower() in extracted.lower():
            found_terms.append(term)
        else:
            missing_terms.append(term)
    
    print(f"\nFound terms: {found_terms}")
    print(f"Missing terms: {missing_terms}")
    
    # At least 80% of key terms should be extracted
    success_rate = len(found_terms) / len(key_terms) * 100
    print(f"Extraction success rate: {success_rate:.1f}%")
    
    assert success_rate >= 80, f"Only {success_rate:.1f}% of key terms extracted"
    
    # Should not have excessive spaces
    # Count sequences of 3+ spaces
    import re
    excessive_spaces = len(re.findall(r'   +', extracted))
    print(f"Excessive space sequences: {excessive_spaces}")
    
    # Should be minimal (our cleaning should fix this)
    assert excessive_spaces < 10, "Too many excessive space sequences"


def test_cli_search_with_resume():
    """Test CLI search with resume parameter.
    
    This tests the CLI interface as recommended in CONTRIBUTING.md
    """
    import subprocess
    import sys
    
    # Create a test resume file
    resume_text = "Senior Python Developer with 5 years experience in DevOps and automation"
    Path("test_resume.txt").write_text(resume_text, encoding="utf-8")
    
    try:
        # Run CLI search (assuming main.py has a find command)
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
        
        print(f"\n=== CLI OUTPUT ===")
        print(f"Return code: {result.returncode}")
        print(f"Stdout:\n{result.stdout[:500]}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr[:500]}")
        
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
    # Allow running this test file directly for quick validation
    pytest.main([__file__, "-v", "-s"])
