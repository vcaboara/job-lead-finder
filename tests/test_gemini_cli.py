"""Comprehensive tests for gemini_cli module."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestGeminiCliMain:
    """Tests for gemini_cli main function."""

    @pytest.fixture
    def mock_genai_legacy(self):
        """Mock the legacy google.genai package."""
        with patch.dict("sys.modules", {"google.genai": MagicMock()}):
            yield

    def test_cli_requires_prompt(self):
        """Test CLI fails without --prompt argument."""
        with patch("sys.argv", ["gemini_cli.py"]):
            with pytest.raises(SystemExit):
                from app import gemini_cli

                gemini_cli.main()

    def test_cli_requires_api_key(self):
        """Test CLI fails without API key."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(SystemExit) as exc:
                    from app import gemini_cli

                    gemini_cli.main()
                assert exc.value.code == 2

    def test_cli_uses_key_from_env(self):
        """Test CLI uses GEMINI_API_KEY from environment and passes to client."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "env-api-key"}, clear=True):
                # Mock the genai module to capture the API key
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify Client was initialized with the API key from environment
                    mock_genai.Client.assert_called_once_with(api_key="env-api-key")

    def test_cli_accepts_key_argument(self):
        """Test CLI accepts --key argument and passes it to client."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "provided-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                # Mock the genai module to capture the API key
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify Client was initialized with the provided key
                    mock_genai.Client.assert_called_once_with(api_key="provided-key")

    def test_cli_uses_google_api_key_fallback(self):
        """Test CLI falls back to GOOGLE_API_KEY if GEMINI_API_KEY not set."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            # Only set GOOGLE_API_KEY, not GEMINI_API_KEY
            with patch.dict(os.environ, {"GOOGLE_API_KEY": "fallback-key"}, clear=True):
                # Mock the genai module to capture the API key
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify Client was initialized with the fallback GOOGLE_API_KEY
                    mock_genai.Client.assert_called_once_with(api_key="fallback-key")

    def test_cli_model_default(self):
        """Test CLI uses default model when not specified."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify generate_content was called with the default model
                    call_args = mock_client.models.generate_content.call_args
                    assert "gemini" in call_args.kwargs["model"].lower()

    def test_cli_custom_model(self):
        """Test CLI accepts custom model and passes it to API."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--model", "custom-model", "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify generate_content was called with the custom model
                    call_args = mock_client.models.generate_content.call_args
                    assert call_args.kwargs["model"] == "custom-model"

    def test_cli_no_tool_flag(self):
        """Test CLI accepts --no-tool flag and doesn't configure tools."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--no-tool", "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify generate_content was called without config (no tools)
                    call_args = mock_client.models.generate_content.call_args
                    assert "config" not in call_args.kwargs or call_args.kwargs.get("config") is None

    def test_cli_raw_file_argument(self):
        """Test CLI writes raw response to file when --raw-file is provided."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
            raw_file_path = tf.name

        test_args = ["gemini_cli.py", "--prompt", "test", "--raw-file", raw_file_path, "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

        # Verify file was written
        try:
            with open(raw_file_path) as f:
                content = f.read()
            assert len(content) > 0  # File should have content
        finally:
            os.unlink(raw_file_path)  # Cleanup

    def test_cli_exits_if_no_sdk_installed(self):
        """Test CLI exits gracefully if no SDK is installed."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "test-key"]

        with patch("sys.argv", test_args):
            # Mock both SDK imports to fail
            with patch.dict("sys.modules", {"google.genai": None, "google.generativeai": None}):
                with pytest.raises(SystemExit):
                    # Force reimport to trigger SDK check
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()


class TestGeminiCliSDKSelection:
    """Tests for SDK selection logic in gemini_cli."""

    def test_prefers_legacy_genai_package_at_runtime(self, capsys):
        """Test that legacy google.genai is preferred over google.generativeai at runtime."""
        test_args = ["gemini_cli.py", "--prompt", "test", "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                # Create mocks for both SDKs
                mock_legacy_genai = MagicMock()
                mock_legacy_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_legacy_client.models.generate_content.return_value = mock_response
                mock_legacy_genai.Client.return_value = mock_legacy_client

                mock_new_genai = MagicMock()

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_legacy_genai

                # Both SDKs available, but legacy should be used
                with patch.dict(
                    "sys.modules",
                    {"google.genai": mock_legacy_genai, "google.generativeai": mock_new_genai, "google": mock_google},
                ):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify legacy SDK was used (Client was called)
                    mock_legacy_genai.Client.assert_called_once()
                    # Verify output shows legacy SDK
                    captured = capsys.readouterr()
                    assert "google.genai" in captured.out


class TestGeminiCliOutput:
    """Tests for CLI output handling."""

    def test_cli_prints_sdk_name(self, capsys):
        """Test CLI prints which SDK is being used."""
        test_args = ["gemini_cli.py", "--prompt", "test", "--key", "test-key"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {}, clear=True):
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module that has genai as an attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": mock_google}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    captured = capsys.readouterr()
                    assert "Using SDK:" in captured.out
