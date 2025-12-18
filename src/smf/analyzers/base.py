"""Base analyzer pattern for domain-specific analysis logic."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from smf.providers.base_provider import BaseAIProvider


class BaseAnalyzer(ABC):
    """Abstract base class for analyzers.
    
    Analyzers encapsulate domain-specific logic for analyzing and matching items
    (e.g., jobs, patents, grants) against profiles (e.g., resumes, IP portfolios).
    """

    def __init__(self, provider: BaseAIProvider):
        """Initialize the analyzer.
        
        Args:
            provider: AI provider instance to use for analysis
        """
        self.provider = provider

    @abstractmethod
    def analyze_single(self, item: Dict[str, Any], profile: str) -> Dict[str, Any]:
        """Analyze a single item against a profile.
        
        Args:
            item: Item to analyze (e.g., job, patent, grant)
            profile: Profile to match against (e.g., resume, IP portfolio)
            
        Returns:
            Analysis result with score and reasoning
        """
        pass

    def analyze_batch(
        self, items: List[Dict[str, Any]], profile: str, top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Analyze multiple items against a profile.
        
        Default implementation analyzes each item individually and sorts by score.
        Subclasses can override for more efficient batch processing.
        
        Args:
            items: List of items to analyze
            profile: Profile to match against
            top_n: Optional number of top results to return
            
        Returns:
            List of items with analysis results, sorted by score
        """
        results = []
        for item in items:
            result = self.analyze_single(item, profile)
            item_with_result = {**item, **result}
            results.append(item_with_result)
        
        # Sort by score descending
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Return top N if specified
        if top_n:
            return results[:top_n]
        return results

    @abstractmethod
    def extract_key_features(self, item: Dict[str, Any]) -> List[str]:
        """Extract key features from an item for matching.
        
        Args:
            item: Item to extract features from
            
        Returns:
            List of key features (e.g., required skills, technologies, domains)
        """
        pass

    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate that an item has required fields.
        
        Args:
            item: Item to validate
            
        Returns:
            True if item is valid, False otherwise
        """
        required_fields = self.get_required_fields()
        return all(field in item for field in required_fields)

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Get list of required fields for items.
        
        Returns:
            List of required field names
        """
        pass

    def format_for_display(self, item: Dict[str, Any]) -> str:
        """Format an item for display (e.g., in UI or logs).
        
        Args:
            item: Item to format
            
        Returns:
            Formatted string representation
        """
        # Default implementation - subclasses should override
        return str(item)
