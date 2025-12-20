"""Configuration management utilities."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def load_config(config_path: str | Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Args:
        config_path: Path to configuration file
        default: Default configuration to return if file doesn't exist
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.debug(f"Config file {config_path} not found, using defaults")
        return default or {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.debug(f"Loaded config from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return default or {}


def save_config(config: Dict[str, Any], config_path: str | Path) -> bool:
    """Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save configuration to
        
    Returns:
        True if successful, False otherwise
    """
    config_path = Path(config_path)
    
    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.debug(f"Saved config to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config to {config_path}: {e}")
        return False


def get_env_config(prefix: str = "ASMF_") -> Dict[str, str]:
    """Get configuration from environment variables.
    
    Args:
        prefix: Prefix for environment variables (default: ASMF_)
        
    Returns:
        Dictionary of environment variables with prefix removed from keys
    """
    import os
    
    config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    
    return config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries.
    
    Later configs override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    result = {}
    for config in configs:
        result.update(config)
    return result
