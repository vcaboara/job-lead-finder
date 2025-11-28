"""FastAPI UI server for job lead finder.

Reconstructed after refactor: serves HTML template, search API,
configuration endpoints, and leads retrieval.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .config_store import load_config, save_config, scan_entity, scan_instructions, validate_url
from .job_finder import generate_job_leads, save_to_file
from .link_validator import validate_link

app = FastAPI(title="Job Lead Finder", version="0.1.1")

LEADS_FILE = Path("leads.json")
RESUME_FILE = Path("resume.txt")
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# Progress tracking for search operations
search_progress: Dict[str, dict] = {}


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


class BlockedEntity(BaseModel):
    type: str
    value: str


class ConfigResponse(BaseModel):
    system_instructions: str
    blocked_entities: list[BlockedEntity]
    region: str


class BlockedEntityRequest(BaseModel):
    entity: str
    entity_type: str  # 'site' or 'employer'


class ValidateLinkRequest(BaseModel):
    url: str


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
    # Allow search without an API key; provider will fallback internally
    # Load resume from file if not provided in request
    resume_text = req.resume
    if not resume_text and RESUME_FILE.exists():
        resume_text = RESUME_FILE.read_text(encoding="utf-8")

    # Auto-evaluate if resume is available
    should_evaluate = req.evaluate or bool(resume_text)

    # Create unique search ID for progress tracking
    search_id = f"search_{int(time.time() * 1000)}"
    search_progress[search_id] = {
        "status": "starting",
        "message": f"Requesting {req.count} job listings...",
        "attempt": 0,
        "valid_count": 0,
        "timestamp": time.time(),
    }

    try:
        # Request 2x more jobs to account for filtering (oversample strategy)
        # This helps ensure we get the requested count after validation
        oversample_multiplier = 2
        initial_request_count = req.count * oversample_multiplier
        max_retries = 1  # Reduced from 2 for faster response
        all_valid_leads = []
        seen_links = set()  # Track unique job links to avoid duplicates

        for attempt in range(max_retries + 1):
            # Update progress
            search_progress[search_id].update(
                {
                    "status": "fetching",
                    "attempt": attempt + 1,
                    "message": f"Attempt {attempt + 1}/{max_retries + 1}: Fetching jobs from Gemini...",
                }
            )

            # Calculate how many more we need
            needed = req.count - len(all_valid_leads)
            if needed <= 0:
                break

            # Request extra to account for filtering
            request_count = needed * oversample_multiplier if attempt > 0 else initial_request_count

            search_progress[search_id]["message"] = f"Attempt {attempt + 1}: Requesting {request_count} jobs..."

            raw_leads = generate_job_leads(
                query=req.query,
                resume_text=resume_text or "No resume provided.",
                count=request_count,
                model=req.model,
                evaluate=should_evaluate,
                verbose=False,
            )

            # Update progress
            search_progress[search_id].update(
                {"status": "filtering", "message": f"Validating and filtering {len(raw_leads)} results..."}
            )

            # Process and filter leads
            valid_leads = _process_and_filter_leads(raw_leads)

            # Deduplicate by link
            for lead in valid_leads:
                link = lead.get("link", "")
                if link and link not in seen_links:
                    seen_links.add(link)
                    all_valid_leads.append(lead)

            search_progress[search_id].update(
                {"valid_count": len(all_valid_leads), "message": f"Found {len(all_valid_leads)} valid jobs so far..."}
            )

            # Stop if we have enough or got no new results
            if len(all_valid_leads) >= req.count or len(valid_leads) == 0:
                break

        # Take only the requested count
        final_leads = all_valid_leads[: req.count]

        search_progress[search_id].update(
            {
                "status": "complete",
                "message": f"Search complete: {len(final_leads)} jobs found",
                "valid_count": len(final_leads),
            }
        )

        save_to_file(final_leads, str(LEADS_FILE))
        return JSONResponse(
            {
                "status": "success",
                "query": req.query,
                "count": len(final_leads),
                "leads": final_leads,
                "filtered_count": len(all_valid_leads) - len(final_leads),
                "total_fetched": len(all_valid_leads),
                "search_id": search_id,
            }
        )
    except Exception as e:
        search_progress[search_id].update({"status": "error", "message": f"Error: {str(e)}"})
        raise HTTPException(status_code=500, detail=str(e))


def _process_and_filter_leads(raw_leads: list) -> list:
    """Process raw leads and filter out blocked/invalid ones."""
    # Load config for blocked entities
    cfg = load_config()
    blocked = cfg.get("blocked_entities", [])
    blocked_sites = {e.get("value", "").lower() for e in blocked if e.get("type") == "site"}
    blocked_employers = {e.get("value", "").lower() for e in blocked if e.get("type") == "employer"}

    def is_blocked(lead_link: str, company: str) -> bool:
        from urllib.parse import urlparse

        # Company check
        if company and company.lower() in blocked_employers:
            return True
        # Site/domain check
        if not lead_link:
            return False
        try:
            parsed = urlparse(lead_link)
            host = parsed.netloc.lower()
            host = host[4:] if host.startswith("www.") else host
            # Direct match or suffix match (e.g., sub.domain.com endswith domain.com)
            for site in blocked_sites:
                if host == site or host.endswith("." + site):
                    return True
        except Exception:
            return False
        return False

    # Parallelize link validation for speed
    import concurrent.futures
    from urllib.parse import urlparse

    # Pre-filter blocked leads
    unblocked_leads = [lead for lead in raw_leads if not is_blocked(lead.get("link", ""), lead.get("company", ""))]

    # Validate all links in parallel (5-10x faster than sequential)
    links_to_validate = [lead.get("link", "") for lead in unblocked_leads]
    validated_results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_link = {executor.submit(validate_link, link, False): link for link in links_to_validate if link}
        for future in concurrent.futures.as_completed(future_to_link):
            link = future_to_link[future]
            try:
                validated_results[link] = future.result()
            except Exception:
                validated_results[link] = {"valid": False, "status_code": None, "error": "validation_failed"}

    processed_leads = []
    for lead in unblocked_leads:
        link = lead.get("link", "")
        link_info = validated_results.get(link) if link else {"valid": False, "status_code": None, "error": "no_link"}
        # Exclude bad links: 403, 404, localhost/127.0.0.1, search-result pages, and generic career pages
        parsed = urlparse(link) if link else None
        host = parsed.netloc.lower() if parsed else ""
        host = host[4:] if host.startswith("www.") else host
        is_local = host in {"localhost", "127.0.0.1"}
        path = parsed.path.lower() if parsed else ""
        query = parsed.query.lower() if parsed else ""

        # Detect generic career/jobs pages (not specific job postings)
        generic_patterns = [
            "/careers",
            "/jobs",
            "/career",
            "/job",
            "/employment",
            "/opportunities",
            "/join-us",
            "/work-with-us",
        ]
        is_generic_page = any(
            path.rstrip("/") == pattern or path.rstrip("/") + "/" == pattern + "/" for pattern in generic_patterns
        )

        looks_like_search = ("/search" in path) or ("jobs/search" in path) or ("q=" in query)
        status = link_info.get("status_code")
        is_excluded_status = status in {403, 404}

        if (not link_info.get("valid")) or is_excluded_status or is_local or looks_like_search or is_generic_page:
            # Skip adding this lead due to unacceptable link
            continue
        lead["link_status_code"] = status
        lead["link_valid"] = True
        lead["link_warning"] = link_info.get("warning")
        lead["link_error"] = link_info.get("error")
        processed_leads.append(lead)

    return processed_leads


@app.get("/api/search/progress/{search_id}")
def get_search_progress(search_id: str):
    """Get the current progress of a search operation."""
    if search_id not in search_progress:
        raise HTTPException(status_code=404, detail="Search ID not found")
    return JSONResponse(search_progress[search_id])


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


@app.post("/api/config/block-entity", response_model=ConfigResponse)
def add_blocked_entity(req: BlockedEntityRequest):
    """Add a site or employer to the block list."""
    entity = req.entity.strip()
    entity_type = req.entity_type.lower()

    if entity_type not in ("site", "employer"):
        raise HTTPException(status_code=400, detail="entity_type must be 'site' or 'employer'")

    # Validate site domain format
    if entity_type == "site" and not validate_url(entity):
        raise HTTPException(status_code=400, detail="Invalid site domain format")

    # Scan for injection
    findings = scan_entity(entity)
    if findings:
        raise HTTPException(status_code=400, detail={"error": "Rejected by scanner", "findings": findings})

    cfg = load_config()
    blocked = cfg.get("blocked_entities", [])

    # Store as dict with type
    entry = {"type": entity_type, "value": entity}
    if entry not in blocked:
        blocked.append(entry)
        cfg["blocked_entities"] = blocked
        save_config(cfg)

    return ConfigResponse(
        system_instructions=cfg.get("system_instructions", ""),
        blocked_entities=cfg.get("blocked_entities", []),
        region=cfg.get("region", ""),
    )


@app.delete("/api/config/block-entity/{entity_type}/{entity}", response_model=ConfigResponse)
def remove_blocked_entity(entity_type: str, entity: str):
    """Remove a site or employer from the block list."""
    entity = entity.strip()
    entity_type = entity_type.lower()

    cfg = load_config()
    blocked = cfg.get("blocked_entities", [])
    entry = {"type": entity_type, "value": entity}

    if entry in blocked:
        blocked.remove(entry)
        cfg["blocked_entities"] = blocked
        save_config(cfg)

    return ConfigResponse(
        system_instructions=cfg.get("system_instructions", ""),
        blocked_entities=cfg.get("blocked_entities", []),
        region=cfg.get("region", ""),
    )


@app.post("/api/validate-link")
def check_link(req: ValidateLinkRequest):
    """Validate a link is accessible."""
    result = validate_link(req.url, verbose=False)
    return JSONResponse(
        {
            "url": result.get("url", req.url),
            "valid": result.get("valid", False),
            "status_code": result.get("status_code"),
            "error": result.get("error"),
        }
    )


@app.post("/api/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload resume file for job matching."""
    # Validate file size (max 1MB)
    content = await file.read()
    if len(content) > 1_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 1MB)")

    # Validate file type - only text files for now
    if not file.filename.endswith((".txt", ".md")):
        raise HTTPException(status_code=400, detail="Only .txt and .md files supported currently")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")

    # Scan for injection patterns
    findings = scan_instructions(text[:5000])  # Scan first 5000 chars
    if findings:
        raise HTTPException(status_code=400, detail={"error": "Rejected by scanner", "findings": findings})

    # Save to resume.txt
    RESUME_FILE.write_text(text, encoding="utf-8")

    return JSONResponse({"message": "Resume uploaded successfully", "resume": text, "filename": file.filename})


@app.get("/api/resume")
def get_resume():
    """Get current resume text."""
    if not RESUME_FILE.exists():
        return JSONResponse({"resume": None})
    try:
        text = RESUME_FILE.read_text(encoding="utf-8")
        return JSONResponse({"resume": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading resume: {e}")


@app.delete("/api/resume")
def delete_resume():
    """Delete resume file."""
    if not RESUME_FILE.exists():
        raise HTTPException(status_code=404, detail="Resume not found")
    RESUME_FILE.unlink()
    return JSONResponse({"message": "Resume deleted"})
