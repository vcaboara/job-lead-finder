"""Discovery system configuration."""

import copy
from datetime import time
from pathlib import Path

from app.config_manager import load_config, save_config
from app.discovery.base_provider import IndustryType

_DEFAULTS = {
    "enabled": False,
    "database_path": "data/companies.db",
    "schedule": {"enabled": False, "run_time": "09:00", "interval_hours": 24},
    "filters": {"industries": [], "locations": [], "tech_stack": []},
    "notifications": {"enabled": False, "min_new_companies": 5},
    "providers": {"hackernews": {"enabled": True}},
}


def get_discovery_config() -> dict:
    """Get discovery configuration with defaults.

    Returns a deep copy merged with defaults to prevent mutations
    and ensure all default keys are present.
    """
    config = load_config()
    if "discovery" not in config:
        return copy.deepcopy(_DEFAULTS)
    # Merge with defaults to handle missing keys in saved config
    return {**copy.deepcopy(_DEFAULTS), **copy.deepcopy(config["discovery"])}


def update_discovery_config(**kwargs) -> bool:
    """Update discovery configuration.

    Supported kwargs:
        enabled, database_path, schedule_enabled, run_time,
        interval_hours, industries, locations, tech_stack,
        notifications_enabled, min_new_companies, provider_settings

    Returns:
        True if configuration was successfully saved, False otherwise
    """
    config = load_config()
    discovery = get_discovery_config()

    # Validate and apply updates
    if "run_time" in kwargs:
        try:
            h, m = kwargs["run_time"].split(":")
            time(int(h), int(m))
            discovery["schedule"]["run_time"] = kwargs["run_time"]
        except (ValueError, AttributeError):
            raise ValueError("run_time must be in HH:MM format")

    if "interval_hours" in kwargs:
        if kwargs["interval_hours"] < 1:
            raise ValueError("interval_hours must be at least 1")
        discovery["schedule"]["interval_hours"] = kwargs["interval_hours"]

    if "industries" in kwargs:
        # Validate each industry is a valid enum value (raises ValueError if not)
        for ind in kwargs["industries"]:
            IndustryType(ind)
        discovery["filters"]["industries"] = kwargs["industries"]

    if "min_new_companies" in kwargs:
        if kwargs["min_new_companies"] < 1:
            raise ValueError("min_new_companies must be at least 1")
        discovery["notifications"]["min_new_companies"] = kwargs["min_new_companies"]

    if "provider_settings" in kwargs:
        if not isinstance(kwargs["provider_settings"], dict):
            raise ValueError("provider_settings must be a dictionary")
        discovery["providers"] = kwargs["provider_settings"]

    # Simple assignments
    if "enabled" in kwargs:
        discovery["enabled"] = kwargs["enabled"]
    if "database_path" in kwargs:
        discovery["database_path"] = kwargs["database_path"]
    if "schedule_enabled" in kwargs:
        discovery["schedule"]["enabled"] = kwargs["schedule_enabled"]
    if "locations" in kwargs:
        discovery["filters"]["locations"] = kwargs["locations"]
    if "tech_stack" in kwargs:
        discovery["filters"]["tech_stack"] = kwargs["tech_stack"]
    if "notifications_enabled" in kwargs:
        discovery["notifications"]["enabled"] = kwargs["notifications_enabled"]

    config["discovery"] = discovery
    return save_config(config)


def get_database_path() -> Path:
    """Get configured database path."""
    return Path(get_discovery_config()["database_path"])


def is_discovery_enabled() -> bool:
    """Check if discovery is enabled."""
    return get_discovery_config().get("enabled", False)
