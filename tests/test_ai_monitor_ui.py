"""
Tests for AI Resource Monitor Web UI

Covers:
- Data loading and initialization
- Copilot and Gemini usage calculations
- Ollama status checking
- GPU monitoring
- Recommendation generation
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if Flask not available (optional web dependency)
flask = pytest.importorskip("flask", reason="Flask not installed - ai_monitor_ui tests require flask>=3.0.0")

# Import must come after pytest.importorskip to prevent Flask import error
if flask:
    from app.ai_monitor_ui import AIResourceMonitor


@pytest.fixture
def temp_tracking_file(tmp_path):
    """Create a temporary tracking file for tests."""
    return str(tmp_path / ".ai_usage_tracking.json")


@pytest.fixture
def sample_tracking_data():
    """Sample tracking data matching actual implementation structure."""
    today = datetime.now().strftime("%Y-%m-%d")
    current_month = datetime.now().strftime("%Y-%m")
    return {
        "copilot": {
            "daily": [{"date": today} for _ in range(100)],
            "monthly": [{"month": current_month} for _ in range(100)],
        },
        "gemini": {"daily": [{"date": today} for _ in range(5)]},
    }


class TestAIResourceMonitor:
    """Test AIResourceMonitor initialization and data loading."""

    def test_init_creates_default_data(self, temp_tracking_file):
        """Test default data structure when file doesn't exist."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        assert "copilot" in monitor.data
        assert "gemini" in monitor.data
        assert isinstance(monitor.data["copilot"]["daily"], list)
        assert isinstance(monitor.data["copilot"]["monthly"], list)

    def test_init_loads_existing_data(self, temp_tracking_file, sample_tracking_data):
        """Test loading existing tracking data."""
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            json.dump(sample_tracking_data, f)

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        assert monitor.data == sample_tracking_data

    def test_init_handles_corrupted_json(self, temp_tracking_file):
        """Test graceful handling of corrupted JSON."""
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        assert "copilot" in monitor.data
        assert isinstance(monitor.data["copilot"]["daily"], list)

    def test_init_uses_env_variable(self, sample_tracking_data, tmp_path):
        """Test AI_TRACKING_FILE environment variable."""
        tracking_file = tmp_path / "custom.json"
        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(sample_tracking_data, f)

        with patch.dict("os.environ", {"AI_TRACKING_FILE": str(tracking_file)}):
            monitor = AIResourceMonitor()
            assert monitor.tracking_file == Path(tracking_file)


class TestCopilotUsage:
    """Test Copilot usage metric calculations."""

    def test_get_usage_with_data(self, temp_tracking_file, sample_tracking_data):
        """Test usage calculation with existing data."""
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            json.dump(sample_tracking_data, f)

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        usage = monitor.get_copilot_usage()

        assert usage["daily"] == 100
        assert usage["monthly"] == 100
        assert usage["monthly_limit"] == 1500
        assert usage["remaining"] == 1400
        assert usage["percentage_used"] == pytest.approx(6.67, rel=0.01)

    def test_get_usage_with_no_data(self, temp_tracking_file):
        """Test usage calculation with no data."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        usage = monitor.get_copilot_usage()

        assert usage["daily"] == 0
        assert usage["monthly"] == 0
        assert usage["remaining"] == 1500
        assert usage["percentage_used"] == 0.0


class TestGeminiUsage:
    """Test Gemini usage metric calculations."""

    def test_get_usage_with_data(self, temp_tracking_file, sample_tracking_data):
        """Test usage calculation with existing data."""
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            json.dump(sample_tracking_data, f)

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        usage = monitor.get_gemini_usage()

        assert usage["daily"] == 5
        assert usage["daily_limit"] == 20
        assert usage["remaining"] == 15
        assert usage["percentage_used"] == 25.0

    def test_get_usage_with_no_data(self, temp_tracking_file):
        """Test usage calculation with no data."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        usage = monitor.get_gemini_usage()

        assert usage["daily"] == 0
        assert usage["daily_limit"] == 20
        assert usage["remaining"] == 20


