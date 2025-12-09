#!/usr/bin/env python3
"""
AI Resource Monitor Web UI
Provides a graphical dashboard for monitoring AI resource usage across providers.
Runs as a containerized service accessible via web browser.
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template_string

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# HTML template with Chart.js for visualization (lovable.dev dark theme)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Resource Monitor</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap"
        rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --font-sans: 'DM Sans', system-ui, sans-serif;
            --font-display: 'Space Grotesk', system-ui, sans-serif;
            --background: 222 47% 6%;
            --foreground: 210 20% 98%;
            --card: 222 47% 9%;
            --card-foreground: 210 20% 98%;
            --primary: 217 91% 60%;
            --accent: 172 66% 50%;
            --muted: 215 16% 47%;
            --border: 217 33% 17%;
        }

        body {
            font-family: var(--font-sans);
            background: hsl(var(--background));
            color: hsl(var(--foreground));
            padding: 2rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            font-family: var(--font-display);
            font-size: 2.5rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--accent)) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .card {
            background: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(59, 130, 246, 0.15);
        }

        .card h2 {
            font-family: var(--font-display);
            color: hsl(var(--primary));
            margin-bottom: 1rem;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid hsl(var(--border));
        }

        .metric:last-child { border-bottom: none; }
        .metric-label { color: hsl(var(--muted)); font-weight: 500; }
        .metric-value { color: hsl(var(--foreground)); font-weight: 600; }
        .status-good { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-danger { color: #ef4444; }

        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }

        .refresh-info, .timestamp {
            text-align: center;
            color: hsl(var(--muted));
            font-size: 0.875rem;
            margin-top: 1rem;
        }

        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            h1 { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Resource Monitor</h1>

        <div class="grid">
            <!-- Copilot Card -->
            <div class="card">
                <h2>GitHub Copilot Pro</h2>
                <div class="metric">
                    <span class="metric-label">Today</span>
                    <span class="metric-value" id="copilot-daily">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">This Month</span>
                    <span class="metric-value" id="copilot-monthly">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Remaining</span>
                    <span class="metric-value" id="copilot-remaining">-</span>
                </div>
                <div class="chart-container">
                    <canvas id="copilotChart"></canvas>
                </div>
            </div>

            <!-- Gemini Card -->
            <div class="card">
                <h2>Gemini API</h2>
                <div class="metric">
                    <span class="metric-label">Today</span>
                    <span class="metric-value" id="gemini-daily">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Daily Limit</span>
                    <span class="metric-value">20 requests</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Remaining</span>
                    <span class="metric-value" id="gemini-remaining">-</span>
                </div>
                <div class="chart-container">
                    <canvas id="geminiChart"></canvas>
                </div>
            </div>

            <!-- Ollama Card -->
            <div class="card">
                <h2>Local LLM (Ollama)</h2>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value" id="ollama-status">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Models</span>
                    <span class="metric-value" id="ollama-models">-</span>
                </div>
                <div id="ollama-model-list" style="margin-top: 15px; font-size: 0.9em; color: #666;"></div>
            </div>

            <!-- GPU Card -->
            <div class="card">
                <h2>GPU Status</h2>
                <div class="metric">
                    <span class="metric-label">GPU Name</span>
                    <span class="metric-value" id="gpu-name">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Utilization</span>
                    <span class="metric-value" id="gpu-util">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">VRAM Usage</span>
                    <span class="metric-value" id="gpu-vram">-</span>
                </div>
                <div class="chart-container">
                    <canvas id="gpuChart"></canvas>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>💡 Recommendations</h2>
            <div id="recommendations" style="line-height: 1.8; color: hsl(var(--muted));"></div>
        </div>

        <div class="timestamp" id="timestamp">Last updated: -</div>
        <div class="refresh-info">Auto-refreshes every 30 seconds</div>
    </div>

    <script>
        let copilotChart, geminiChart, gpuChart;

        // Chart.js dark theme defaults
        Chart.defaults.color = 'hsl(210 20% 98%)';
        Chart.defaults.borderColor = 'hsl(217 33% 17%)';

        function initCharts() {
            // Copilot Chart
            const copilotCtx = document.getElementById('copilotChart').getContext('2d');
            copilotChart = new Chart(copilotCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Remaining'],
                    datasets: [{
                        data: [0, 1500],
                        backgroundColor: ['hsl(217 91% 60%)', 'hsl(217 33% 25%)'],
                        borderWidth: 2,
                        borderColor: 'hsl(222 47% 11%)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: { color: 'hsl(210 20% 98%)' }
                        }
                    }
                }
            });

            // Gemini Chart
            const geminiCtx = document.getElementById('geminiChart').getContext('2d');
            geminiChart = new Chart(geminiCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Remaining'],
                    datasets: [{
                        data: [0, 20],
                        backgroundColor: ['hsl(172 66% 50%)', 'hsl(217 33% 25%)'],
                        borderWidth: 2,
                        borderColor: 'hsl(222 47% 11%)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: { color: 'hsl(210 20% 98%)' }
                        }
                    }
                }
            });

            // GPU Chart
            const gpuCtx = document.getElementById('gpuChart').getContext('2d');
            gpuChart = new Chart(gpuCtx, {
                type: 'bar',
                data: {
                    labels: ['Utilization', 'VRAM'],
                    datasets: [{
                        label: 'Usage %',
                        data: [0, 0],
                        backgroundColor: ['hsl(172 66% 50%)', 'hsl(217 91% 60%)'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { color: 'hsl(210 20% 98%)' },
                            grid: { color: 'hsl(217 33% 17%)' }
                        },
                        x: {
                            ticks: { color: 'hsl(210 20% 98%)' },
                            grid: { color: 'hsl(217 33% 17%)' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        function updateDashboard() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    // Update Copilot
                    document.getElementById('copilot-daily').textContent = data.copilot.daily + ' requests';
                    document.getElementById('copilot-monthly').textContent =
                        `${data.copilot.monthly}/${data.copilot.monthly_limit} requests`;
                    document.getElementById('copilot-remaining').textContent =
                        data.copilot.remaining + ' requests';

                    copilotChart.data.datasets[0].data = [
                        data.copilot.monthly,
                        data.copilot.remaining
                    ];
                    copilotChart.update();

                    // Update Gemini
                    document.getElementById('gemini-daily').textContent =
                        `${data.gemini.daily}/${data.gemini.daily_limit} requests`;
                    document.getElementById('gemini-remaining').textContent =
                        data.gemini.remaining + ' requests';

                    geminiChart.data.datasets[0].data = [
                        data.gemini.daily,
                        data.gemini.remaining
                    ];
                    geminiChart.update();

                    // Update Ollama
                    document.getElementById('ollama-status').textContent = data.ollama.status || 'unknown';
                    document.getElementById('ollama-models').textContent =
                        data.ollama.model_count || '0';

                    if (data.ollama.models && data.ollama.models.length > 0) {
                        document.getElementById('ollama-model-list').innerHTML =
                            data.ollama.models.map(m => `• ${m.name} (${m.size})`).join('<br>');
                    } else {
                        document.getElementById('ollama-model-list').innerHTML = 'No active models';
                    }

                    // Update GPU
                    if (data.gpu) {
                        document.getElementById('gpu-name').textContent = data.gpu.name || 'N/A';
                        document.getElementById('gpu-util').textContent =
                            data.gpu.gpu_util ? `${data.gpu.gpu_util.toFixed(0)}%` : 'N/A';

                        const vramUsed = data.gpu.mem_used_mb / 1024;
                        const vramTotal = data.gpu.mem_total_mb / 1024;
                        document.getElementById('gpu-vram').textContent =
                            data.gpu.mem_used_mb && data.gpu.mem_total_mb
                                ? `${vramUsed.toFixed(1)}GB / ${vramTotal.toFixed(1)}GB`
                                : 'N/A';

                        const vramPercent = data.gpu.mem_total_mb
                            ? (data.gpu.mem_used_mb / data.gpu.mem_total_mb * 100)
                            : 0;

                        gpuChart.data.datasets[0].data = [
                            data.gpu.gpu_util || 0,
                            vramPercent
                        ];
                        gpuChart.update();
                    }

                    // Update Recommendations
                    if (data.recommendations && data.recommendations.length > 0) {
                        document.getElementById('recommendations').innerHTML =
                            data.recommendations.map(r => `• ${r}`).join('<br>');
                    } else {
                        document.getElementById('recommendations').innerHTML =
                            '✓ All systems operating within normal parameters';
                    }

                    // Update timestamp
                    document.getElementById('timestamp').textContent =
                        'Last updated: ' + new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching metrics:', error);
                });
        }

        // Initialize
        initCharts();
        updateDashboard();
        setInterval(updateDashboard, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""


class AIResourceMonitor:
    """Monitor AI resource usage across providers."""

    def __init__(self, tracking_file: Optional[str] = None):
        if tracking_file is None:
            import os

            tracking_file = os.getenv("AI_TRACKING_FILE", ".ai_usage_tracking.json")
        self.tracking_file = Path(tracking_file)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load tracking data from JSON file.

        Returns:
            Dict containing tracking data. Returns default structure if file missing or invalid.
        """
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load tracking data: %s. Using defaults.", str(e))
                return self._init_data()
        return self._init_data()

    def _init_data(self) -> Dict:
        """Initialize empty tracking data."""
        return {
            "copilot": {"daily": [], "monthly": []},
            "gemini": {"daily": []},
        }

    def get_copilot_usage(self) -> Dict[str, float]:
        """Get Copilot usage statistics.

        Returns:
            Dict with daily, monthly, monthly_limit, remaining, and percentage_used.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")

        daily_count = sum(1 for entry in self.data.get("copilot", {}).get("daily", []) if entry["date"] == today)
        monthly_count = sum(
            1 for entry in self.data.get("copilot", {}).get("monthly", []) if entry["month"] == current_month
        )

        monthly_limit = 1500

        # Validate that limit is positive (future-proofing if limit becomes configurable)
        if monthly_limit <= 0:
            logger.warning("Copilot monthly_limit is %d, should be positive", monthly_limit)
            return {
                "daily": daily_count,
                "monthly": monthly_count,
                "monthly_limit": monthly_limit,
                "remaining": 0,
                "percentage_used": 100.0 if monthly_count > 0 else 0.0,
            }

        return {
            "daily": daily_count,
            "monthly": monthly_count,
            "monthly_limit": monthly_limit,
            "remaining": max(0, monthly_limit - monthly_count),
            "percentage_used": (monthly_count / monthly_limit * 100),
        }

    def get_gemini_usage(self) -> Dict[str, float]:
        """Get Gemini API usage statistics.

        Returns:
            Dict with daily, daily_limit, remaining, and percentage_used.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        daily_count = sum(1 for entry in self.data.get("gemini", {}).get("daily", []) if entry["date"] == today)

        daily_limit = 20

        # Validate that limit is positive (future-proofing if limit becomes configurable)
        if daily_limit <= 0:
            logger.warning("Gemini daily_limit is %d, should be positive", daily_limit)
            return {
                "daily": daily_count,
                "daily_limit": daily_limit,
                "remaining": 0,
                "percentage_used": 100.0 if daily_count > 0 else 0.0,
            }

        return {
            "daily": daily_count,
            "daily_limit": daily_limit,
            "remaining": max(0, daily_limit - daily_count),
            "percentage_used": (daily_count / daily_limit * 100),
        }

    def check_ollama_status(self) -> Optional[Dict]:
        """Check Ollama server status and running models.

        Returns:
            Dict with status, models list, and model_count if Ollama available, None otherwise.
        """
        try:
            result = subprocess.run(
                ["ollama", "ps"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) <= 1:
                    return {"status": "running", "models": [], "model_count": 0}

                models = []
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 3:
                        models.append({"name": parts[0], "size": parts[2] if len(parts) > 2 else "unknown"})

                return {"status": "running", "models": models, "model_count": len(models)}

            # Non-zero return code - Ollama not running or command failed
            if result.stderr:
                logger.debug("Ollama ps command failed (rc=%d): %s", result.returncode, result.stderr.strip())
            return {"status": "not running", "models": [], "model_count": 0}

        except FileNotFoundError:
            logger.debug("Ollama command not found - Ollama not installed")
            return None
        except subprocess.TimeoutExpired:
            logger.warning("Ollama ps command timed out after 5 seconds")
            return None

    def check_gpu_usage(self) -> Optional[Dict]:
        """Check GPU utilization and memory usage.

        Returns:
            Dict with GPU name, utilization, and memory stats if available, None otherwise.
        """
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split("\n")[0]
                parts = [p.strip() for p in line.split(",")]

                if len(parts) >= 4:
                    return {
                        "name": parts[0],
                        "gpu_util": float(parts[1]),
                        "mem_used_mb": float(parts[2]),
                        "mem_total_mb": float(parts[3]),
                    }

            # Non-zero return code or empty output
            if result.returncode != 0 and result.stderr:
                logger.debug("nvidia-smi command failed (rc=%d): %s", result.returncode, result.stderr.strip())

        except FileNotFoundError:
            logger.debug("nvidia-smi command not found - NVIDIA GPU drivers not installed")
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi command timed out after 5 seconds")
        except ValueError as e:
            logger.warning("Failed to parse nvidia-smi output: %s", e)

        return None

    def get_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current usage.

        Returns:
            List of recommendation strings for resource optimization.
        """
        recommendations = []

        copilot = self.get_copilot_usage()
        if copilot["monthly_limit"] <= 0:
            recommendations.append("⚠️ Copilot monthly_limit is invalid. Please update configuration.")
        elif copilot["percentage_used"] > 80:
            recommendations.append(
                f"⚠️ Copilot usage at {copilot['percentage_used']:.0f}% "
                f"({copilot['remaining']} requests remaining) - Consider using Gemini or Local LLM"
            )

        gemini = self.get_gemini_usage()
        if gemini["daily_limit"] <= 0:
            recommendations.append("⚠️ Gemini daily_limit is invalid. Please update configuration.")
        elif gemini["percentage_used"] > 80:
            recommendations.append(
                f"⚠️ Gemini API usage at {gemini['percentage_used']:.0f}% "
                f"({gemini['remaining']} requests remaining) - Switch to Local LLM or Copilot"
            )

        gpu = self.check_gpu_usage()
        if gpu and gpu["gpu_util"] > 90:
            recommendations.append(f"⚠️ GPU utilization high ({gpu['gpu_util']:.0f}%) - Monitor performance")

        if gpu and gpu["mem_total_mb"] > 0:
            vram_usage = (gpu["mem_used_mb"] / gpu["mem_total_mb"]) * 100
            if vram_usage > 90:
                recommendations.append(
                    f"⚠️ VRAM usage high ({vram_usage:.0f}%) - Consider using smaller model or reducing batch size"
                )

        ollama = self.check_ollama_status()
        if ollama and ollama["status"] == "running" and ollama["model_count"] == 0:
            recommendations.append("💡 Ollama is running but no models loaded - Ready for unlimited local inference")

        return recommendations


monitor = AIResourceMonitor()


@app.route("/")
def dashboard() -> str:
    """Serve the dashboard HTML page.

    Returns:
        Rendered HTML template.
    """
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/metrics")
def get_metrics() -> Dict:
    """API endpoint for current metrics.

    Returns:
        JSON response with all provider metrics and recommendations.
    """
    return jsonify(
        {
            "copilot": monitor.get_copilot_usage(),
            "gemini": monitor.get_gemini_usage(),
            "ollama": monitor.check_ollama_status() or {},
            "gpu": monitor.check_gpu_usage(),
            "recommendations": monitor.get_recommendations(),
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    # Development server - for production, use a WSGI server like Gunicorn or Waitress
    # Example: gunicorn app.ai_monitor_ui:app --bind 0.0.0.0:9000
    app.run(host="0.0.0.0", port=9000, debug=False)
