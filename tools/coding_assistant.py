#!/usr/bin/env python3
"""Coding Assistant using local Ollama models.

This tool leverages local LLM models (DeepSeek Coder, CodeLlama) for code generation,
refactoring, bug fixing, and test writing - all running locally with no API costs.

Usage:
    # Generate code
    python tools/coding_assistant.py generate "Create a Python function to parse CSV files"

    # Refactor code
    python tools/coding_assistant.py refactor path/to/file.py

    # Fix bugs
    python tools/coding_assistant.py fix "AttributeError: 'NoneType' object has no attribute 'value'" path/to/file.py

    # Write tests
    python tools/coding_assistant.py test path/to/file.py

    # Review code
    python tools/coding_assistant.py review path/to/file.py

Requirements:
    - Ollama running locally (http://localhost:11434)
    - Models: deepseek-coder:6.7b (recommended) or codellama:7b
    - Run setup: python scripts/setup_ollama_models.py
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import httpx

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CodingAssistant:
    """Local coding assistant using Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "deepseek-coder:6.7b"):
        """Initialize coding assistant.

        Args:
            base_url: Ollama server URL
            model: Model to use (deepseek-coder:6.7b or codellama:7b)
        """
        self.base_url = base_url
        self.model = model
        self.timeout = 300  # 5 minutes for complex code generation

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                # Check server
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    logger.error(
                        f"Ollama server returned HTTP {response.status_code}: {response.text}")
                    logger.error(
                        "Is Ollama running? Check: docker compose ps ollama")
                    return False

                # Check model
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                if self.model not in model_names:
                    logger.error(
                        f"Model '{self.model}' not installed. Available models: {model_names or 'none'}")
                    logger.error("Run: python scripts/setup_ollama_models.py")
                    return False

                return True
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            logger.error(
                "Make sure Ollama is running: docker compose up -d ollama")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama: {type(e).__name__}: {e}")
            return False

    def _generate(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate response from Ollama.

        Args:
            prompt: User prompt
            system_prompt: System instructions

        Returns:
            Generated text or None on error
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # More deterministic for code
                        "top_p": 0.9,
                        "num_predict": 2048,  # Max tokens
                    },
                }

                logger.info(f"Generating with {self.model}...")
                response = client.post(
                    f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()

                result = response.json()
                generated = result.get("response", "").strip()
                if not generated:
                    logger.error(
                        f"Empty response from Ollama. Full result: {result}")
                return generated

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Generation failed - HTTP {e.response.status_code}: {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Generation timed out after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Generation failed: {type(e).__name__}: {e}")
            return None

    def generate_code(self, description: str) -> Optional[str]:
        """Generate code from natural language description.

        Args:
            description: What the code should do

        Returns:
            Generated code or None
        """
        system_prompt = """You are an expert Python developer. Generate clean, production-ready code.
- Follow PEP 8 style guidelines
- Include type hints
- Add docstrings for functions/classes
- Handle errors appropriately
- Keep functions focused and modular
- Only output the code, no explanations"""

        prompt = f"Write Python code for: {description}"

        return self._generate(prompt, system_prompt)

    def refactor_code(self, file_path: str) -> Optional[str]:
        """Refactor code for better quality.

        Args:
            file_path: Path to code file

        Returns:
            Refactored code or None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        code = path.read_text(encoding="utf-8")

        system_prompt = """You are an expert Python code reviewer. Refactor the code to improve:
- Code clarity and readability
- Performance and efficiency
- Error handling
- Modularity and reusability
- Follow Python best practices
- Only output the refactored code, no explanations"""

        prompt = f"Refactor this code:\n\n```python\n{code}\n```"

        return self._generate(prompt, system_prompt)

    def fix_bug(self, error_message: str, file_path: Optional[str] = None) -> Optional[str]:
        """Fix a bug based on error message and optionally the code.

        Args:
            error_message: Error or bug description
            file_path: Optional path to buggy code

        Returns:
            Fixed code or fix suggestion
        """
        code = ""
        if file_path:
            path = Path(file_path)
            if path.exists():
                code = path.read_text(encoding="utf-8")
            else:
                logger.warning(
                    f"File not found: {file_path}, fixing based on error only")

        system_prompt = """You are an expert Python debugger. Analyze the error and provide:
1. Root cause explanation
2. Fixed code
3. Prevention tips
Be concise and focus on the solution."""

        if code:
            prompt = f"Fix this error:\n\nError: {error_message}\n\nCode:\n```python\n{code}\n```"
        else:
            prompt = f"How to fix this error: {error_message}"

        return self._generate(prompt, system_prompt)

    def write_tests(self, file_path: str) -> Optional[str]:
        """Generate pytest tests for code.

        Args:
            file_path: Path to code file

        Returns:
            Test code or None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        code = path.read_text(encoding="utf-8")

        system_prompt = """You are an expert test engineer. Write comprehensive pytest tests:
- Test happy paths and edge cases
- Test error handling
- Use fixtures appropriately
- Include parametrize for multiple inputs
- Mock external dependencies
- Only output the test code, no explanations"""

        prompt = f"Write pytest tests for:\n\n```python\n{code}\n```"

        return self._generate(prompt, system_prompt)

    def review_code(self, file_path: str) -> Optional[str]:
        """Review code and provide suggestions.

        Args:
            file_path: Path to code file

        Returns:
            Review feedback or None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        code = path.read_text(encoding="utf-8")

        system_prompt = """You are an expert code reviewer. Review the code for:
- Bugs and potential issues
- Performance problems
- Security vulnerabilities
- Code style and best practices
- Missing error handling
Provide specific, actionable feedback."""

        prompt = f"Review this code:\n\n```python\n{code}\n```"

        return self._generate(prompt, system_prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Coding Assistant using local Ollama models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate code
  python tools/coding_assistant.py generate "Parse CSV and return list of dicts"

  # Refactor code
  python tools/coding_assistant.py refactor src/app/job_finder.py

  # Fix bug
  python tools/coding_assistant.py fix "KeyError: 'email'" src/app/config.py

  # Write tests
  python tools/coding_assistant.py test src/app/utils.py

  # Review code
  python tools/coding_assistant.py review src/app/main.py
        """,
    )

    parser.add_argument("command", choices=[
                        "generate", "refactor", "fix", "test", "review"], help="Command to run")
    parser.add_argument(
        "input", help="Description for generate, error for fix, or file path for others")
    parser.add_argument("file", nargs="?",
                        help="Optional file path (for fix command)")
    parser.add_argument("--model", default="deepseek-coder:6.7b",
                        help="Model to use (default: deepseek-coder:6.7b)")
    parser.add_argument(
        "--output", "-o", help="Output file path (default: print to stdout)")

    args = parser.parse_args()

    assistant = CodingAssistant(model=args.model)

    # Check Ollama availability
    if not assistant._check_ollama():
        sys.exit(1)

    # Execute command
    result = None
    if args.command == "generate":
        result = assistant.generate_code(args.input)
    elif args.command == "refactor":
        result = assistant.refactor_code(args.input)
    elif args.command == "fix":
        result = assistant.fix_bug(args.input, args.file)
    elif args.command == "test":
        result = assistant.write_tests(args.input)
    elif args.command == "review":
        result = assistant.review_code(args.input)

    if result is None:
        logger.error("Failed to generate response")
        sys.exit(1)

    # Output result
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        logger.info(f"Result saved to {args.output}")
    else:
        print("\n" + "=" * 80)
        print(result)
        print("=" * 80)


if __name__ == "__main__":
    main()
