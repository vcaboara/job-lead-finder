"""Discovery provider implementations.

Each provider implements BaseDiscoveryProvider to discover companies
from different sources.
"""

from .jsearch_provider import JSearchProvider

__all__ = ["JSearchProvider"]
