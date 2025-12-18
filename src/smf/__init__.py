"""AI Search Match Framework (ASMF).

A reusable framework for AI-powered search and analysis applications.
Provides common infrastructure for job finding, patent evaluation, grant finding, etc.
"""

__version__ = "0.1.0"

from smf.providers import AIProviderFactory, BaseAIProvider
from smf.analyzers import BaseAnalyzer
from smf.parsers import DocumentParser, PDFParser, DOCXParser, TXTParser

__all__ = [
    "AIProviderFactory",
    "BaseAIProvider",
    "BaseAnalyzer",
    "DocumentParser",
    "PDFParser",
    "DOCXParser",
    "TXTParser",
]
