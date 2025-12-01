"""Job search configuration management.

Handles persistent configuration for:
- Job search preferences (location, remote/hybrid/onsite)
- MCP provider selection (enable/disable sources)
- Search parameters (count, oversample multiplier)
"""

import json
from pathlib import Path
from typing import Any, Dict, List

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "location": {
        "default_location": "United States",
        "prefer_remote": True,
        "allow_hybrid": True,
        "allow_onsite": False,
    },
    "providers": {
        "remoteok": {"enabled": True, "name": "RemoteOK"},
        "remotive": {"enabled": True, "name": "Remotive"},
        "duckduckgo": {"enabled": True, "name": "DuckDuckGo"},
        "github": {"enabled": False, "name": "GitHub Jobs"},
        "linkedin": {"enabled": False, "name": "LinkedIn"},
        "indeed": {"enabled": False, "name": "Indeed"},
    },
    "search": {
        "default_count": 5,
        "oversample_multiplier": 5,
        "enable_ai_ranking": True,
    },
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file, or return defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Merge with defaults to handle new keys
            return {**DEFAULT_CONFIG, **config}
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_enabled_providers() -> List[str]:
    """Get list of enabled provider names."""
    config = load_config()
    return [info["name"] for key, info in config["providers"].items() if info.get("enabled", False)]


def update_provider_status(provider_key: str, enabled: bool) -> bool:
    """Enable or disable a provider."""
    config = load_config()
    if provider_key in config["providers"]:
        config["providers"][provider_key]["enabled"] = enabled
        return save_config(config)
    return False


def get_location_preferences() -> Dict[str, Any]:
    """Get location and remote/onsite preferences."""
    config = load_config()
    return config["location"]


def update_location_preferences(
    default_location: str = None,
    prefer_remote: bool = None,
    allow_hybrid: bool = None,
    allow_onsite: bool = None,
) -> bool:
    """Update location preferences."""
    config = load_config()
    if default_location is not None:
        config["location"]["default_location"] = default_location
    if prefer_remote is not None:
        config["location"]["prefer_remote"] = prefer_remote
    if allow_hybrid is not None:
        config["location"]["allow_hybrid"] = allow_hybrid
    if allow_onsite is not None:
        config["location"]["allow_onsite"] = allow_onsite
    return save_config(config)


def get_search_preferences() -> Dict[str, Any]:
    """Get search parameter preferences."""
    config = load_config()
    return config["search"]


def update_search_preferences(
    default_count: int = None,
    oversample_multiplier: int = None,
    enable_ai_ranking: bool = None,
) -> bool:
    """Update search preferences."""
    config = load_config()
    if default_count is not None and default_count > 0:
        config["search"]["default_count"] = default_count
    if oversample_multiplier is not None and oversample_multiplier > 0:
        config["search"]["oversample_multiplier"] = oversample_multiplier
    if enable_ai_ranking is not None:
        config["search"]["enable_ai_ranking"] = enable_ai_ranking
    return save_config(config)
