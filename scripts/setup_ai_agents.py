#!/usr/bin/env python3
"""
AI Agent Setup Utility
Automates setup for parallel AI development with multiple LLM providers.
Works cross-platform: Windows, Linux, Mac
"""

import argparse
import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a styled header for CLI output.

    Args:
        text: Header text to display.    Note: Uses print() for formatted console output in interactive setup.
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print success message with styled output.

    Args:
        text: Success message to display.
    """
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message with styled output.

    Args:
        text: Info message to display.
    """
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message with styled output.

    Args:
        text: Warning message to display.
    """
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    logger.warning(text)


def print_error(text: str) -> None:
    """Print error message with styled output.

    Args:
        text: Error message to display.
    """
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    logger.error(text)


def run_command(
    cmd: List[str], check: bool = True, capture_output: bool = False, timeout: Optional[int] = None
) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr.

    Args:
        cmd: Command and arguments as a list.
        check: Whether to raise exception on non-zero exit (default: True).
        capture_output: Whether to capture stdout/stderr (default: False).
        timeout: Command timeout in seconds (default: None).

    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(cmd, check=check, capture_output=capture_output, text=True, timeout=timeout)
        return result.returncode, result.stdout if capture_output else "", result.stderr if capture_output else ""
    except subprocess.CalledProcessError as e:
        logger.debug("Command failed with code %d: %s", e.returncode, " ".join(cmd))
        return e.returncode, e.stdout if capture_output else "", e.stderr if capture_output else ""
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after %ds: %s", timeout, " ".join(cmd))
        return 124, "", f"Command timed out: {cmd[0]}"
    except FileNotFoundError:
        logger.error("Command not found: %s", cmd[0])
        return 1, "", f"Command not found: {cmd[0]}"


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    return shutil.which(cmd) is not None


def get_gpu_info() -> Optional[Dict]:
    """Detect GPU vendor, name, and VRAM.

    Returns:
        Dict with vendor, name, and vram_gb if GPU detected, None otherwise.
    """
    try:
        # Try nvidia-smi for NVIDIA GPUs
        code, stdout, _ = run_command(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], check=False, capture_output=True
        )
        if code == 0 and stdout:
            lines = stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                if len(parts) == 2:
                    name, vram = parts
                    vram_gb = int(vram.strip().split()[0]) / 1024
                    return {"vendor": "NVIDIA", "name": name.strip(), "vram_gb": vram_gb}
                else:
                    logger.warning("Unexpected nvidia-smi output format (expected 2 values, got %d)", len(parts))
    except FileNotFoundError:
        logger.debug("nvidia-smi not found, no NVIDIA GPU detected")
    except (ValueError, IndexError) as e:
        logger.warning("Failed to parse GPU info: %s", str(e))
    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Unexpected error detecting GPU: %s", str(e))

    return None


def recommend_ollama_model(vram_gb: float) -> List[str]:
    """Recommend Ollama models based on VRAM

    Args:
        vram_gb: Available VRAM in gigabytes

    Returns:
        List of recommended model names for Ollama
    """
    if vram_gb >= 16:
        return ["qwen2.5:32b-instruct-fp16", "qwen2.5:32b-instruct-q4_K_M", "qwen2.5:14b-instruct-q4_K_M"]
    elif vram_gb >= 12:
        return ["qwen2.5:32b-instruct-q4_K_M", "qwen2.5:14b-instruct-q4_K_M"]
    elif vram_gb >= 8:
        return ["qwen2.5:14b-instruct-q4_K_M", "llama3.2:3b"]
    else:
        return ["llama3.2:3b", "qwen2.5:7b-instruct-q4_K_M"]


def check_docker() -> bool:
    """Check if Docker is installed and running"""
    print_header("Checking Docker")

    if not check_command_exists("docker"):
        print_error("Docker is not installed")
        print_info("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False

    print_success("Docker is installed")

    # Check if Docker daemon is running
    code, _, _ = run_command(["docker", "ps"], check=False, capture_output=True)
    if code != 0:
        print_error("Docker daemon is not running")
        print_info("Please start Docker Desktop")
        return False

    print_success("Docker daemon is running")
    return True


def check_git() -> bool:
    """Check if Git is installed"""
    print_header("Checking Git")

    if not check_command_exists("git"):
        print_error("Git is not installed")
        return False

    print_success("Git is installed")
    return True


def setup_env_file(project_root: Path) -> bool:
    """Setup .env file from template"""
    print_header("Setting up .env file")

    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        print_warning(f".env already exists at {env_file}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != "y":
            print_info("Keeping existing .env file")
            return True

    if not env_example.exists():
        print_error(f".env.example not found at {env_example}")
        return False

    shutil.copy(env_example, env_file)
    print_success(f"Created .env file at {env_file}")
    print_warning("⚠️  Please edit .env and add your API keys:")
    print_info("  - GEMINI_API_KEY (get from https://aistudio.google.com/app/apikey)")
    print_info("  - GITHUB_TOKEN (optional, for GitHub Copilot features)")
    print_info("  - OPENAI_API_KEY (optional)")

    return True


def check_ollama() -> Tuple[bool, Optional[str]]:
    """Check if Ollama is installed and get version"""
    if not check_command_exists("ollama"):
        return False, None

    code, stdout, _ = run_command(["ollama", "--version"], check=False, capture_output=True)
    if code == 0:
        return True, stdout.strip()
    return False, None


def setup_ollama(gpu_info: Optional[dict]) -> bool:
    """Setup Ollama and pull recommended models"""
    print_header("Setting up Ollama (Local LLM)")

    installed, version = check_ollama()

    if not installed:
        print_warning("Ollama is not installed")
        print_info("Installation instructions:")

        system = platform.system()
        if system == "Windows":
            print_info("  Windows: Download from https://ollama.ai/download")
        elif system == "Darwin":
            print_info("  Mac: brew install ollama")
        else:
            print_info("  Linux: curl -fsSL https://ollama.ai/install.sh | sh")

        response = input("\nHave you installed Ollama? (y/N): ").strip().lower()
        if response != "y":
            print_info("Skipping Ollama setup. You can run this script again later.")
            return False

        # Re-check after installation
        installed, version = check_ollama()
        if not installed:
            print_error("Ollama still not detected. Please check installation.")
            return False

    print_success(f"Ollama is installed: {version}")

    # Check if Ollama server is running
    code, _, _ = run_command(["ollama", "list"], check=False, capture_output=True)
    if code != 0:
        print_warning("Ollama server may not be running")
        print_info("Starting Ollama server...")
        # On Windows/Mac, Ollama runs as a service. On Linux, may need manual start.
        if platform.system() == "Linux":
            print_info("Run: ollama serve &")

    # Get list of installed models
    code, stdout, _ = run_command(["ollama", "list"], check=False, capture_output=True)
    installed_models = []
    if code == 0 and stdout:
        installed_models = [line.split()[0] for line in stdout.strip().split("\n")[1:] if line]

    print_info(f"Currently installed models: {', '.join(installed_models) if installed_models else 'None'}")

    # Recommend models based on GPU
    if gpu_info:
        recommended = recommend_ollama_model(gpu_info["vram_gb"])
        print_info(f"Recommended models for {gpu_info['name']} ({gpu_info['vram_gb']:.1f}GB VRAM):")
        for i, model in enumerate(recommended, 1):
            status = "✓ installed" if model in installed_models else "not installed"
            print_info(f"  {i}. {model} ({status})")

        if not all(model in installed_models for model in recommended):
            response = (
                input(f"\nPull recommended model '{recommended[0]}'? This may take several minutes. (y/N): ")
                .strip()
                .lower()
            )
            if response == "y":
                print_info(f"Pulling {recommended[0]}...")
                code, _, _ = run_command(["ollama", "pull", recommended[0]], check=False)
                if code == 0:
                    print_success(f"Successfully pulled {recommended[0]}")
                else:
                    print_error(f"Failed to pull {recommended[0]}")
                    return False
    else:
        print_info("No GPU detected. Consider using qwen2.5:7b-instruct-q4_K_M for CPU")

    return True


def start_docker_services(project_root: Path) -> bool:
    """Start Docker services"""
    print_header("Starting Docker Services")

    compose_file = project_root / "docker-compose.yml"
    if not compose_file.exists():
        print_error(f"docker-compose.yml not found at {compose_file}")
        return False

    print_info("Starting services with docker compose up -d...")
    code, stdout, stderr = run_command(["docker", "compose", "up", "-d"], check=False, capture_output=True)

    if code != 0:
        print_error("Failed to start Docker services")
        print_error(stderr)
        return False

    print_success("Docker services started")

    # List running services
    print_info("\nChecking service status...")
    code, stdout, _ = run_command(["docker", "compose", "ps"], check=False, capture_output=True)
    if code == 0:
        print(stdout)

    return True


def verify_setup(project_root: Path) -> bool:
    """Verify complete setup"""
    print_header("Verifying Setup")

    checks = []

    # Check .env exists
    env_file = project_root / ".env"
    checks.append(("Environment file (.env)", env_file.exists()))

    # Check Docker services (expecting core services: ui, worker, ai-monitor)
    code, stdout, _ = run_command(["docker", "compose", "ps"], check=False, capture_output=True)
    expected_services = {"ui", "worker", "ai-monitor"}
    if code == 0 and stdout:
        # Check if expected services are running
        running_service_names = {line.split()[0] for line in stdout.split("\n") if "Up" in line and line.strip()}
        services_ok = len(expected_services.intersection(running_service_names)) >= 2
        checks.append(("Docker services running", services_ok))
    else:
        checks.append(("Docker services running", False))

    # Check Ollama
    ollama_installed, _ = check_ollama()
    checks.append(("Ollama installed", ollama_installed))

    # Print results
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")
            all_passed = False

    return all_passed


def main() -> None:
    """Main entry point for the AI agent setup CLI."""
    parser = argparse.ArgumentParser(description="AI Agent Setup Utility - Automate parallel AI development setup")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker setup and service startup")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama setup")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    print_header("AI Agent Parallel Work Setup")
    print_info(f"Platform: {platform.system()} {platform.release()}")
    print_info(f"Python: {sys.version.split()[0]}")
    print_info(f"Project root: {args.project_root.absolute()}")

    # Detect GPU
    gpu_info = get_gpu_info()
    if gpu_info:
        print_success(f"GPU detected: {gpu_info['name']} ({gpu_info['vram_gb']:.1f}GB VRAM)")
    else:
        print_info("No NVIDIA GPU detected (CPU mode)")

    # Check prerequisites
    if not check_git():
        print_error("Git is required. Please install Git first.")
        sys.exit(1)

    if not args.skip_docker and not check_docker():
        print_error("Docker is required. Please install and start Docker Desktop first.")
        sys.exit(1)

    # Setup .env file
    if not setup_env_file(args.project_root):
        print_error("Failed to setup .env file")
        sys.exit(1)

    # Setup Ollama
    if not args.skip_ollama:
        setup_ollama(gpu_info)

    # Start Docker services
    if not args.skip_docker:
        if not start_docker_services(args.project_root):
            print_error("Failed to start Docker services")
            sys.exit(1)

    # Verify setup
    print()
    if verify_setup(args.project_root):
        print_header("Setup Complete! 🎉")
        print_success("Your AI agent development environment is ready!")
        print_info("\nNext steps:")
        print_info("  1. Edit .env and add your API keys")
        print_info("  2. Access Vibe Check MCP at http://localhost:3000")
        print_info("  3. Access Vibe Kanban at http://localhost:3001")
        print_info("  4. Read PARALLEL_WORK_STRATEGY.md for execution plan")
    else:
        print_header("Setup Incomplete")
        print_warning("Some components failed to setup. Please check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
