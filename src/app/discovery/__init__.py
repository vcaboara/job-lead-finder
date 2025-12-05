"""Company discovery system for finding job opportunities beyond traditional aggregators.

This module provides infrastructure for discovering companies through various sources
(HN, YC, GitHub, etc.) and monitoring their careers pages for new opportunities.
"""

from .base_provider import (
    BaseDiscoveryProvider,
    Company,
    CompanySize,
    DiscoveryResult,
    IndustryType,
)
from .company_store import CompanyStore
from .config import (
    get_database_path,
    get_discovery_config,
    is_discovery_enabled,
    update_discovery_config,
)

__all__ = [
    "BaseDiscoveryProvider",
    "Company",
    "CompanySize",
    "CompanyStore",
    "DiscoveryResult",
    "IndustryType",
    "get_database_path",
    "get_discovery_config",
    "is_discovery_enabled",
    "update_discovery_config",
]
