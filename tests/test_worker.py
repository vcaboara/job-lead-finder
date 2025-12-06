"""Tests for background worker process."""

import asyncio
import signal
from unittest.mock import MagicMock, patch

import pytest


class TestWorkerMain:
    """Tests for worker main function."""

    @pytest.mark.asyncio
    async def test_main_starts_scheduler(self):
        """Test that main function starts the scheduler."""
        with patch("app.worker.get_scheduler") as mock_get_scheduler, patch("app.worker.shutdown_requested", False):
            mock_scheduler = MagicMock()
            mock_get_scheduler.return_value = mock_scheduler

            # Create a task that will run main and cancel it after a short time
            async def run_main_briefly():
                import app.worker

                app.worker.shutdown_requested = False
                task = asyncio.create_task(app.worker.main())
                await asyncio.sleep(0.1)
                app.worker.shutdown_requested = True
                await asyncio.sleep(0.1)
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            await run_main_briefly()

            # Verify scheduler was started
            mock_get_scheduler.assert_called_once()
            mock_scheduler.start.assert_called_once_with(find_links_interval_minutes=60, cleanup_interval_hours=24)

    @pytest.mark.asyncio
    async def test_main_graceful_shutdown(self):
        """Test that main function handles graceful shutdown."""
        with patch("app.worker.get_scheduler") as mock_get_scheduler:
            mock_scheduler = MagicMock()
            mock_get_scheduler.return_value = mock_scheduler

            # Simulate immediate shutdown
            import app.worker

            app.worker.shutdown_requested = False

            async def trigger_shutdown():
                await asyncio.sleep(0.05)
                app.worker.shutdown_requested = True

            # Run main and trigger shutdown
            await asyncio.gather(app.worker.main(), trigger_shutdown())

            # Verify scheduler was stopped
            mock_scheduler.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_handles_keyboard_interrupt(self):
        """Test that main function handles KeyboardInterrupt."""
        with patch("app.worker.get_scheduler") as mock_get_scheduler, patch("app.worker.asyncio.sleep") as mock_sleep:
            mock_scheduler = MagicMock()
            mock_get_scheduler.return_value = mock_scheduler

            # Make sleep raise KeyboardInterrupt
            mock_sleep.side_effect = KeyboardInterrupt()

            import app.worker

            app.worker.shutdown_requested = False

            # Should handle KeyboardInterrupt gracefully
            await app.worker.main()

            # Verify scheduler was stopped
            mock_scheduler.stop.assert_called_once()


class TestSignalHandler:
    """Tests for signal handler."""

    def test_signal_handler_sets_shutdown_flag(self):
        """Test that signal handler sets shutdown flag."""
        import app.worker

        app.worker.shutdown_requested = False

        # Simulate SIGTERM
        app.worker.signal_handler(signal.SIGTERM, None)

        assert app.worker.shutdown_requested is True

    def test_signal_handler_with_different_signals(self):
        """Test signal handler with different signal types."""
        import app.worker

        for sig in [signal.SIGINT, signal.SIGTERM]:
            app.worker.shutdown_requested = False
            app.worker.signal_handler(sig, None)
            assert app.worker.shutdown_requested is True


class TestWorkerLogging:
    """Tests for worker logging configuration."""

    def test_logs_directory_created(self):
        """Test that logs directory is created."""
        from pathlib import Path

        logs_dir = Path("logs")

        # Directory should exist (created by worker module import)
        assert logs_dir.exists()
        assert logs_dir.is_dir()
