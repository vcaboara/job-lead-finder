#!/usr/bin/env python3
"""Email webhook integration for inbound email processing.

This module handles incoming emails via SendGrid Inbound Parse webhook,
manages user forwarding addresses, and stores emails for processing.
"""
import hashlib
import json
import logging
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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
        self._load_configs()

    def _load_configs(self):
        """Load email configurations from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self._configs = {
                        addr: UserEmailConfig.from_dict(cfg)
                        for addr, cfg in data.items()
                    }
                logger.info("Loaded %d email configs", len(self._configs))
            except Exception as e:
                logger.error("Failed to load email configs: %s", e)

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
        # Generate short random identifier
        random_id = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:6]
        forwarding_address = f"user-{random_id}@{self.domain}"

        # Check for collision (extremely unlikely)
        while forwarding_address in self._configs:
            random_id = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:6]
            forwarding_address = f"user-{random_id}@{self.domain}"

        # Create config
        config = UserEmailConfig(
            user_id=user_id,
            forwarding_address=forwarding_address,
            created_at=datetime.now(),
        )

        self._configs[forwarding_address] = config
        self._save_configs()

        logger.info(
            "Created forwarding address %s for user %s", forwarding_address, user_id
        )
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
        """
        # Generate unique email ID from content hash
        content = f"{email.to_address}{email.from_address}{email.subject}{email.received_at}"
        email_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Save to inbox
        email_file = self.inbox_dir / f"{email_id}.json"
        with open(email_file, "w") as f:
            json.dump(email.to_dict(), f, indent=2)

        # Update config stats
        config = self.get_config(email.to_address)
        if config:
            config.email_count += 1
            config.last_email_at = email.received_at
            self._save_configs()

        logger.info("Stored email %s from %s", email_id, email.from_address)
        return email_id

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
            "last_email_at": config.last_email_at.isoformat()
            if config.last_email_at
            else None,
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
        """
        email_file = self.inbox_dir / f"{email_id}.json"
        if not email_file.exists():
            return None

        with open(email_file, "r") as f:
            data = json.load(f)
            data["received_at"] = datetime.fromisoformat(data["received_at"])
            return InboundEmail(**data)
