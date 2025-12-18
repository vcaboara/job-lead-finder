"""Job lead analyzer using ASMF BaseAnalyzer pattern."""
import logging
from typing import Any, Dict, List

from smf.analyzers import BaseAnalyzer
from smf.providers import BaseAIProvider

logger = logging.getLogger(__name__)


class JobLeadAnalyzer(BaseAnalyzer):
    """Analyzer for job leads - matches jobs against candidate resumes."""

    def __init__(self, provider: BaseAIProvider):
        """Initialize job lead analyzer.
        
        Args:
            provider: AI provider for analysis
        """
        super().__init__(provider)

    def analyze_single(self, item: Dict[str, Any], profile: str) -> Dict[str, Any]:
        """Analyze a single job against a candidate's resume.
        
        Args:
            item: Job dictionary with title, company, description, etc.
            profile: Candidate's resume text
            
        Returns:
            Dict with 'score' (0-100) and 'reasoning'
        """
        try:
            result = self.provider.evaluate(item, profile)
            return result
        except Exception as e:
            logger.error(f"Failed to analyze job: {e}")
            return {"score": 0, "reasoning": f"Analysis failed: {str(e)}"}

    def analyze_batch(
        self, items: List[Dict[str, Any]], profile: str, top_n: int | None = None
    ) -> List[Dict[str, Any]]:
        """Analyze multiple jobs against a candidate's resume.
        
        Uses batch ranking if provider supports it (more efficient than individual analysis).
        
        Args:
            items: List of job dictionaries
            profile: Candidate's resume text
            top_n: Optional number of top results to return
            
        Returns:
            List of jobs with scores and reasoning, sorted by score
        """
        # Check if provider has optimized batch ranking
        if hasattr(self.provider, 'rank_jobs_batch') and top_n:
            try:
                return self.provider.rank_jobs_batch(items, profile, top_n)
            except Exception as e:
                logger.warning(f"Batch ranking failed, falling back to individual analysis: {e}")
        
        # Fall back to parent implementation (individual analysis)
        return super().analyze_batch(items, profile, top_n)

    def extract_key_features(self, item: Dict[str, Any]) -> List[str]:
        """Extract key features from a job posting.
        
        Args:
            item: Job dictionary
            
        Returns:
            List of key features (skills, technologies, etc.)
        """
        features = []
        
        # Extract from title
        if 'title' in item:
            features.append(f"Title: {item['title']}")
        
        # Extract from description/summary
        description = item.get('description', item.get('summary', ''))
        if description:
            # Simple keyword extraction (could be enhanced with NLP)
            keywords = [
                'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker',
                'Kubernetes', 'SQL', 'MongoDB', 'Machine Learning', 'AI', 'DevOps',
                'Senior', 'Junior', 'Mid-level', 'Remote', 'Full-time', 'Contract'
            ]
            for keyword in keywords:
                if keyword.lower() in description.lower():
                    features.append(keyword)
        
        return features

    def get_required_fields(self) -> List[str]:
        """Get required fields for job items.
        
        Returns:
            List of required field names
        """
        return ['title', 'company']

    def format_for_display(self, item: Dict[str, Any]) -> str:
        """Format a job for display.
        
        Args:
            item: Job dictionary
            
        Returns:
            Formatted string representation
        """
        title = item.get('title', 'Unknown')
        company = item.get('company', 'Unknown')
        location = item.get('location', 'N/A')
        score = item.get('score', 'N/A')
        
        result = f"{title} at {company} ({location})"
        if score != 'N/A':
            result += f" - Score: {score}/100"
        
        return result
