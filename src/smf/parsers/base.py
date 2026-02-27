"""Base document parser interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class DocumentParser(ABC):
    """Abstract base class for document parsers.
    
    All parsers should inherit from this class and implement the required methods.
    """

    @abstractmethod
    def parse(self, content: bytes) -> str:
        """Parse document content and extract text.
        
        Args:
            content: Document file content as bytes
            
        Returns:
            Extracted text from the document
            
        Raises:
            Exception: If parsing fails
        """
        pass

    @abstractmethod
    def supports_format(self, filename: str) -> bool:
        """Check if this parser supports the given file format.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass

    def get_metadata(self, content: bytes) -> Dict[str, Any]:
        """Extract metadata from the document (optional).
        
        Args:
            content: Document file content as bytes
            
        Returns:
            Dictionary of metadata (empty by default)
        """
        return {}
