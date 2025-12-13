#!/usr/bin/env python3
"""
Ollama Code Assistant - Local LLM utility for development tasks
Leverages local Ollama models for privacy-sensitive and batch operations.

Recommended models for 12GB VRAM (RTX 4070 Ti):
- qwen2.5-coder:32b (Q4) - Best overall coding
- deepseek-coder:33b (Q4) - Code generation
- codellama:34b (Q4) - Code review/explanation
"""

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for Ollama model selection"""

    name: str
    best_for: str
    context_length: int
    vram_required_gb: float


RECOMMENDED_MODELS = {
    "qwen2.5-coder:32b": ModelConfig(
        name="qwen2.5-coder:32b",
        best_for="code_review,refactoring,bug_detection",
        context_length=32768,
        vram_required_gb=11.5,
    ),
    "deepseek-coder:33b": ModelConfig(
        name="deepseek-coder:33b",
        best_for="code_generation,completion,boilerplate",
        context_length=16384,
        vram_required_gb=11.8,
    ),
    "codellama:34b": ModelConfig(
        name="codellama:34b", best_for="explanation,documentation,teaching", context_length=16384, vram_required_gb=12.0
    ),
}


class OllamaAssistant:
    """Manages interactions with local Ollama models"""

    def __init__(self, model: str = "qwen2.5-coder:32b"):
        self.model = model
        self._verify_ollama_installed()

    def _verify_ollama_installed(self):
        """Check if Ollama is installed and running"""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                logger.error("Ollama not installed or not running")
                logger.error("Install: https://ollama.ai/download")
                sys.exit(1)

            if self.model not in result.stdout:
                logger.warning(f"Model {self.model} not found. Pulling...")
                self._pull_model()

        except FileNotFoundError:
            logger.error("Ollama CLI not found in PATH")
            sys.exit(1)

    def _pull_model(self):
        """Pull the specified model from Ollama registry"""
        logger.info(f"Pulling {self.model}... This may take several minutes")
        result = subprocess.run(["ollama", "pull", self.model], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to pull model: {result.stderr}")
            sys.exit(1)
        logger.info(f"Successfully pulled {self.model}")

    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Query Ollama model with prompt"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        cmd = ["ollama", "run", self.model, prompt]
        if system_prompt:
            # Prepend system prompt to user message for Ollama CLI
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}"
            cmd = ["ollama", "run", self.model, full_prompt]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
            if result.returncode != 0:
                logger.error(f"Ollama query failed: {result.stderr}")
                return ""
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error("Query timeout (5 min)")
            return ""


class CodeReviewer:
    """Code review automation using local LLM"""

    def __init__(self, assistant: OllamaAssistant):
        self.assistant = assistant

    def review_file(self, file_path: Path) -> Dict[str, Any]:
        """Review a Python file for issues"""
        logger.info(f"Reviewing {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        system_prompt = """You are an expert Python code reviewer. Analyze code for:
1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style violations (PEP 8)
5. Missing error handling
6. Potential edge cases

Provide concise, actionable feedback in JSON format:
{
  "severity": "high|medium|low",
  "issues": [
    {"line": <line_num>, "type": "bug|security|performance|style", "description": "..."}
  ],
  "suggestions": ["..."]
}"""

        prompt = f"Review this Python code:\n\n```python\n{code}\n```"

        response = self.assistant.query(prompt, system_prompt)

        try:
            # Try to parse JSON response
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to plain text
            return {"raw_review": response}

    def batch_review(self, directory: Path, pattern: str = "*.py") -> Dict[str, Any]:
        """Review all Python files in directory"""
        results = {}
        files = list(directory.rglob(pattern))

        logger.info(f"Found {len(files)} files to review")

        for file_path in files:
            if "test_" not in file_path.name and "__pycache__" not in str(file_path):
                results[str(file_path)] = self.review_file(file_path)

        return results


class DocstringGenerator:
    """Generate docstrings for Python functions"""

    def __init__(self, assistant: OllamaAssistant):
        self.assistant = assistant

    def generate_docstrings(self, file_path: Path) -> str:
        """Generate docstrings for all functions in file"""
        logger.info(f"Generating docstrings for {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        system_prompt = """You are a Python documentation expert. Add comprehensive docstrings
