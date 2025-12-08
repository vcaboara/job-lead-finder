#!/usr/bin/env python3
"""
AI Resource Monitor Web UI
Provides a graphical dashboard for monitoring AI resource usage across providers.
Runs as a containerized service accessible via web browser.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# HTML template with Chart.js for visualization
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Resource Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #666; font-weight: 500; }
        .metric-value { color: #333; font-weight: 600; }
        .status-good { color: #10b981; }
        .status-warning { color: #f59e0b; }
        .status-danger { color: #ef4444; }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 15px;
        }
        .refresh-info {
            text-align: center;
            color: white;
            font-size: 0.9em;
            margin-top: 20px;
        }
        .timestamp {
            text-align: center;
            color: rgba(255,255,255,0.8);
            font-size: 0.85em;
            margin-top: 10px;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
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
            <div id="recommendations" style="line-height: 1.8; color: #666;"></div>
        </div>

        <div class="timestamp" id="timestamp">Last updated: -</div>
        <div class="refresh-info">Auto-refreshes every 30 seconds</div>
    </div>

    <script>
        let copilotChart, geminiChart, gpuChart;

        function initCharts() {
            // Copilot Chart
            const copilotCtx = document.getElementById('copilotChart').getContext('2d');
            copilotChart = new Chart(copilotCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Remaining'],
                    datasets: [{
                        data: [0, 1500],
                        backgroundColor: ['#667eea', '#e5e7eb'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true, position: 'bottom' }
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
                        backgroundColor: ['#764ba2', '#e5e7eb'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true, position: 'bottom' }
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
                        backgroundColor: ['#10b981', '#3b82f6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 100 }
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

    def __init__(self, tracking_file: str = ".ai_usage_tracking.json"):
        self.tracking_file = Path(tracking_file)
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load tracking data from JSON file."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._init_data()
        return self._init_data()

    def _init_data(self) -> Dict:
        """Initialize empty tracking data."""
        return {
            "copilot": {"daily": [], "monthly": []},
            "gemini": {"daily": []},
        }

    def get_copilot_usage(self) -> Dict:
        """Get Copilot usage statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%Y-%m")

        daily_count = sum(1 for entry in self.data.get("copilot", {}).get("daily", []) if entry["date"] == today)
        monthly_count = sum(
            1 for entry in self.data.get("copilot", {}).get("monthly", []) if entry["month"] == current_month
        )

        monthly_limit = 1500
        return {
            "daily": daily_count,
            "monthly": monthly_count,
            "monthly_limit": monthly_limit,
            "remaining": max(0, monthly_limit - monthly_count),
            "percentage_used": (monthly_count / monthly_limit * 100) if monthly_limit > 0 else 0,
        }

    def get_gemini_usage(self) -> Dict:
        """Get Gemini API usage statistics."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_count = sum(1 for entry in self.data.get("gemini", {}).get("daily", []) if entry["date"] == today)

        daily_limit = 20
        return {
            "daily": daily_count,
            "daily_limit": daily_limit,
            "remaining": max(0, daily_limit - daily_count),
            "percentage_used": (daily_count / daily_limit * 100) if daily_limit > 0 else 0,
        }

    def check_ollama_status(self) -> Optional[Dict]:
        """Check Ollama server status and running models."""
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

            return {"status": "not running", "models": [], "model_count": 0}

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def check_gpu_usage(self) -> Optional[Dict]:
        """Check GPU utilization and memory usage."""
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

        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        return None

    def get_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current usage."""
        recommendations = []

        copilot = self.get_copilot_usage()
        if copilot["percentage_used"] > 80:
            recommendations.append(
                f"⚠️ Copilot usage at {copilot['percentage_used']:.0f}% "
                f"({copilot['remaining']} requests remaining) - Consider using Gemini or Local LLM"
            )

        gemini = self.get_gemini_usage()
        if gemini["percentage_used"] > 80:
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
                    f"⚠️ VRAM usage high ({vram_usage:.0f}%) - " "Consider using smaller model or reducing batch size"
                )

        ollama = self.check_ollama_status()
        if ollama and ollama["status"] == "running" and ollama["model_count"] == 0:
            recommendations.append("💡 Ollama is running but no models loaded - Ready for unlimited local inference")

        return recommendations


monitor = AIResourceMonitor()


@app.route("/")
def dashboard():
    """Serve the dashboard HTML."""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/metrics")
def get_metrics():
    """API endpoint for current metrics."""
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
    app.run(host="0.0.0.0", port=9000, debug=False)
