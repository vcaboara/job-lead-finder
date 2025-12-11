#!/usr/bin/env python3
"""Email webhook integration for inbound email processing.

This module handles incoming emails via SendGrid Inbound Parse webhook,
manages user forwarding addresses, and stores emails for processing.
"""
import hashlib
import json
import logging
import os
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Security constants
MAX_EMAIL_LENGTH = 1000000  # 1MB max email size
MAX_SUBJECT_LENGTH = 998  # RFC 2822 limit
MAX_EMAILS_PER_USER = 1000  # Max emails stored per user
EMAIL_TTL_DAYS = 30  # Auto-delete emails older than 30 days
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
RATE_LIMIT_MAX_EMAILS = 100  # Max emails per user per hour
EMAIL_CLEANUP_BUFFER = 100  # Keep this many emails under quota during cleanup


@dataclass
class UserEmailConfig:
    """Configuration for user's email forwarding."""

    user_id: str
    forwarding_address: str  # user-{uuid}@domain.com
    created_at: datetime
    email_count: int = 0
    last_email_at: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.last_email_at:
            data["last_email_at"] = self.last_email_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "UserEmailConfig":
        """Create from dictionary."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("last_email_at"):
            data["last_email_at"] = datetime.fromisoformat(data["last_email_at"])
        return cls(**data)


@dataclass
class InboundEmail:
    """Inbound email data from webhook."""

    to_address: str
    from_address: str
    subject: str
    body_text: str
    body_html: Optional[str]
    received_at: datetime
    raw_email: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    def __post_init__(self):
        """Validate email data after initialization."""
        # Validate email addresses
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(self.to_address):
            raise ValueError(f"Invalid to_address: {self.to_address}")
        if not email_pattern.match(self.from_address):
            raise ValueError(f"Invalid from_address: {self.from_address}")

        # Validate subject length
        if len(self.subject) > MAX_SUBJECT_LENGTH:
            raise ValueError(f"Subject too long: {len(self.subject)} > {MAX_SUBJECT_LENGTH}")

        # Validate body sizes
        total_size = len(self.body_text) + (len(self.body_html) if self.body_html else 0)
        if total_size > MAX_EMAIL_LENGTH:
            raise ValueError(f"Email too large: {total_size} > {MAX_EMAIL_LENGTH}")

        # Validate date is reasonable (not too far in past/future)
        now = datetime.now()
        if self.received_at > now + timedelta(days=1):
            raise ValueError("Email date is in the future")
        if self.received_at < now - timedelta(days=365):
            raise ValueError("Email date is too old")

        # Sanitize HTML content to prevent XSS
        if self.body_html:
            self.body_html = self._sanitize_html(self.body_html)

    def _sanitize_html(self, html: str) -> str:
        """Sanitize HTML content to prevent XSS attacks.

        Args:
            html: Raw HTML content

        Returns:
            Sanitized HTML content
        """
        # Remove script tags and event handlers
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'on\w+\s*=\s*["\'].*?["\']', "", html, flags=re.IGNORECASE)
        html = re.sub(r"javascript:", "", html, flags=re.IGNORECASE)
        return html

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        data = asdict(self)
        data["received_at"] = self.received_at.isoformat()
        return data


class EmailWebhookManager:
    """Manages email webhook configuration and processing."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize webhook manager.

        Args:
            data_dir: Directory for storing email configs and data
        """
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(exist_ok=True)

        self.config_file = self.data_dir / "email_configs.json"
        self.inbox_dir = self.data_dir / "inbox"
        self.inbox_dir.mkdir(exist_ok=True)

        self.domain = os.getenv("SENDGRID_DOMAIN", "jobforge.local")
        self._configs: Dict[str, UserEmailConfig] = {}
        self._rate_limits: Dict[str, List[datetime]] = {}  # Track email timestamps per user
        self._load_configs()

    def _load_configs(self):
        """Load email configurations from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self._configs = {addr: UserEmailConfig.from_dict(cfg) for addr, cfg in data.items()}
                logger.info("Loaded %d email configs", len(self._configs))
            except json.JSONDecodeError as e:
                logger.error("Corrupt config file, starting fresh: %s", e)
                self._configs = {}
                # Save empty config to recover
                self._save_configs()
            except Exception as e:
                logger.error("Failed to load email configs: %s", e)
                raise RuntimeError(f"Cannot load email configs: {e}") from e

    def _save_configs(self):
        """Save email configurations to disk."""
        try:
            data = {addr: cfg.to_dict() for addr, cfg in self._configs.items()}
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save email configs: %s", e)

    def generate_forwarding_address(self, user_id: str = "default") -> str:
        """Generate unique forwarding address for user.

        Args:
            user_id: User identifier

        Returns:
            Forwarding email address like user-abc123@domain.com
        """
        # Generate secure random identifier (4 bytes -> 8 hex chars)
        # This provides 32 bits of entropy (2^32 = ~4 billion combinations)
        max_attempts = 10
        for _ in range(max_attempts):
            random_bytes = secrets.token_bytes(6)
            random_id = "".join(f"{b:02x}" for b in random_bytes[:4])  # 4 bytes -> 8 hex chars
            forwarding_address = f"user-{random_id}@{self.domain}"

            # Check for collision
            if forwarding_address not in self._configs:
                break
        else:
            raise RuntimeError("Failed to generate unique forwarding address after multiple attempts")

        # Create config
        config = UserEmailConfig(
            user_id=user_id,
            forwarding_address=forwarding_address,
            created_at=datetime.now(),
        )

        self._configs[forwarding_address] = config
        self._save_configs()

        logger.info("Created forwarding address %s for user %s", forwarding_address, user_id)
        return forwarding_address

    def get_config(self, forwarding_address: str) -> Optional[UserEmailConfig]:
        """Get config for forwarding address.

        Args:
            forwarding_address: Email address to lookup

        Returns:
            Config if found, None otherwise
        """
        return self._configs.get(forwarding_address)

    def get_user_config(self, user_id: str) -> Optional[UserEmailConfig]:
        """Get config for user ID.

        Args:
            user_id: User identifier

        Returns:
            Config if found, None otherwise
        """
        for config in self._configs.values():
            if config.user_id == user_id:
                return config
        return None

    def validate_address(self, address: str) -> bool:
        """Check if forwarding address is valid.

        Args:
            address: Email address to validate

        Returns:
            True if address is configured and active
        """
        config = self.get_config(address)
        return config is not None and config.is_active

    def store_inbound_email(self, email: InboundEmail) -> str:
        """Store inbound email to disk.

        Args:
            email: Email data to store

        Returns:
            Email ID (filename)

        Raises:
            ValueError: If rate limit exceeded or validation fails
        """
        # Get config for rate limiting
        config = self.get_config(email.to_address)
        if not config:
            raise ValueError(f"No config found for address: {email.to_address}")

        # Check rate limit
        user_id = config.user_id
        if not self._check_rate_limit(user_id):
            raise ValueError(f"Rate limit exceeded for user {user_id}")

        # Check user email count limit
        user_emails = self.list_pending_emails(user_id)
        if len(user_emails) >= MAX_EMAILS_PER_USER:
            logger.warning("User %s has reached max emails, cleaning old ones", user_id)
            self._cleanup_old_emails(user_id)

        # Generate unique email ID from content hash
        content = f"{email.to_address}{email.from_address}{email.subject}{email.received_at}"
        email_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Save to inbox
        email_file = self.inbox_dir / f"{email_id}.json"
        with open(email_file, "w") as f:
            json.dump(email.to_dict(), f, indent=2)

        # Update config stats and rate limit tracking
        config.email_count += 1
        config.last_email_at = email.received_at
        self._save_configs()
        self._record_email_timestamp(user_id)

        logger.info("Stored email %s from %s", email_id, email.from_address)
        return email_id

    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit.

        Args:
            user_id: User identifier

        Returns:
            True if within rate limit, False otherwise
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)

        # Initialize if not exists
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []

        # Remove old timestamps
        self._rate_limits[user_id] = [ts for ts in self._rate_limits[user_id] if ts > cutoff]

        # Check if under limit
        return len(self._rate_limits[user_id]) < RATE_LIMIT_MAX_EMAILS

    def _record_email_timestamp(self, user_id: str):
        """Record timestamp for rate limiting.

        Args:
            user_id: User identifier
        """
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        self._rate_limits[user_id].append(datetime.now())

    def _cleanup_old_emails(self, user_id: str):
        """Delete old emails for user to stay under quota.

        Args:
            user_id: User identifier
        """
        emails = []
        for email_file in self.inbox_dir.glob("*.json"):
            try:
                with open(email_file, "r") as f:
                    data = json.load(f)
                    config = self.get_config(data["to_address"])
                    if config and config.user_id == user_id:
                        received_at = datetime.fromisoformat(data["received_at"])
                        emails.append((email_file, received_at))
            except Exception as e:
                logger.warning("Failed to read email %s: %s", email_file, e)

        # Sort by date and delete oldest
        emails.sort(key=lambda x: x[1])
        emails_to_delete = emails[: len(emails) - MAX_EMAILS_PER_USER + EMAIL_CLEANUP_BUFFER]

        for email_file, _ in emails_to_delete:
            try:
                email_file.unlink()
                logger.info("Deleted old email %s for user %s", email_file.stem, user_id)
            except Exception as e:
                logger.error("Failed to delete email %s: %s", email_file, e)

    def get_user_stats(self, user_id: str) -> Dict:
        """Get email statistics for user.

        Args:
            user_id: User identifier

        Returns:
            Statistics dict
        """
        config = self.get_user_config(user_id)
        if not config:
            return {
                "forwarding_address": None,
                "emails_processed": 0,
                "last_email_at": None,
            }

        return {
            "forwarding_address": config.forwarding_address,
            "emails_processed": config.email_count,
            "last_email_at": config.last_email_at.isoformat() if config.last_email_at else None,
            "is_active": config.is_active,
        }

    def disable_address(self, forwarding_address: str) -> bool:
        """Disable a forwarding address.

        Args:
            forwarding_address: Address to disable

        Returns:
            True if disabled, False if not found
        """
        config = self.get_config(forwarding_address)
        if config:
            config.is_active = False
            self._save_configs()
            logger.info("Disabled forwarding address %s", forwarding_address)
            return True
        return False

    def list_pending_emails(self, user_id: Optional[str] = None) -> List[str]:
        """List pending emails in inbox.

        Args:
            user_id: Optional user filter

        Returns:
            List of email IDs
        """
        emails = []
        for email_file in self.inbox_dir.glob("*.json"):
            if user_id:
                # Filter by user
                with open(email_file, "r") as f:
                    data = json.load(f)
                    config = self.get_config(data["to_address"])
                    if config and config.user_id == user_id:
                        emails.append(email_file.stem)
            else:
                emails.append(email_file.stem)
        return emails

    def get_email(self, email_id: str) -> Optional[InboundEmail]:
        """Retrieve stored email.

        Args:
            email_id: Email ID to retrieve

        Returns:
            Email data if found

        Raises:
            ValueError: If email_id is invalid (security check)
        """
        # Validate email_id to prevent path traversal
        if not email_id or not email_id.isalnum() or len(email_id) != 16:
            raise ValueError(f"Invalid email_id format: {email_id}")

        email_file = self.inbox_dir / f"{email_id}.json"

        # Additional security: ensure resolved path is within inbox_dir
        try:
            resolved_path = email_file.resolve()
            inbox_resolved = self.inbox_dir.resolve()
            if not str(resolved_path).startswith(str(inbox_resolved)):
                raise ValueError(f"Path traversal attempt detected: {email_id}")
        except Exception as e:
            logger.error("Path validation failed for email_id %s: %s", email_id, e)
            raise ValueError(f"Invalid email_id: {email_id}") from e

        if not email_file.exists():
            return None

        try:
            with open(email_file, "r") as f:
                data = json.load(f)
                data["received_at"] = datetime.fromisoformat(data["received_at"])
                return InboundEmail(**data)
        except Exception as e:
            logger.error("Failed to load email %s: %s", email_id, e)
            return None

    def cleanup_expired_emails(self):
        """Delete emails older than TTL_DAYS."""
        cutoff = datetime.now() - timedelta(days=EMAIL_TTL_DAYS)
        deleted_count = 0

        for email_file in self.inbox_dir.glob("*.json"):
            try:
                with open(email_file, "r") as f:
                    data = json.load(f)
                    received_at = datetime.fromisoformat(data["received_at"])
                    if received_at < cutoff:
                        email_file.unlink()
                        deleted_count += 1
            except Exception as e:
                logger.warning("Failed to process email %s for cleanup: %s", email_file, e)

        if deleted_count > 0:
            logger.info("Cleaned up %d expired emails", deleted_count)