to all functions and classes using Google style format:

def function(arg1: str, arg2: int) -> bool:
    \"\"\"Brief description.

    Detailed explanation if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised
    \"\"\"

Return ONLY the complete updated code with docstrings added."""

        prompt = f"Add docstrings to this Python code:\n\n```python\n{code}\n```"

        response = self.assistant.query(prompt, system_prompt)

        # Extract code from markdown if present
        if "```python" in response:
            response = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        return response

    def batch_generate(self, directory: Path, output_suffix: str = "_documented") -> None:
        """Generate docstrings for all Python files"""
        files = list(directory.rglob("*.py"))

        for file_path in files:
            if "test_" not in file_path.name and "__pycache__" not in str(file_path):
                documented_code = self.generate_docstrings(file_path)

                # Save to new file
                output_path = file_path.with_stem(file_path.stem + output_suffix)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(documented_code)

                logger.info(f"Saved documented version: {output_path}")


class TestGenerator:
    """Generate pytest tests for Python modules"""

    def __init__(self, assistant: OllamaAssistant):
        self.assistant = assistant

    def generate_tests(self, file_path: Path) -> str:
        """Generate pytest tests for module"""
        logger.info(f"Generating tests for {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        system_prompt = """You are a Python testing expert. Generate comprehensive pytest tests for the provided code.

Include:
1. Test fixtures for setup/teardown
2. Unit tests for each function/method
3. Edge case testing
4. Error condition testing
5. Mock external dependencies using pytest-mock

Use pytest best practices:
- Descriptive test names (test_function_when_condition_then_outcome)
- Arrange-Act-Assert pattern
- Parametrize for multiple inputs
- Proper fixtures and conftest patterns

