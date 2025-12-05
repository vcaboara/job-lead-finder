"""Tests for discovery configuration."""

import json
import tempfile
from pathlib import Path

import pytest

from app.discovery import (
    get_database_path,
    get_discovery_config,
    is_discovery_enabled,
    update_discovery_config,
)
from app.discovery.base_provider import IndustryType


@pytest.fixture
def temp_config(monkeypatch):
    """Use temporary config file for tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = Path(f.name)
        json.dump({}, f)
    
    monkeypatch.setattr('app.config_manager.CONFIG_FILE', config_path)
    monkeypatch.setattr('app.discovery.config.load_config', 
                        lambda: json.loads(config_path.read_text()) if config_path.exists() else {})
    
    yield config_path
    config_path.unlink()


def test_get_default_config(temp_config):
    """Test default discovery configuration."""
    config = get_discovery_config()
    
    assert config["enabled"] is False
    assert config["database_path"] == "data/companies.db"
    assert config["schedule"]["enabled"] is False
    assert config["schedule"]["run_time"] == "09:00"
    assert config["schedule"]["interval_hours"] == 24


def test_is_discovery_enabled_default(temp_config):
    """Test discovery disabled by default."""
    assert is_discovery_enabled() is False


def test_get_database_path_default(temp_config):
    """Test default database path."""
    path = get_database_path()
    assert path == Path("data/companies.db")


def test_update_discovery_enabled(temp_config):
    """Test enabling discovery."""
    success = update_discovery_config(enabled=True)
    assert success is True
    assert is_discovery_enabled() is True


def test_update_database_path(temp_config):
    """Test updating database path."""
    update_discovery_config(database_path="custom/path.db")
    path = get_database_path()
    assert path == Path("custom/path.db")


def test_update_schedule(temp_config):
    """Test updating schedule settings."""
    update_discovery_config(
        schedule_enabled=True,
        run_time="14:30",
        interval_hours=12
    )
    
    config = get_discovery_config()
    assert config["schedule"]["enabled"] is True
    assert config["schedule"]["run_time"] == "14:30"
    assert config["schedule"]["interval_hours"] == 12


def test_update_filters(temp_config):
    """Test updating filter settings."""
    update_discovery_config(
        industries=[IndustryType.TECH.value, IndustryType.HEALTHCARE.value],
        locations=["San Francisco", "Remote"],
        tech_stack=["Python", "React"]
    )
    
    config = get_discovery_config()
    assert len(config["filters"]["industries"]) == 2
    assert "San Francisco" in config["filters"]["locations"]
    assert "Python" in config["filters"]["tech_stack"]


def test_invalid_run_time(temp_config):
    """Test invalid time format raises error."""
    with pytest.raises(ValueError, match="HH:MM format"):
        update_discovery_config(run_time="25:00")
    
    with pytest.raises(ValueError, match="HH:MM format"):
        update_discovery_config(run_time="invalid")


def test_invalid_interval(temp_config):
    """Test invalid interval raises error."""
    with pytest.raises(ValueError, match="at least 1"):
        update_discovery_config(interval_hours=0)


def test_invalid_industry(temp_config):
    """Test invalid industry raises error."""
    with pytest.raises(ValueError):
        update_discovery_config(industries=["INVALID_INDUSTRY"])


def test_partial_update(temp_config):
    """Test partial config updates preserve other values."""
    update_discovery_config(enabled=True, database_path="test.db")
    
    update_discovery_config(schedule_enabled=True)
    config2 = get_discovery_config()
    
    assert config2["enabled"] is True
    assert config2["database_path"] == "test.db"
    assert config2["schedule"]["enabled"] is True
