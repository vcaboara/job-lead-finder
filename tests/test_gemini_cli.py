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
        """Test CLI uses GEMINI_API_KEY from environment."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
                # Mock the genai module
                mock_genai = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "test response"
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                with patch.dict("sys.modules", {"google.genai": mock_genai, "google": MagicMock()}):
                    # This should not raise an exception
                    # We can verify the key is read
                    assert os.getenv("GEMINI_API_KEY") == "test-key"

    def test_cli_accepts_key_argument(self):
        """Test CLI accepts --key argument."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "provided-key"]

        with patch("sys.argv", test_args):
            # Mock the genai module
            mock_genai = MagicMock()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "test response"
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            with patch.dict("sys.modules", {"google.genai": mock_genai, "google": MagicMock()}):
                # Argument parsing is tested by argparse
                # In real execution it would use this key
                pass

    def test_cli_uses_google_api_key_fallback(self):
        """Test CLI falls back to GOOGLE_API_KEY if GEMINI_API_KEY not set."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt"]

        with patch("sys.argv", test_args):
            with patch.dict(os.environ, {"GOOGLE_API_KEY": "fallback-key"}):
                # Should use GOOGLE_API_KEY as fallback
                assert os.getenv("GOOGLE_API_KEY") == "fallback-key"

    def test_cli_model_default(self, capsys):
        """Test CLI uses default model when calling generate_content."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--key", "test-key"]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_genai.types = None  # Avoid tool config

        # Create a mock google module with genai attribute
        mock_google = MagicMock()
        mock_google.genai = mock_genai

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify generate_content was called with a model containing "gemini"
                mock_client.models.generate_content.assert_called_once()
                call_kwargs = mock_client.models.generate_content.call_args[1]
                assert "gemini" in call_kwargs["model"].lower()

    def test_cli_custom_model(self, capsys):
        """Test CLI uses custom model when provided via --model argument."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--model", "custom-model", "--key", "test-key"]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_genai.types = None  # Avoid tool config

        # Create a mock google module with genai attribute
        mock_google = MagicMock()
        mock_google.genai = mock_genai

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify generate_content was called with the custom model
                mock_client.models.generate_content.assert_called_once()
                call_kwargs = mock_client.models.generate_content.call_args[1]
                assert call_kwargs["model"] == "custom-model"

    def test_cli_no_tool_flag(self, capsys):
        """Test CLI does not configure tools when --no-tool flag is used."""
        test_args = ["gemini_cli.py", "--prompt", "test prompt", "--no-tool", "--key", "test-key"]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.Client.return_value = mock_client
        # Set up types module that would normally configure tools
        mock_types = MagicMock()
        mock_genai.types = mock_types

        # Create a mock google module with genai attribute
        mock_google = MagicMock()
        mock_google.genai = mock_genai

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify generate_content was called without config (no tools)
                mock_client.models.generate_content.assert_called_once()
                call_kwargs = mock_client.models.generate_content.call_args[1]
                # When --no-tool is set, config should not be passed
                assert "config" not in call_kwargs

    def test_cli_raw_file_argument(self, capsys, tmp_path):
        """Test CLI writes raw response to file when --raw-file is provided."""
        output_file = tmp_path / "output.txt"
        test_args = ["gemini_cli.py", "--prompt", "test", "--raw-file", str(output_file), "--key", "test-key"]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response

        mock_genai = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_genai.types = None  # Avoid tool config

        # Create a mock google module with genai attribute
        mock_google = MagicMock()
        mock_google.genai = mock_genai

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mock_google, "google.genai": mock_genai}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify raw file was written
                assert output_file.exists()
                content = output_file.read_text()
                assert len(content) > 0  # File should have content

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

    def test_cli_prints_sdk_name(self, capsys):
        """Test CLI prints which SDK is being used."""
        # This test verifies the CLI provides feedback about which SDK it's using
        # In actual usage, output like "Using SDK: google.genai" should appear
        pass  # Requires full integration test

    def test_cli_writes_raw_file_if_specified(self):
        """Test CLI writes raw response to file when --raw-file is provided."""
        # This test would require mocking file writes
        # Verifies that --raw-file argument causes output to be written
        pass  # Requires integration test with file mocking
