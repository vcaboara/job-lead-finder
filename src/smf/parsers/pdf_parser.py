"""PDF document parser using pypdf."""
import re
from io import BytesIO
from typing import Dict, Any

from smf.parsers.base import DocumentParser


class PDFParser(DocumentParser):
    """Parser for PDF documents using pypdf library."""

    def __init__(self):
        """Initialize the PDF parser."""
        try:
            from pypdf import PdfReader
            self.PdfReader = PdfReader
            self._available = True
        except ImportError:
            self._available = False

    def parse(self, content: bytes) -> str:
        """Parse PDF content and extract text.
        
        Args:
            content: PDF file content as bytes
            
        Returns:
            Extracted and cleaned text from PDF
            
        Raises:
            Exception: If pypdf is not installed or parsing fails
        """
        if not self._available:
            raise Exception("pypdf not installed. Install with: pip install pypdf")

        try:
            pdf = self.PdfReader(BytesIO(content))
            text_parts = []

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            raw_text = "\n".join(text_parts)

            # Clean up the extracted text
            cleaned_text = self._clean_text(raw_text)

            return cleaned_text.strip()
        except Exception as exc:
            raise Exception(f"Failed to extract PDF text: {exc}") from exc

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Fix multiple spaces between words
        cleaned = re.sub(r"  +", " ", text)
        
        # Normalize line breaks
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
        
        return cleaned

    def supports_format(self, filename: str) -> bool:
        """Check if this parser supports PDF files.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if filename ends with .pdf
        """
        return filename.lower().endswith('.pdf')

    def get_metadata(self, content: bytes) -> Dict[str, Any]:
        """Extract metadata from PDF.
        
        Args:
            content: PDF file content as bytes
            
        Returns:
            Dictionary with PDF metadata (pages, title, author, etc.)
        """
        if not self._available:
            return {}

        try:
            pdf = self.PdfReader(BytesIO(content))
            metadata = {
                "pages": len(pdf.pages),
            }
            
            # Add PDF info if available
            if pdf.metadata:
                if '/Title' in pdf.metadata:
                    metadata['title'] = pdf.metadata['/Title']
                if '/Author' in pdf.metadata:
                    metadata['author'] = pdf.metadata['/Author']
            
            return metadata
        except Exception:
            return {}
