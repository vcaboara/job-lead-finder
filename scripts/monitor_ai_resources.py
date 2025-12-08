#!/usr/bin/env python3
"""
LLM Resource Monitor
Monitors usage of AI resources (Copilot, Gemini, Local LLM) and provides recommendations.
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ResourceMonitor:
    """Monitor AI resource usage and quotas"""

    def __init__(self, tracking_file: Path = Path(".ai_usage_tracking.json")):
        self.tracking_file = tracking_file
        self.data = self._load_tracking_data()

    def _load_tracking_data(self) -> dict:
        """Load usage tracking data"""
        if self.tracking_file.exists():
            with open(self.tracking_file) as f:
                return json.load(f)
        return {
            "copilot": {"daily": {}, "monthly_limit": 1500},
            "gemini": {"daily": {}, "daily_limit": 20},
            "local_llm": {"sessions": []},
        }

    def _save_tracking_data(self):
        """Save usage tracking data"""
        with open(self.tracking_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def record_copilot_usage(self, count: int = 1):
        """Record Copilot usage"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["copilot"]["daily"]:
            self.data["copilot"]["daily"][today] = 0
        self.data["copilot"]["daily"][today] += count
        self._save_tracking_data()

    def record_gemini_usage(self, count: int = 1):
        """Record Gemini API usage"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["gemini"]["daily"]:
            self.data["gemini"]["daily"][today] = 0
        self.data["gemini"]["daily"][today] += count
        self._save_tracking_data()

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
        remaining = monthly_limit - monthly_usage

        return {
            "daily": daily_usage,
            "monthly": monthly_usage,
            "monthly_limit": monthly_limit,
            "remaining": remaining,
            "percentage_used": (monthly_usage / monthly_limit) * 100 if monthly_limit > 0 else 0,
        }

    def get_gemini_usage(self) -> Dict[str, int]:
        """Get Gemini API usage stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_usage = self.data["gemini"]["daily"].get(today, 0)
        daily_limit = self.data["gemini"]["daily_limit"]
        remaining = daily_limit - daily_usage

        return {
            "daily": daily_usage,
            "daily_limit": daily_limit,
            "remaining": remaining,
            "percentage_used": (daily_usage / daily_limit) * 100 if daily_limit > 0 else 0,
        }

    def check_ollama_status(self) -> Optional[dict]:
        """Check Ollama server status and running models"""
        try:
            result = subprocess.run(["ollama", "ps"], capture_output=True, text=True, check=False)

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
            return {"status": "not_installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

        return {"status": "offline"}

    def check_gpu_usage(self) -> Optional[dict]:
        """Check GPU utilization"""
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
                return gpus
        except (FileNotFoundError, Exception):
            # nvidia-smi not available or parsing failed - GPU monitoring is optional
            pass

        return None

    def get_recommendations(self) -> List[str]:
        """Get usage recommendations"""
        recommendations = []

        copilot = self.get_copilot_usage()
        gemini = self.get_gemini_usage()

        # Copilot recommendations
        if copilot["percentage_used"] > 80:
            recommendations.append(
                f"⚠️  Copilot usage at {copilot['percentage_used']:.0f}% "
                f"({copilot['remaining']} requests remaining this month). "
                "Consider using Gemini or Local LLM for simpler tasks."
            )
        elif copilot["percentage_used"] > 50:
            recommendations.append(
                f"ℹ️  Copilot usage at {copilot['percentage_used']:.0f}%. " "Pace yourself to last the month."
            )

        # Gemini recommendations
        if gemini["percentage_used"] > 80:
            recommendations.append(
                f"⚠️  Gemini quota at {gemini['percentage_used']:.0f}% "
                f"({gemini['remaining']} requests remaining today). "
                "Switch to Local LLM for remaining tasks."
            )
        elif gemini["remaining"] == gemini["daily_limit"]:
            recommendations.append(f"✓ Gemini quota fully available ({gemini['daily_limit']} requests today)")

        # Ollama recommendations
        ollama_status = self.check_ollama_status()
        if ollama_status:
            if ollama_status["status"] == "not_installed":
                recommendations.append("💡 Install Ollama for unlimited local LLM usage (no API costs)")
            elif ollama_status["status"] == "offline":
                recommendations.append("⚠️  Ollama is offline. Start it with: ollama serve")
            elif ollama_status["status"] == "running":
                if ollama_status["models"]:
                    model_names = [m["name"] for m in ollama_status["models"]]
                    recommendations.append(f"✓ Ollama running with models: {', '.join(model_names)}")
                else:
                    recommendations.append("✓ Ollama is running (no active models)")

        # GPU recommendations
        gpus = self.check_gpu_usage()
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

    def print_status(self):
        """Print formatted status report"""
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


def main():
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