Return ONLY the complete test file code."""

        prompt = f"Generate pytest tests for this code:\n\n```python\n{code}\n```"

        response = self.assistant.query(prompt, system_prompt)

        # Extract code from markdown if present
        if "```python" in response:
            response = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        return response

    def generate_for_module(self, module_path: Path, output_dir: Path) -> None:
        """Generate test file for module"""
        test_code = self.generate_tests(module_path)

        # Create test filename
        test_filename = f"test_{module_path.stem}.py"
        test_path = output_dir / test_filename

        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        logger.info(f"Generated test file: {test_path}")


class RefactoringAnalyzer:
    """Analyze code for refactoring opportunities"""

    def __init__(self, assistant: OllamaAssistant):
        self.assistant = assistant

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file for code smells and refactoring opportunities"""
        logger.info(f"Analyzing {file_path} for refactoring")

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        system_prompt = """You are a code refactoring expert. Identify:

1. Code smells:
   - Long methods (>50 lines)
   - Complex conditionals (nested if/elif)
   - Duplicated code
   - Large classes (>300 lines)
   - Too many parameters (>5)

2. Refactoring opportunities:
   - Extract method
   - Extract class
   - Replace conditional with polymorphism
   - Introduce parameter object
   - Simplify boolean expressions

3. Design pattern suggestions

Provide output in JSON format:
{
  "code_smells": [{"type": "...", "location": "...", "description": "..."}],
  "refactoring_suggestions": [{"type": "...", "benefit": "...", "effort": "low|medium|high"}],
  "design_patterns": ["..."]
}"""

        prompt = f"Analyze this code for refactoring:\n\n```python\n{code}\n```"

        response = self.assistant.query(prompt, system_prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_analysis": response}


@dataclass
class ModelUpdateStatus:
    """Status of a model's update state"""

    status_icon: str
    recommendation: str
    category: str  # 'up_to_date', 'needs_check', 'updates_available'


def _parse_model_age(modified: str) -> ModelUpdateStatus:
    """
    Parse model modification time and determine update status.

    Args:
        modified: Time string like "3 weeks ago" or "2 months ago"

    Returns:
        ModelUpdateStatus with status icon, recommendation, and category
    """
    import re

    # Define age thresholds and their corresponding statuses
    # Format: (keywords, pattern, [(threshold_value, status_icon, recommendation, category)])
    age_rules = [
        (
            ["second", "minute", "hour"],
            None,
            [(float("inf"), "✅ Just updated", "Up to date", "up_to_date")],
        ),
        (
            ["day"],
            r"(\d+)\s+day",
            [
                (7, "✅ Recent", "Up to date", "up_to_date"),
                (30, "⚠️ Moderate", "Consider checking", "needs_check"),
                (float("inf"), "⚠️ Old", "Check for updates", "needs_check"),
            ],
        ),
        (
            ["week"],
            r"(\d+)\s+week",
            [
                (2, "✅ Recent", "Up to date", "up_to_date"),
                (8, "⚠️ Moderate", "Check for updates", "needs_check"),
                (float("inf"), "🔴 Old", "Update recommended", "updates_available"),
            ],
        ),
        (
            ["month"],
            r"(\d+)\s+month",
            [
                (2, "⚠️ Moderate", "Check for updates", "needs_check"),
                (float("inf"), "🔴 Old", "Update recommended", "updates_available"),
            ],
        ),
        (
            ["year"],
            None,
            [(float("inf"), "🔴 Very old", "Update strongly recommended", "updates_available")],
        ),
    ]

    # Check each age rule
    for keywords, pattern, thresholds in age_rules:
        if not any(keyword in modified for keyword in keywords):
            continue

        # Extract numeric value if pattern exists
        value = 1
        if pattern:
            match = re.search(pattern, modified)
            if match:
                value = int(match.group(1))
            else:
                continue  # Pattern expected but not found

        # Find matching threshold
        for threshold, icon, rec, cat in thresholds:
            if value < threshold:
                return ModelUpdateStatus(icon, rec, cat)

    # Default if no rule matched
    return ModelUpdateStatus("❓ Unknown", "Check manually", "needs_check")


def check_model_updates():
    """Check installed models for available updates"""
    logger.info("Checking for model updates...")

    # Get list of installed models
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error("Failed to get model list")
        return

    lines = result.stdout.strip().split("\n")
    if len(lines) < 2:
        logger.info("No models installed")
        return

    # User-facing output goes to stdout
    print("\n" + "=" * 80)
    print("Ollama Model Update Check")
    print("=" * 80 + "\n")

    # Parse model list (skip header)
    models = lines[1:]

    # Categorize models by status
    updates_available = []
    up_to_date = []
    needs_check = []

    for line in models:
        parts = line.split()
        if len(parts) < 4:
            continue

        name = parts[0]
        # Modified time is typically last 2-3 parts (e.g., "3 weeks ago" or "2 months ago")
        modified = " ".join(parts[-3:]) if len(parts) > 5 else " ".join(parts[-2:])

        # Determine status using extracted function
        status = _parse_model_age(modified)

        # Print status line to stdout for user
        print(f"{status.status_icon:15} {name:35} {modified:20} → {status.recommendation}")

        # Categorize model
        if status.category == "up_to_date":
            up_to_date.append(name)
        elif status.category == "needs_check":
            needs_check.append(name)
        elif status.category == "updates_available":
            updates_available.append(name)

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ Up to date: {len(up_to_date)}")
    print(f"⚠️ Consider checking: {len(needs_check)}")
    print(f"🔴 Updates recommended: {len(updates_available)}")

    # Update commands
    if updates_available:
        print("\n" + "=" * 80)
        print("To update models:")
        print("=" * 80)
        for model in updates_available:
            print(f"ollama pull {model}")

    if needs_check:
        print("\n" + "=" * 80)
        print("To check for updates:")
        print("=" * 80)
        for model in needs_check:
            print(f"ollama pull {model}  # Will only download if newer version exists")

    print("\n" + "=" * 80)
    print("Note: 'ollama pull' only downloads if a newer version is available.")
    print("Ollama models don't have explicit version numbers, so age is the indicator.")
    print("Check https://ollama.ai/library for model release notes.")
    print("=" * 80 + "\n")


def recommend_model(task: str, available_vram_gb: float = 12.0) -> str:
    """Recommend best model for task and hardware"""
    task_lower = task.lower()

    # Filter models by VRAM
    suitable_models = {
        name: config for name, config in RECOMMENDED_MODELS.items() if config.vram_required_gb <= available_vram_gb
    }

    if not suitable_models:
        logger.warning("No models fit in %sGB VRAM", available_vram_gb)
        return "qwen2.5-coder:7b"  # Fallback to smaller model

    # Match task to best model
    for name, config in suitable_models.items():
        if any(keyword in task_lower for keyword in config.best_for.split(",")):
            logger.info("Recommended model for '%s': %s", task, name)
            return name

    # Default to qwen2.5-coder
    return "qwen2.5-coder:32b"


def main():
    parser = argparse.ArgumentParser(
        description="Ollama Code Assistant - Local LLM development tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review a single file
  python ollama_code_assistant.py review src/app/job_finder.py

  # Review all files in directory
  python ollama_code_assistant.py review src/app/ --batch

  # Generate docstrings for file
  python ollama_code_assistant.py docstring src/app/job_tracker.py

  # Generate tests for module
  python ollama_code_assistant.py test src/app/email_processor.py -o tests/

  # Analyze for refactoring
  python ollama_code_assistant.py refactor src/app/ui_server.py

  # Recommend model for task
  python ollama_code_assistant.py recommend "code review" --vram 12
        """,
    )

    parser.add_argument(
        "command",
        choices=["review", "docstring", "test", "refactor", "recommend", "check-updates"],
        help="Command to execute",
    )
    parser.add_argument("target", nargs="?", help="File or directory to process (not needed for check-updates)")
    parser.add_argument(
        "-m", "--model", default="qwen2.5-coder:32b", help="Ollama model to use (default: qwen2.5-coder:32b)"
    )
    parser.add_argument("-o", "--output", help="Output directory for generated files")
    parser.add_argument("--batch", action="store_true", help="Process all files in directory")
    parser.add_argument("--vram", type=float, default=12.0, help="Available VRAM in GB (default: 12)")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")

    args = parser.parse_args()

    # Handle check-updates command
    if args.command == "check-updates":
        check_model_updates()
        return

    # Handle recommend command separately
    if args.command == "recommend":
        model = recommend_model(args.target, args.vram)
        print(f"Recommended model: {model}")
        print(f"Best for: {RECOMMENDED_MODELS[model].best_for}")
        print(f"VRAM required: {RECOMMENDED_MODELS[model].vram_required_gb}GB")
        return

    # Initialize assistant
    assistant = OllamaAssistant(args.model)

    target_path = Path(args.target)

    if args.command == "review":
        reviewer = CodeReviewer(assistant)

        if args.batch and target_path.is_dir():
            results = reviewer.batch_review(target_path)
            output = json.dumps(results, indent=2) if args.format == "json" else str(results)
        else:
            results = reviewer.review_file(target_path)
            output = json.dumps(results, indent=2) if args.format == "json" else str(results)

        print(output)

    elif args.command == "docstring":
        generator = DocstringGenerator(assistant)

        if args.batch and target_path.is_dir():
            generator.batch_generate(target_path)
        else:
            documented = generator.generate_docstrings(target_path)
            print(documented)

    elif args.command == "test":
        generator = TestGenerator(assistant)
        output_dir = Path(args.output) if args.output else Path("tests")
        output_dir.mkdir(exist_ok=True)

        generator.generate_for_module(target_path, output_dir)

    elif args.command == "refactor":
        analyzer = RefactoringAnalyzer(assistant)
        results = analyzer.analyze_file(target_path)

        output = json.dumps(results, indent=2) if args.format == "json" else str(results)
        print(output)


if __name__ == "__main__":
    main()
