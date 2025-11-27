import json
import re
import threading
from pathlib import Path
from typing import Any, Dict

_CONFIG_PATH = Path("config.json")
_LOCK = threading.Lock()
_DEFAULT: Dict[str, Any] = {"system_instructions": "", "blocked_entities": [], "region": ""}


def _fresh_default() -> Dict[str, Any]:
    """Return a fresh default config dict (avoids shared mutable lists)."""
    return {"system_instructions": "", "blocked_entities": [], "region": ""}


def load_config() -> Dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return _fresh_default()
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        # merge defaults
        out = _fresh_default()
        if isinstance(data, dict):
            out.update({k: v for k, v in data.items() if k in _DEFAULT})
        return out
    except Exception:
        return _fresh_default()


def save_config(cfg: Dict[str, Any]) -> None:
    with _LOCK:
        tmp = _fresh_default()
        tmp.update({k: v for k, v in cfg.items() if k in _DEFAULT})
        with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(tmp, fh, indent=2)


INJECTION_PATTERNS = [
    r"(?i)\bignore\b",
    r"(?i)\bforget\b",
    r"(?i)\boverride\b",
    r"(?i)\bsystem\b.*\binstruction",
    r"(?i)\bjailbreak\b",
    r"(?i)\bexfiltrate\b",
    r"(?i)\bleak\b",
    r"(?i)\bpassword\b",
    r"(?i)\bapi[_-]?key\b",
    r"(?i)\btoken\b",
]


def scan_instructions(text: str) -> list[str]:
    findings: list[str] = []
    for pat in INJECTION_PATTERNS:
        if re.search(pat, text):
            findings.append(pat)
    if len(text) < 10:
        findings.append("too_short")
    return findings


def scan_entity(entity: str) -> list[str]:
    """Scan a blocked entity (site/employer) for injection attempts."""
    findings: list[str] = []
    # Check for injection patterns
    for pat in INJECTION_PATTERNS:
        if re.search(pat, entity):
            findings.append(pat)
    # Check for suspicious patterns
    if len(entity.strip()) < 2:
        findings.append("too_short")
    if any(char in entity for char in ["<", ">", "{", "}", ";"]):
        findings.append("suspicious_chars")
    return findings


def validate_url(url: str) -> bool:
    """Basic URL validation for blocked sites."""
    if not url or len(url) < 4:
        return False
    # Basic domain pattern check
    pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-_.]*\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, url.strip()))
