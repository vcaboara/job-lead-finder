"""FastAPI UI server for job lead finder."""
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .job_finder import generate_job_leads, save_to_file
from .gemini_provider import GeminiProvider

app = FastAPI(title="Job Lead Finder", version="0.1.1")

# Leads file path
LEADS_FILE = Path("leads.json")


class SearchRequest(BaseModel):
    query: str
    resume: Optional[str] = None
    count: int = 5
    model: Optional[str] = None
    evaluate: bool = False


class HealthResponse(BaseModel):
    status: str
    api_key_configured: bool


@app.get("/health", response_model=HealthResponse)
def health():
    """Check API health and configuration."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    return HealthResponse(
        status="healthy",
        api_key_configured=bool(api_key),
    )


@app.post("/api/search")
def search(req: SearchRequest):
    """Search for jobs and optionally evaluate them."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        leads = generate_job_leads(
            query=req.query,
            resume_text=req.resume or "No resume provided.",
            count=req.count,
            model=req.model,
            evaluate=req.evaluate,
            verbose=False,
        )

        # Save to file
        save_to_file(leads, str(LEADS_FILE))

        return JSONResponse(
            {
                "status": "success",
                "query": req.query,
                "count": len(leads),
                "leads": leads,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads")
def get_leads():
    """Retrieve saved leads from leads.json."""
    if not LEADS_FILE.exists():
        return JSONResponse({"leads": []})

    try:
        with open(LEADS_FILE, "r") as f:
            leads = json.load(f)
        return JSONResponse({"leads": leads})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading leads: {str(e)}")


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the UI dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Job Lead Finder</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            header {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
            header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .content {
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .search-panel, .leads-panel {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            }
            .search-panel {
                height: fit-content;
            }
            .search-panel h2, .leads-panel h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            .form-group input,
            .form-group textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: inherit;
                font-size: 1em;
            }
            .form-group textarea {
                min-height: 80px;
                resize: vertical;
            }
            .form-group input:focus,
            .form-group textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .checkbox-group input[type="checkbox"] {
                width: auto;
                margin: 0;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 1em;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .leads-list {
                display: flex;
                flex-direction: column;
                gap: 15px;
                max-height: 800px;
                overflow-y: auto;
            }
            .lead-card {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                background: #f9f9f9;
                transition: all 0.2s;
            }
            .lead-card:hover {
                background: #f0f0f0;
                border-color: #667eea;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
            }
            .lead-card h3 {
                color: #333;
                margin-bottom: 8px;
                font-size: 1.1em;
            }
            .lead-card .company {
                color: #667eea;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .lead-card .location {
                color: #888;
                font-size: 0.9em;
                margin-bottom: 8px;
            }
            .lead-card .summary {
                color: #666;
                font-size: 0.95em;
                line-height: 1.4;
                margin-bottom: 10px;
            }
            .lead-card .score-section {
                display: flex;
                align-items: center;
                gap: 10px;
                margin: 10px 0;
                padding-top: 10px;
                border-top: 1px solid #e0e0e0;
            }
            .score-badge {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                font-weight: 600;
                font-size: 0.9em;
            }
            .score-badge.high {
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            }
            .score-badge.medium {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }
            .score-badge.low {
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            }
            .reasoning {
                font-size: 0.85em;
                color: #666;
                font-style: italic;
            }
            .lead-card a {
                display: inline-block;
                margin-top: 10px;
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }
            .lead-card a:hover {
                text-decoration: underline;
            }
            .status {
                text-align: center;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                display: none;
            }
            .status.show {
                display: block;
            }
            .status.loading {
                background: #e3f2fd;
                color: #1976d2;
            }
            .status.success {
                background: #e8f5e9;
                color: #388e3c;
            }
            .status.error {
                background: #ffebee;
                color: #d32f2f;
            }
            .empty-state {
                text-align: center;
                padding: 40px 20px;
                color: #999;
            }
            @media (max-width: 768px) {
                .content {
                    grid-template-columns: 1fr;
                }
                header h1 {
                    font-size: 1.8em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔍 Job Lead Finder</h1>
                <p>AI-powered job search with intelligent evaluation</p>
            </header>

            <div class="content">
                <div class="search-panel">
                    <h2>Search</h2>
                    <form id="searchForm">
                        <div class="form-group">
                            <label for="query">Query *</label>
                            <input type="text" id="query" name="query" placeholder="e.g., remote python developer" required>
                        </div>
                        <div class="form-group">
                            <label for="resume">Resume (optional)</label>
                            <textarea id="resume" name="resume" placeholder="Paste your resume or profile summary..."></textarea>
                        </div>
                        <div class="form-group">
                            <label for="count">Results Count</label>
                            <input type="number" id="count" name="count" value="5" min="1" max="20">
                        </div>
                        <div class="form-group checkbox-group">
                            <input type="checkbox" id="evaluate" name="evaluate">
                            <label for="evaluate" style="margin: 0;">Evaluate against resume</label>
                        </div>
                        <button type="submit">Search</button>
                    </form>
                </div>

                <div class="leads-panel">
                    <h2>Results</h2>
                    <div id="status" class="status"></div>
                    <div id="leadsList" class="leads-list">
                        <div class="empty-state">
                            <p>No leads yet. Search to get started!</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function loadLeads() {
                try {
                    const resp = await fetch('/api/leads');
                    const data = await resp.json();
                    displayLeads(data.leads);
                } catch (e) {
                    console.error('Error loading leads:', e);
                }
            }

            function displayLeads(leads) {
                const container = document.getElementById('leadsList');
                if (!leads || leads.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No leads yet. Search to get started!</p></div>';
                    return;
                }
                container.innerHTML = leads.map(lead => `
                    <div class="lead-card">
                        <h3>${lead.title}</h3>
                        <div class="company">${lead.company}</div>
                        <div class="location">📍 ${lead.location}</div>
                        <div class="summary">${lead.summary}</div>
                        ${lead.score !== undefined ? `
                            <div class="score-section">
                                <div class="score-badge ${lead.score >= 80 ? 'high' : lead.score >= 60 ? 'medium' : 'low'}">
                                    Score: ${lead.score}
                                </div>
                                ${lead.reasoning ? `<div class="reasoning">${lead.reasoning}</div>` : ''}
                            </div>
                        ` : ''}
                        <a href="${lead.link}" target="_blank">View on site →</a>
                    </div>
                `).join('');
            }

            function showStatus(message, type) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = `status show ${type}`;
                if (type !== 'loading') {
                    setTimeout(() => status.classList.remove('show'), 5000);
                }
            }

            document.getElementById('searchForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const query = document.getElementById('query').value;
                const resume = document.getElementById('resume').value;
                const count = parseInt(document.getElementById('count').value);
                const evaluate = document.getElementById('evaluate').checked;

                showStatus('Searching...', 'loading');

                try {
                    const resp = await fetch('/api/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, resume: resume || null, count, evaluate })
                    });
                    const data = await resp.json();
                    if (!resp.ok) throw new Error(data.detail || 'Search failed');
                    displayLeads(data.leads);
                    showStatus(`Found ${data.count} job${data.count !== 1 ? 's' : ''}!`, 'success');
                } catch (e) {
                    showStatus(`Error: ${e.message}`, 'error');
                    console.error(e);
                }
            });

            // Load initial leads on page load
            loadLeads();
        </script>
    </body>
    </html>
    """
