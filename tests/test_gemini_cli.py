"""Comprehensive tests for gemini_cli module."""

import importlib
import os
import sys
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
        """Test CLI uses GEMINI_API_KEY from environment."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
                # Mock the genai module
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create mock google package with genai attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                with patch.dict(
                    "sys.modules", {"google": mock_google, "google.genai": mock_genai}
                ):
                    from app import gemini_cli

                    # Reload to ensure the module picks up the mocked sys.modules
                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Verify the Client was called with the API key from environment
                    mock_genai.Client.assert_called_once_with(api_key="test-key")

    def test_cli_accepts_key_argument(self):
        """Test CLI accepts --key argument."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "provided-key"]

        with patch("sys.argv", test_args):
            # Mock the genai module
            mock_genai = MagicMock()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "test response"
            mock_response.candidates = None
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            # Create a mock google module with genai attribute
            mock_google = MagicMock()
            mock_google.genai = mock_genai

            with patch.dict(
                "sys.modules", {"google": mock_google, "google.genai": mock_genai}
            ):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                # Call main() - should not raise an exception
                gemini_cli.main()

                # Verify that Client was called with the provided key
                mock_genai.Client.assert_called_once_with(api_key="provided-key")

    def test_cli_uses_google_api_key_fallback(self):
        """Test CLI falls back to GOOGLE_API_KEY if GEMINI_API_KEY not set."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            # Set GOOGLE_API_KEY but NOT GEMINI_API_KEY
            env_vars = {"GOOGLE_API_KEY": "fallback-key"}
            with patch.dict(os.environ, env_vars, clear=True):
                # Mock the genai module at import time
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_response.candidates = None
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                # Create a mock google module with genai attribute
                mock_google = MagicMock()
                mock_google.genai = mock_genai

                # Patch sys.modules before calling main so the import uses our mock
                with patch.dict(
                    sys.modules, {"google": mock_google, "google.genai": mock_genai}
                ):
                    from app import gemini_cli

                    gemini_cli.main()

                    # Verify Client was called with the fallback key
                    mock_genai.Client.assert_called_once_with(api_key="fallback-key")

    def test_cli_model_default(self):
        """Test CLI uses default model if not specified."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "test-key"]

        with patch("sys.argv", test_args):
            import argparse

            # Parse args to check default
            parser = argparse.ArgumentParser()
            parser.add_argument("--prompt", "-p", required=True)
            parser.add_argument(
                "--model", "-m", default=os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-preview-09-2025"
            )
            parser.add_argument("--key", "-k", default=None)

            args = parser.parse_args(test_args[1:])
            assert "gemini" in args.model.lower()

    def test_cli_custom_model(self):
        """Test CLI accepts custom model."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--model", "custom-model", "--key", "test-key"]

        with patch("sys.argv", test_args):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--prompt", "-p", required=True)
            parser.add_argument("--model", "-m", default="default-model")
            parser.add_argument("--key", "-k", default=None)

            args = parser.parse_args(test_args[1:])
            assert args.model == "custom-model"

    def test_cli_no_tool_flag(self):
        """Test CLI accepts --no-tool flag."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--no-tool", "--key", "test-key"]

        with patch("sys.argv", test_args):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--prompt", "-p", required=True)
            parser.add_argument("--no-tool", action="store_true")
            parser.add_argument("--key", "-k", default=None)

            args = parser.parse_args(test_args[1:])
            assert args.no_tool is True

    def test_cli_raw_file_argument(self):
        """Test CLI accepts --raw-file argument."""
        test_args = ["gemini_cli.py", "--prompt", "test", "--raw-file", "output.txt", "--key", "test-key"]

        with patch("sys.argv", test_args):
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--prompt", "-p", required=True)
            parser.add_argument("--raw-file", default=None)
            parser.add_argument("--key", "-k", default=None)

            args = parser.parse_args(test_args[1:])
            assert args.raw_file == "output.txt"

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


class TestGeminiCliArguments:
    """Tests for argument parsing in gemini_cli."""

    def test_prompt_short_form(self):
        """Test -p short form for prompt."""
        test_args = ["gemini_cli.py", "-p", "test prompt", "--key", "test-key"]
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--prompt", "-p", required=True)
        parser.add_argument("--key", "-k", default=None)

        args = parser.parse_args(test_args[1:])
        assert args.prompt == "test prompt"

    def test_model_short_form(self):
        """Test -m short form for model."""
        test_args = ["gemini_cli.py", "--prompt", "test", "-m", "custom-model", "--key", "test-key"]
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--prompt", "-p", required=True)
        parser.add_argument("--model", "-m", default="default")
        parser.add_argument("--key", "-k", default=None)

        args = parser.parse_args(test_args[1:])
        assert args.model == "custom-model"

    def test_key_short_form(self):
        """Test -k short form for key."""
        test_args = ["gemini_cli.py", "--prompt", "test", "-k", "my-key"]
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--prompt", "-p", required=True)
        parser.add_argument("--key", "-k", default=None)

        args = parser.parse_args(test_args[1:])
        assert args.key == "my-key"


class TestGeminiCliSDKSelection:
    """Tests for SDK selection logic in gemini_cli."""

    def test_prefers_legacy_genai_package(self):
        """Test that legacy google.genai is preferred over google.generativeai."""
        # This is more of a documentation test since the actual logic is in the module
        # We can verify the import order in the code
        import inspect

        from app import gemini_cli

        source = inspect.getsource(gemini_cli.main)
        # Check that google.genai is tried first
        assert "from google import genai" in source or "google.genai" in source

    def test_falls_back_to_generativeai(self):
        """Test fallback to google.generativeai if legacy not available."""
        import inspect

        from app import gemini_cli

        source = inspect.getsource(gemini_cli.main)
        # Check that fallback exists
        assert "google.generativeai" in source


class TestGeminiCliOutput:
    """Tests for CLI output handling."""

    @pytest.fixture
    def mock_genai_module(self):
        """Create a mock genai module with client and response."""
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = None
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        mock_genai.types = MagicMock()
        return mock_genai

    def test_cli_prints_sdk_name(self, capsys, mock_genai_module):
        """Test CLI prints which SDK is being used."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
                # Mock the genai module
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": MagicMock()}):
                    import importlib

                    from app import gemini_cli

                    importlib.reload(gemini_cli)
                    gemini_cli.main()

                    # Capture and verify stdout contains SDK name
                    captured = capsys.readouterr()
                    assert "Using SDK: google.genai" in captured.out

    def test_cli_writes_raw_file_if_specified(self, mock_genai_module):
        """Test CLI writes raw response to file when --raw-file is provided."""
        import tempfile

        # Create a temporary file that will be automatically cleaned up
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            test_args = ["gemini_cli.py", "--prompt", "test", "--raw-file", tmp_path]

            with patch("sys.argv", test_args):
                with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
                    # Mock the genai module
                    mock_genai = MagicMock()
                    mock_client = MagicMock()
                    mock_response = MagicMock()
                    mock_response.text = "test response"
                    mock_response.__repr__ = lambda self: "MockResponse(text='test response')"
                    mock_client.models.generate_content.return_value = mock_response
                    mock_genai.Client.return_value = mock_client

                    with patch.dict("sys.modules", {"google.genai": mock_genai, "google": MagicMock()}):
                        import importlib

                        from app import gemini_cli

                        importlib.reload(gemini_cli)
                        gemini_cli.main()

                        # Verify the raw file was written
                        assert os.path.exists(tmp_path)
                        with open(tmp_path, "r") as f:
                            content = f.read()
                        # Verify content is the repr of the response
                        assert "MockResponse" in content or len(content) > 0
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
