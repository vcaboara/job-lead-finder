"""Plain text document parser."""
from typing import Dict, Any

from smf.parsers.base import DocumentParser


class TXTParser(DocumentParser):
    """Parser for plain text documents."""

    def parse(self, content: bytes) -> str:
        """Parse text content.
        
        Args:
            content: Text file content as bytes
            
        Returns:
            Decoded text content
            
        Raises:
            Exception: If decoding fails
        """
        try:
            # Try UTF-8 first
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                return content.decode('latin-1')
            except Exception as exc:
                raise Exception(f"Failed to decode text file: {exc}") from exc

    def supports_format(self, filename: str) -> bool:
        """Check if this parser supports text files.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if filename ends with .txt or .md
        """
        lower_name = filename.lower()
        return lower_name.endswith('.txt') or lower_name.endswith('.md')

    def get_metadata(self, content: bytes) -> Dict[str, Any]:
        """Extract metadata from text file.
        
        Args:
            content: Text file content as bytes
            
        Returns:
            Dictionary with basic metadata (size, lines, etc.)
        """
        try:
            text = self.parse(content)
            return {
                "size_bytes": len(content),
                "lines": len(text.splitlines()),
                "chars": len(text),
            }
        except Exception:
            return {}