class TestOllamaStatus:
    """Test Ollama server status checking."""

    def test_status_running_with_models(self, temp_tracking_file):
        """Test Ollama status with running models."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        mock_output = """NAME                        ID              SIZE    UNTIL
qwen2.5:32b-instruct       abc123          18GB    2 minutes
mistral:7b                 def456          4.1GB   Forever"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            status = monitor.check_ollama_status()

            assert status["status"] == "running"
            assert status["model_count"] == 2
            assert status["models"][0]["name"] == "qwen2.5:32b-instruct"
            assert status["models"][0]["size"] == "18GB"

    def test_status_running_no_models(self, temp_tracking_file):
        """Test Ollama status with no models."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        mock_output = "NAME                        ID              SIZE    UNTIL\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            status = monitor.check_ollama_status()

            assert status["status"] == "running"
            assert status["model_count"] == 0

    def test_status_not_installed(self, temp_tracking_file):
        """Test Ollama not installed."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            status = monitor.check_ollama_status()
            assert status is None

    def test_status_timeout(self, temp_tracking_file):
        """Test Ollama command timeout."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ollama", 5)):
            status = monitor.check_ollama_status()
            assert status is None


class TestGPUUsage:
    """Test GPU monitoring via nvidia-smi."""

    def test_gpu_usage_success(self, temp_tracking_file):
        """Test successful GPU data retrieval."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        mock_output = "NVIDIA GeForce RTX 4090, 45, 12000, 24000"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            gpu = monitor.check_gpu_usage()

            assert gpu["name"] == "NVIDIA GeForce RTX 4090"
            assert gpu["gpu_util"] == 45.0
            assert gpu["mem_used_mb"] == 12000.0
            assert gpu["mem_total_mb"] == 24000.0

    def test_gpu_not_available(self, temp_tracking_file):
        """Test when nvidia-smi not available."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert monitor.check_gpu_usage() is None

    def test_gpu_timeout(self, temp_tracking_file):
        """Test nvidia-smi timeout."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("nvidia-smi", 5)):
            assert monitor.check_gpu_usage() is None

    def test_gpu_invalid_data(self, temp_tracking_file):
        """Test invalid nvidia-smi output."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="invalid,data")
            assert monitor.check_gpu_usage() is None


class TestRecommendations:
    """Test recommendation generation logic."""

    def test_high_copilot_usage(self, temp_tracking_file):
        """Test recommendations for high Copilot usage."""
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")
        data = {
            "copilot": {
                "daily": [{"date": today} for _ in range(50)],
                "monthly": [{"month": current_month} for _ in range(1300)],
            },
            "gemini": {"daily": []},
        }
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch.object(monitor, "check_ollama_status", return_value=None):
            with patch.object(monitor, "check_gpu_usage", return_value=None):
                recommendations = monitor.get_recommendations()

        assert any("Copilot" in rec for rec in recommendations)

    def test_high_gemini_usage(self, temp_tracking_file):
        """Test recommendations for high Gemini usage."""
        today = datetime.now().strftime("%Y-%m-%d")
        data = {
            "copilot": {"daily": [], "monthly": []},
            "gemini": {"daily": [{"date": today} for _ in range(18)]},
        }
        with open(temp_tracking_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch.object(monitor, "check_ollama_status", return_value=None):
            with patch.object(monitor, "check_gpu_usage", return_value=None):
                recommendations = monitor.get_recommendations()

        assert any("Gemini" in rec for rec in recommendations)

    def test_no_issues(self, temp_tracking_file):
        """Test recommendations when usage is low."""
        monitor = AIResourceMonitor(tracking_file=temp_tracking_file)
        with patch.object(
            monitor, "check_ollama_status", return_value={"status": "running", "models": [], "model_count": 0}
        ):
            with patch.object(
                monitor,
                "check_gpu_usage",
                return_value={"name": "GPU", "gpu_util": 30.0, "mem_used_mb": 8000, "mem_total_mb": 24000},
            ):
                recommendations = monitor.get_recommendations()

        warning_recs = [rec for rec in recommendations if "⚠️" in rec]
        assert len(warning_recs) == 0
