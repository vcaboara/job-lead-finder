"""FastAPI UI server for job lead finder.

Reconstructed after refactor: serves HTML template, search API,
configuration endpoints, and leads retrieval.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .config_store import load_config, save_config, scan_instructions
from .job_finder import generate_job_leads, save_to_file

app = FastAPI(title="Job Lead Finder", version="0.1.1")

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


class SystemInstructionsRequest(BaseModel):
    instructions: str


class ConfigResponse(BaseModel):
    system_instructions: str
    blocked_entities: list[str]
    region: str


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "templates" / "index.html"
    try:
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="UI template not found")


@app.get("/health", response_model=HealthResponse)
def health():
    api_key = os.getenv("GEMINI_API_KEY", "")
    return HealthResponse(status="healthy", api_key_configured=bool(api_key))


@app.get("/api/config", response_model=ConfigResponse)
def get_config():
    cfg = load_config()
    return ConfigResponse(
        system_instructions=cfg.get("system_instructions", ""),
        blocked_entities=cfg.get("blocked_entities", []),
        region=cfg.get("region", ""),
    )


@app.post("/api/config/system-instructions", response_model=ConfigResponse)
def update_system_instructions(req: SystemInstructionsRequest):
    findings = scan_instructions(req.instructions)
    if findings:
        raise HTTPException(status_code=400, detail={"error": "Rejected by scanner", "findings": findings})
    cfg = load_config()
    cfg["system_instructions"] = req.instructions
    save_config(cfg)
    return ConfigResponse(
        system_instructions=cfg.get("system_instructions", ""),
        blocked_entities=cfg.get("blocked_entities", []),
        region=cfg.get("region", ""),
    )


@app.post("/api/search")
def search(req: SearchRequest):
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
        save_to_file(leads, str(LEADS_FILE))
        return JSONResponse({"status": "success", "query": req.query, "count": len(leads), "leads": leads})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads")
def get_leads():
    if not LEADS_FILE.exists():
        return JSONResponse({"leads": []})
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as fh:
            leads = json.load(fh)
        return JSONResponse({"leads": leads})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading leads: {e}")
