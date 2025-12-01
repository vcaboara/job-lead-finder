"""Link validation utilities for job leads.

This module provides functions to validate URLs returned by Gemini job search,
following redirects and identifying broken links (404s, etc.).
"""

import time
from typing import Any, Dict, Optional

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def validate_link(url: str, timeout: int = 5, verbose: bool = False) -> Dict[str, Any]:
    """Validate a single URL by making a HEAD/GET request and following redirects.

    Args:
        url: The URL to validate.
        timeout: Request timeout in seconds.
        verbose: Print diagnostic info.

    Returns:
        A dict with keys:
        - 'valid': bool indicating if the link is valid (status 2xx/3xx)
        - 'status_code': HTTP status code (or None if request failed)
        - 'final_url': Final URL after following redirects (or None if failed)
        - 'error': Error message if validation failed (or None)
        - 'warning': Optional human-readable note (e.g., blocked, requires auth)
    """
    if not url or not isinstance(url, str):
        return {
            "valid": False,
            "status_code": None,
            "final_url": None,
            "error": "Invalid URL format",
            "warning": "invalid url",
        }

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    if not REQUESTS_AVAILABLE:
        return {
            "valid": None,  # Unknown; requests library not available
            "status_code": None,
            "final_url": url,
            "error": "requests library not installed; cannot validate",
            "warning": "validator unavailable",
        }

    try:
        # Use HEAD request first (faster), fall back to GET if HEAD fails
        try:
            resp = requests.head(url, timeout=timeout, allow_redirects=True, verify=True)
            status_code = resp.status_code
            final_url = resp.url
        except requests.exceptions.RequestException:
            # Fall back to GET request
            resp = requests.get(url, timeout=timeout, allow_redirects=True, verify=True, stream=True)
            status_code = resp.status_code
            final_url = resp.url

        # Detect "soft 404s" - sites that return 200 but redirect to error pages
        final_url_lower = str(final_url).lower()
        is_soft_404 = any(
            pattern in final_url_lower
            for pattern in [
                "/404",
                "/error",
                "/not-found",
                "/notfound",
                "/page-not-found",
                "/errorpages/404",
                "/errors/404",
            ]
        )

        # Consider 2xx/3xx as valid; treat 403 as soft-valid (site may block automation but link exists)
        # But mark as invalid if it's a soft 404
        valid = (200 <= status_code < 400 or status_code == 403) and not is_soft_404

        # Map status codes to soft warnings (non-breaking)
        warning: Optional[str] = None
        if is_soft_404:
            warning = "soft 404 (redirected to error page)"
        elif status_code == 403:
            warning = "access forbidden (treated as present)"
        elif not valid:
            if status_code == 401:
                warning = "requires authentication"
            elif status_code == 404:
                warning = "not found (404)"
            elif status_code and 500 <= status_code < 600:
                warning = "server error"

        if verbose:
            print(f"link_validator: {url} -> {status_code} (valid={valid}, soft_404={is_soft_404})")

        return {
            "valid": valid,
            "status_code": status_code,
            "final_url": str(final_url),
            "error": "soft 404 detected" if is_soft_404 else None,
            "warning": warning,
        }
    except Exception as e:
        error_msg = str(e)
        if verbose:
            print(f"link_validator: {url} -> ERROR: {error_msg}")
        return {
            "valid": False,
            "status_code": None,
            "final_url": url,
            "error": error_msg,
            "warning": "request error/timeout",
        }


def validate_leads(
    leads: list[Dict[str, Any]],
    timeout: int = 5,
    verbose: bool = False,
    max_workers: int = 3,
) -> list[Dict[str, Any]]:
    """Validate all links in a list of job leads.

    Each lead dict is enriched with:
    - 'link_valid': bool indicating if the link is valid
    - 'link_status_code': HTTP status code
    - 'link_final_url': Final URL after redirects
    - 'link_error': Error message if validation failed

    Args:
        leads: List of job lead dicts with 'link' key.
        timeout: Request timeout per link in seconds.
        verbose: Print diagnostic info.
        max_workers: Number of concurrent requests (if using threading in future).

    Returns:
        List of leads with validation info added.
    """
    if not leads:
        return leads

    if verbose:
        print(f"link_validator: validating {len(leads)} leads")

    validated = []
    for i, lead in enumerate(leads):
        url = lead.get("link", "")
        if verbose:
            print(f"link_validator: [{i+1}/{len(leads)}] validating {url}")

        validation = validate_link(url, timeout=timeout, verbose=verbose)

        # Enrich lead with validation data
        enriched = dict(lead)
        enriched["link_valid"] = validation["valid"]
        enriched["link_status_code"] = validation["status_code"]
        enriched["link_final_url"] = validation["final_url"]
        enriched["link_error"] = validation["error"]
        enriched["link_warning"] = validation.get("warning")

        validated.append(enriched)
        # Small delay to avoid overwhelming servers
        time.sleep(0.2)

    if verbose:
        valid_count = sum(1 for lead in validated if lead.get("link_valid"))
        print(f"link_validator: {valid_count}/{len(validated)} links valid")

    return validated


def filter_valid_links(leads: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Filter job leads to keep only those with valid links.

    Args:
        leads: List of validated leads (from validate_leads).

    Returns:
        List of leads where link_valid is True.
    """
    return [lead for lead in leads if lead.get("link_valid", False)]
