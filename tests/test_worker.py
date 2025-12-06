"""Tests for background worker process."""

import signal
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestSignalHandler:
    """Tests for signal handler."""

    def test_signal_handler_sets_shutdown_flag(self):
        """Test that signal handler sets shutdown flag."""
        # Import locally to avoid module-level logging issues
        import app.worker as worker_module

        worker_module.shutdown_requested = False

        # Simulate SIGTERM
        worker_module.signal_handler(signal.SIGTERM, None)

        assert worker_module.shutdown_requested is True

    def test_signal_handler_with_different_signals(self):
        """Test signal handler with different signal types."""
        import app.worker as worker_module

        for sig in [signal.SIGINT, signal.SIGTERM]:
            worker_module.shutdown_requested = False
            worker_module.signal_handler(sig, None)
            assert worker_module.shutdown_requested is True


class TestWorkerLogging:
    """Tests for worker logging configuration."""

    def test_logs_directory_created(self):
        """Test that logs directory is created."""
        logs_dir = Path("logs")

        # Directory should exist (created by worker module import)
        assert logs_dir.exists()
        assert logs_dir.is_dir()
