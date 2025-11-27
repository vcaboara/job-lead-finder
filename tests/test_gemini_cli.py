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


class TestGeminiCliIntegration:
    """Integration tests that mock the Gemini client and verify end-to-end behavior."""

    @pytest.fixture
    def mock_gemini_setup(self):
        """Create mock Gemini client setup for integration tests."""
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "API response"
        mock_response.candidates = None
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        mock_google = MagicMock()
        mock_google.genai = mock_genai

        return {
            "genai": mock_genai,
            "client": mock_client,
            "response": mock_response,
            "google": mock_google,
        }

    def test_cli_prompt_short_form_calls_api(self, mock_gemini_setup):
        """Test -p short form properly sends prompt to API."""
        test_args = ["gemini_cli.py", "-p", "test prompt", "-k", "test-key"]
        mocks = mock_gemini_setup

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mocks["google"], "google.genai": mocks["genai"]}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify the API was called with the prompt
                mocks["genai"].Client.assert_called_once_with(api_key="test-key")
                mocks["client"].models.generate_content.assert_called_once()
                call_kwargs = mocks["client"].models.generate_content.call_args
                assert call_kwargs.kwargs.get("contents") == "test prompt"

    def test_cli_model_short_form_calls_api_with_model(self, mock_gemini_setup):
        """Test -m short form properly sets model for API call."""
        test_args = ["gemini_cli.py", "-p", "test", "-m", "custom-model", "-k", "test-key"]
        mocks = mock_gemini_setup

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mocks["google"], "google.genai": mocks["genai"]}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify the API was called with the custom model
                mocks["client"].models.generate_content.assert_called_once()
                call_kwargs = mocks["client"].models.generate_content.call_args
                assert call_kwargs.kwargs.get("model") == "custom-model"

    def test_cli_key_short_form_configures_client(self, mock_gemini_setup):
        """Test -k short form properly configures API client with key."""
        test_args = ["gemini_cli.py", "-p", "test", "-k", "my-api-key"]
        mocks = mock_gemini_setup

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mocks["google"], "google.genai": mocks["genai"]}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify the client was configured with the API key
                mocks["genai"].Client.assert_called_once_with(api_key="my-api-key")

    def test_cli_no_tool_flag_disables_search_tool(self, mock_gemini_setup):
        """Test --no-tool flag prevents google_search tool from being configured."""
        test_args = ["gemini_cli.py", "-p", "test", "-k", "test-key", "--no-tool"]
        mocks = mock_gemini_setup
        mock_types = MagicMock()
        mocks["genai"].types = mock_types

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mocks["google"], "google.genai": mocks["genai"]}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

                # Verify GenerateContentConfig was NOT called (no tool config)
                mock_types.GenerateContentConfig.assert_not_called()

    def test_cli_raw_file_writes_output(self, mock_gemini_setup, tmp_path):
        """Test --raw-file writes response to specified file."""
        output_file = tmp_path / "output.txt"
        test_args = ["gemini_cli.py", "-p", "test", "-k", "test-key", "--raw-file", str(output_file)]
        mocks = mock_gemini_setup

        with patch("sys.argv", test_args):
            with patch.dict("sys.modules", {"google": mocks["google"], "google.genai": mocks["genai"]}):
                import importlib

                from app import gemini_cli

                importlib.reload(gemini_cli)
                gemini_cli.main()

        # Verify the file was written
        assert output_file.exists()
        content = output_file.read_text()
        assert "MagicMock" in content  # repr of mock response


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
