#!/usr/bin/env python3
"""Setup script for Ollama models required by the project.

This script automates downloading and verifying Ollama models for:
1. AI Code Reviews (GitHub Actions)
2. Local Coding Assistant
3. Job Resume Matching

It prevents common mistakes and provides clear feedback.

Usage:
    python scripts/setup_ollama_models.py
    python scripts/setup_ollama_models.py --reviews-only
    python scripts/setup_ollama_models.py --coding-only
"""

import argparse
import logging
import subprocess
import sys
from typing import List, Optional

import httpx

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Model configurations
MODELS = {
    "code-reviews": {
        "name": "deepseek-coder:6.7b",
        "size": "3.8 GB",
        "purpose": "AI code reviews in GitHub Actions",
        "priority": "high",
    },
    "coding-assistant": {
        "name": "codellama:7b",
        "size": "3.8 GB",
        "purpose": "Local code generation and refactoring",
        "priority": "high",
    },
    "job-matching": {
        "name": "llama3.2:3b",
        "size": "2.0 GB",
        "purpose": "Resume and job description matching",
        "priority": "medium",
    },
    "general-llm": {
        "name": "llama3:8b",
        "size": "4.7 GB",
        "purpose": "General purpose tasks",
        "priority": "low",
    },
}


class OllamaSetup:
    """Ollama setup and model management."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama setup.

        Args:
            base_url: Ollama server URL
        """
        self.base_url = base_url
        self.timeout = 600  # 10 minutes for downloads

    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running.

        Returns:
            True if running, False otherwise
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    logger.info("✓ Ollama server is running")
                    return True
                else:
                    logger.error(
                        f"Ollama server failed with status code {response.status_code}: {response.text}")
                    return False
        except httpx.ConnectError:
            logger.error("✗ Cannot connect to Ollama server")
            logger.error(f"  Make sure Ollama is running on {self.base_url}")
            logger.error("  Run: docker compose up -d ollama")
            return False
        except Exception as e:
            logger.error(f"✗ Error checking Ollama: {e}")
            return False

    def list_installed_models(self) -> List[str]:
        """List currently installed models.

        Returns:
            List of model names
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                return [m.get("name") for m in models if m.get("name")]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to list models - HTTP {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {type(e).__name__}: {e}")
            return []

    def is_model_installed(self, model_name: str) -> bool:
        """Check if a model is installed.

        Args:
            model_name: Name of the model

        Returns:
            True if installed, False otherwise
        """
        installed = self.list_installed_models()
        return model_name in installed

    def pull_model(self, model_name: str) -> bool:
        """Pull (download) a model.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                f"Downloading {model_name}... (this may take several minutes)")

            # Use subprocess to show progress
            cmd = ["ollama", "pull", model_name]
            result = subprocess.run(cmd, capture_output=False, text=True)

            if result.returncode == 0:
                logger.info(f"✓ Successfully downloaded {model_name}")
                return True
            else:
                logger.error(
                    f"✗ Failed to download {model_name} (exit code: {result.returncode})")
                if result.stderr:
                    logger.error(f"  Error details: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.error("✗ 'ollama' command not found")
            logger.error(
                "  Install Ollama CLI or use Docker: docker exec job-lead-finder-ollama-1 ollama pull {model_name}"
            )
            return False
        except Exception as e:
            logger.error(f"✗ Error pulling model: {e}")
            return False

    def verify_model(self, model_name: str) -> bool:
        """Verify a model works by generating a test response.

        Args:
            model_name: Name of the model to verify

        Returns:
            True if working, False otherwise
        """
        try:
            logger.info(f"Verifying {model_name}...")

            with httpx.Client(timeout=30.0) as client:
                payload = {
                    "model": model_name,
                    "prompt": "Say 'OK' if you can read this.",
                    "stream": False,
                }
                response = client.post(
                    f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()

                result = response.json()
                if result.get("response"):
                    logger.info(f"✓ {model_name} is working correctly")
                    return True
                else:
                    logger.error(
                        f"✗ {model_name} returned empty response. Full result: {result}")
                    return False

        except httpx.HTTPStatusError as e:
            logger.error(
                f"✗ Error verifying model - HTTP {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"✗ Error verifying model: {type(e).__name__}: {e}")
            return False

    def setup_models(self, model_keys: Optional[List[str]] = None) -> bool:
        """Setup (download and verify) models.

        Args:
            model_keys: List of model keys to setup (default: all high priority)

        Returns:
            True if all successful, False if any failed
        """
        # Check Ollama is running
        if not self.check_ollama_running():
            return False

        # Determine which models to setup
        if model_keys is None:
            # Default: high priority models
            model_keys = [
                k for k, v in MODELS.items() if v["priority"] == "high"]

        # List currently installed
        installed = self.list_installed_models()
        logger.info(
            f"\nCurrently installed models: {installed if installed else 'None'}\n")

        # Setup each model
        success = True
        for key in model_keys:
            if key not in MODELS:
                logger.error(f"Unknown model key: {key}")
                success = False
                continue

            config = MODELS[key]
            model_name = config["name"]

            logger.info(f"\n{'=' * 80}")
            logger.info(f"Model: {model_name}")
            logger.info(f"Size: {config['size']}")
            logger.info(f"Purpose: {config['purpose']}")
            logger.info(f"{'=' * 80}")

            # Check if already installed
            if self.is_model_installed(model_name):
                logger.info(f"✓ {model_name} already installed")
                # Still verify it works
                if not self.verify_model(model_name):
                    success = False
                continue

            # Pull model
            if not self.pull_model(model_name):
                success = False
                continue

            # Verify model
            if not self.verify_model(model_name):
                success = False

        return success

    def print_summary(self):
        """Print summary of installed models and next steps."""
        installed = self.list_installed_models()

        logger.info("\n" + "=" * 80)
        logger.info("SETUP SUMMARY")
        logger.info("=" * 80)

        if installed:
            logger.info(f"\n✓ Installed models ({len(installed)}):")
            for model in installed:
                # Find purpose
                purpose = "Unknown"
                for config in MODELS.values():
                    if config["name"] == model:
                        purpose = config["purpose"]
                        break
                logger.info(f"  - {model:<25} ({purpose})")
        else:
            logger.info("\n✗ No models installed")

        logger.info("\n" + "=" * 80)
        logger.info("NEXT STEPS")
        logger.info("=" * 80)
        logger.info("\n1. Test the coding assistant:")
        logger.info(
            '   python tools/coding_assistant.py generate "Create a function to sum two numbers"')
        logger.info("\n2. Create a test PR to verify AI reviews:")
        logger.info("   git checkout -b test/ai-review")
        logger.info("   # Make a small change")
        logger.info("   git commit -m 'test: Verify AI review workflow'")
        logger.info("   git push origin test/ai-review")
        logger.info("   gh pr create")
        logger.info("\n3. Check Ollama tunnel is running:")
        logger.info("   docker compose logs ollama-tunnel | grep https://")
        logger.info("\n4. Update GitHub secret if tunnel URL changed:")
        logger.info(
            "   gh secret set OLLAMA_BASE_URL --body 'https://your-tunnel-url.trycloudflare.com'")
        logger.info("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Setup Ollama models for the project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available models:
{chr(10).join(f"  {k:<20} {v['name']:<25} {v['size']:<10} {v['purpose']}" for k, v in MODELS.items())}

Examples:
  # Setup all high-priority models (recommended)
  python scripts/setup_ollama_models.py

  # Setup only code review models
  python scripts/setup_ollama_models.py --reviews-only

  # Setup only coding assistant models
  python scripts/setup_ollama_models.py --coding-only

  # Setup specific models
  python scripts/setup_ollama_models.py --models code-reviews coding-assistant
        """,
    )

    parser.add_argument("--reviews-only", action="store_true",
                        help="Setup only code review models")
    parser.add_argument("--coding-only", action="store_true",
                        help="Setup only coding assistant models")
    parser.add_argument("--models", nargs="+",
                        choices=list(MODELS.keys()), help="Specific models to setup")
    parser.add_argument(
        "--base-url", default="http://localhost:11434", help="Ollama server URL")

    args = parser.parse_args()

    setup = OllamaSetup(base_url=args.base_url)

    # Determine which models to setup
    model_keys = None
    if args.reviews_only:
        model_keys = ["code-reviews"]
    elif args.coding_only:
        model_keys = ["coding-assistant"]
    elif args.models:
        model_keys = args.models

    # Run setup
    logger.info("Starting Ollama model setup...\n")
    success = setup.setup_models(model_keys)

    # Print summary
    setup.print_summary()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
