#!/usr/bin/env python3
"""
LLM Resource Monitor
Monitors usage of AI resources (Copilot, Gemini, Local LLM) and provides recommendations.
"""

import argparse
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor AI resource usage and quotas"""

    def __init__(self, tracking_file: Path = Path(".ai_usage_tracking.json")):
        self.tracking_file = tracking_file
        self.data = self._load_tracking_data()

    def _load_tracking_data(self) -> Dict:
        """Load usage tracking data from JSON file.

        Returns:
            Dict containing tracking data for all AI providers.
            Default structure if file doesn't exist.
        """
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load tracking data: %s. Using defaults.", str(e))
        return {
            "copilot": {"daily": {}, "monthly_limit": 1500},
            "gemini": {"daily": {}, "daily_limit": 20},
            "local_llm": {"sessions": []},
        }

    def _save_tracking_data(self) -> None:
        """Save usage tracking data to JSON file.

        Raises:
            IOError: If file write fails.
        """
        try:
            with open(self.tracking_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            logger.error("Failed to save tracking data: %s", str(e))
            raise

    def record_copilot_usage(self, count: int = 1) -> None:
        """Record Copilot usage for the current day.

        Args:
            count: Number of requests to record (default: 1).
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["copilot"]["daily"]:
            self.data["copilot"]["daily"][today] = 0
        self.data["copilot"]["daily"][today] += count
        self._save_tracking_data()
        logger.debug("Recorded %d Copilot request(s) for %s", count, today)

    def record_gemini_usage(self, count: int = 1) -> None:
        """Record Gemini API usage for the current day.

        Args:
            count: Number of requests to record (default: 1).
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["gemini"]["daily"]:
            self.data["gemini"]["daily"][today] = 0
        self.data["gemini"]["daily"][today] += count
        self._save_tracking_data()
        logger.debug("Recorded %d Gemini request(s) for %s", count, today)

    def get_copilot_usage(self) -> Dict[str, int]:
        """Get Copilot usage stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        this_month = datetime.now().strftime("%Y-%m")

        daily_usage = self.data["copilot"]["daily"].get(today, 0)

        # Calculate monthly usage
        monthly_usage = sum(
            count for date, count in self.data["copilot"]["daily"].items() if date.startswith(this_month)
        )

        monthly_limit = self.data["copilot"]["monthly_limit"]

        # Validate that limit is positive
        if monthly_limit <= 0:
            logger.warning("Copilot monthly_limit is %d, should be positive", monthly_limit)
            return {
                "daily": daily_usage,
                "monthly": monthly_usage,
                "monthly_limit": monthly_limit,
                "remaining": 0,
                "percentage_used": 100.0 if monthly_usage > 0 else 0.0,
            }

        remaining = monthly_limit - monthly_usage

        return {
            "daily": daily_usage,
            "monthly": monthly_usage,
            "monthly_limit": monthly_limit,
            "remaining": remaining,
            "percentage_used": (monthly_usage / monthly_limit) * 100,
        }

    def get_gemini_usage(self) -> Dict[str, int]:
        """Get Gemini API usage stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_usage = self.data["gemini"]["daily"].get(today, 0)
        daily_limit = self.data["gemini"]["daily_limit"]

        # Validate that limit is positive
        if daily_limit <= 0:
            logger.warning("Gemini daily_limit is %d, should be positive", daily_limit)
            return {
                "daily": daily_usage,
                "daily_limit": daily_limit,
                "remaining": 0,
                "percentage_used": 100.0 if daily_usage > 0 else 0.0,
            }

        remaining = daily_limit - daily_usage

        return {
            "daily": daily_usage,
            "daily_limit": daily_limit,
            "remaining": remaining,
            "percentage_used": (daily_usage / daily_limit) * 100,
        }

    def check_ollama_status(self) -> Optional[Dict]:
        """Check Ollama server status and running models.

        Returns:
            Dict with status and models if Ollama is available, None otherwise.
        """
        try:
            result = subprocess.run(["ollama", "ps"], capture_output=True, text=True, check=False, timeout=5)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Header + models
                    running_models = []
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if parts:
                                running_models.append(
                                    {
                                        "name": parts[0],
                                        "size": parts[2] if len(parts) > 2 else "unknown",
                                        "until": " ".join(parts[4:]) if len(parts) > 4 else "unknown",
                                    }
                                )
                    return {"status": "running", "models": running_models}
                return {"status": "running", "models": []}
        except FileNotFoundError:
            logger.debug("Ollama not installed")
            return {"status": "not_installed"}
        except subprocess.TimeoutExpired:
            logger.warning("Ollama command timed out")
            return {"status": "timeout"}
        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Error checking Ollama status: %s", str(e))
            return {"status": "error", "error": str(e)}

        return {"status": "offline"}

    def check_gpu_usage(self) -> Optional[List[Dict]]:
        """Check GPU utilization and memory usage.

        Returns:
            List of dicts with GPU metrics for each GPU, or None if nvidia-smi unavailable.
        """
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                gpus = []
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 4:
                            gpus.append(
                                {
                                    "gpu_util": float(parts[0]),
                                    "mem_util": float(parts[1]),
                                    "mem_used_mb": float(parts[2]),
                                    "mem_total_mb": float(parts[3]),
                                }
                            )
                return gpus if gpus else None
        except FileNotFoundError:
            logger.debug("nvidia-smi not found, GPU monitoring unavailable")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi command timed out")
        except (ValueError, IndexError) as e:
            logger.error("Failed to parse GPU data: %s", str(e))
        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Unexpected error checking GPU usage: %s", str(e))

        return None

    def _get_copilot_recommendations(self, copilot: Dict[str, float]) -> Optional[str]:
        """Get recommendation for Copilot usage.

        Args:
            copilot: Copilot usage data.

        Returns:
            Recommendation string or None.
        """
        if copilot["monthly_limit"] <= 0:
            return (
                "⚠️  Copilot monthly_limit is invalid (set to 0 or negative). "
                "Please update configuration with a positive limit."
            )

        if copilot["percentage_used"] > 80:
            return (
                f"⚠️  Copilot usage at {copilot['percentage_used']:.0f}% "
                f"({copilot['remaining']} requests remaining this month). "
                "Consider using Gemini or Local LLM for simpler tasks."
            )

        if copilot["percentage_used"] > 50:
            return f"ℹ️  Copilot usage at {copilot['percentage_used']:.0f}%. Pace yourself to last the month."

        return None

    def _get_gemini_recommendations(self, gemini: Dict[str, float]) -> Optional[str]:
        """Get recommendation for Gemini usage.

        Args:
            gemini: Gemini usage data.

        Returns:
            Recommendation string or None.
        """
        if gemini["daily_limit"] <= 0:
            return (
                "⚠️  Gemini daily_limit is invalid (set to 0 or negative). "
                "Please update configuration with a positive limit."
            )

        if gemini["percentage_used"] > 80:
            return (
                f"⚠️  Gemini quota at {gemini['percentage_used']:.0f}% "
                f"({gemini['remaining']} requests remaining today). "
                "Switch to Local LLM for remaining tasks."
            )

        if gemini["remaining"] == gemini["daily_limit"]:
            return f"✓ Gemini quota fully available ({gemini['daily_limit']} requests today)"

        return None

    def _get_ollama_recommendations(self, ollama_status: Optional[Dict]) -> Optional[str]:
        """Get recommendation for Ollama status.

        Args:
            ollama_status: Ollama status data.

        Returns:
            Recommendation string or None.
        """
        if not ollama_status:
            return None

        status_recommendations = {
            "not_installed": "💡 Install Ollama for unlimited local LLM usage (no API costs)",
            "offline": "⚠️  Ollama is offline. Start it with: ollama serve",
        }

        if ollama_status["status"] in status_recommendations:
            return status_recommendations[ollama_status["status"]]

        if ollama_status["status"] == "running":
            if ollama_status["models"]:
                model_names = [m["name"] for m in ollama_status["models"]]
                return f"✓ Ollama running with models: {', '.join(model_names)}"
            return "✓ Ollama is running (no active models)"

        return None

    def get_recommendations(self) -> List[str]:
        """Get usage recommendations"""
        recommendations = []

        copilot = self.get_copilot_usage()
        gemini = self.get_gemini_usage()
        ollama_status = self.check_ollama_status()
        gpus = self.check_gpu_usage()

        # Add provider recommendations
        for recommendation in [
            self._get_copilot_recommendations(copilot),
            self._get_gemini_recommendations(gemini),
            self._get_ollama_recommendations(ollama_status),
        ]:
            if recommendation:
                recommendations.append(recommendation)

        # GPU recommendations
        if gpus:
            for i, gpu in enumerate(gpus):
                if gpu["gpu_util"] > 90:
                    recommendations.append(
                        f"⚠️  GPU {i} at {gpu['gpu_util']:.0f}% utilization. " "Consider using a smaller model."
                    )
                elif gpu["mem_used_mb"] / gpu["mem_total_mb"] > 0.9:
                    recommendations.append(
                        f"⚠️  GPU {i} memory at {(gpu['mem_used_mb'] / gpu['mem_total_mb'] * 100):.0f}%. "
                        "Consider using a quantized model."
                    )

        return recommendations

    def print_status(self) -> None:
        """Print formatted status report to console.

        Note: This method uses print() for formatted console output.
        For logging, use the logger instead.
        """
        print("\n" + "=" * 60)
        print("AI Resource Usage Monitor")
        print("=" * 60 + "\n")

        # Copilot status
        copilot = self.get_copilot_usage()
        print("GitHub Copilot Pro:")
        print(f"  Today: {copilot['daily']} requests")
        print(f"  This Month: {copilot['monthly']}/{copilot['monthly_limit']} requests")
        print(f"  Remaining: {copilot['remaining']} ({100 - copilot['percentage_used']:.1f}%)")

        # Progress bar
        bar_length = 40
        filled = int(bar_length * copilot["percentage_used"] / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  [{bar}] {copilot['percentage_used']:.1f}%\n")

        # Gemini status
        gemini = self.get_gemini_usage()
        print("Gemini API:")
        print(f"  Today: {gemini['daily']}/{gemini['daily_limit']} requests")
        print(f"  Remaining: {gemini['remaining']} ({100 - gemini['percentage_used']:.1f}%)")

        filled = int(bar_length * gemini["percentage_used"] / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  [{bar}] {gemini['percentage_used']:.1f}%\n")

        # Ollama status
        ollama_status = self.check_ollama_status()
        print("Local LLM (Ollama):")
        if ollama_status:
            print(f"  Status: {ollama_status['status']}")
            if ollama_status.get("models"):
                print("  Active Models:")
                for model in ollama_status["models"]:
                    print(f"    - {model['name']} ({model['size']})")
            else:
                print("  Active Models: None")
        else:
            print("  Status: unknown")
        print()

        # GPU status
        gpus = self.check_gpu_usage()
        if gpus:
            print("GPU Status:")
            for i, gpu in enumerate(gpus):
                print(f"  GPU {i}:")
                print(f"    Utilization: {gpu['gpu_util']:.0f}%")
                print(
                    f"    Memory: {gpu['mem_used_mb']:.0f}MB / {gpu['mem_total_mb']:.0f}MB "
                    f"({gpu['mem_used_mb'] / gpu['mem_total_mb'] * 100:.0f}%)"
                )
            print()

        # Recommendations
        recommendations = self.get_recommendations()
        if recommendations:
            print("Recommendations:")
            for rec in recommendations:
                print(f"  {rec}")
            print()


def main() -> None:
    """Main entry point for the resource monitor CLI."""
    parser = argparse.ArgumentParser(description="Monitor AI resource usage and get optimization recommendations")
    parser.add_argument("--record-copilot", type=int, metavar="COUNT", help="Record Copilot usage (number of requests)")
    parser.add_argument(
        "--record-gemini", type=int, metavar="COUNT", help="Record Gemini API usage (number of requests)"
    )
    parser.add_argument("--status", action="store_true", help="Show current usage status (default action)")
    parser.add_argument("--reset", action="store_true", help="Reset usage tracking data")

    args = parser.parse_args()

    monitor = ResourceMonitor()

    if args.reset:
        if monitor.tracking_file.exists():
            monitor.tracking_file.unlink()
            print("✓ Usage tracking data reset")
        else:
            print("ℹ️  No tracking data to reset")
        return

    if args.record_copilot:
        monitor.record_copilot_usage(args.record_copilot)
        print(f"✓ Recorded {args.record_copilot} Copilot request(s)")

    if args.record_gemini:
        monitor.record_gemini_usage(args.record_gemini)
        print(f"✓ Recorded {args.record_gemini} Gemini request(s)")

    # Default action: show status
    if args.status or not any([args.record_copilot, args.record_gemini, args.reset]):
        monitor.print_status()


if __name__ == "__main__":
    main()
