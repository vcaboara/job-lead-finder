"""Pytest configuration and fixtures."""

import sys
from io import BytesIO
from pathlib import Path

import pytest

# Add src directory to Python path so 'app' module can be imported
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Try to import PDF/DOCX libraries for testing
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from docx import Document
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False


@pytest.fixture
def create_test_pdf():
    """Factory fixture to create test PDF files.
    
    Returns:
        Callable that takes text and returns PDF bytes
    """
    if not REPORTLAB_AVAILABLE:
        pytest.skip("reportlab not installed")
    
    def _create_pdf(text: str) -> bytes:
        """Create a PDF from text for testing.
        
        Args:
            text: Text content to put in PDF
            
        Returns:
            PDF bytes
        """
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
    
    return _create_pdf


@pytest.fixture
def create_test_docx():
    """Factory fixture to create test DOCX files.
    
    Returns:
        Callable that takes text and returns DOCX bytes
    """
    if not PYTHON_DOCX_AVAILABLE:
        pytest.skip("python-docx not installed")
    
    def _create_docx(text: str) -> bytes:
        """Create a DOCX from text for testing.
        
        Args:
            text: Text content to put in DOCX
            
        Returns:
            DOCX bytes
        """
        doc = Document()
        for para in text.split('\n'):
            if para.strip():
                doc.add_paragraph(para)
        
        packet = BytesIO()
        doc.save(packet)
        packet.seek(0)
        return packet.getvalue()
    
    return _create_docx


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    for file in [Path("resume.txt"), Path("leads.json")]:
        if file.exists():
            file.unlink()
