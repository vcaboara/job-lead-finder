"""Tests for email webhook integration."""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.email_webhook import (
    EmailWebhookManager,
    InboundEmail,
    UserEmailConfig,
)


class TestUserEmailConfig:
    """Test UserEmailConfig dataclass."""

    def test_create_config(self):
        """Test creating user email config."""
        config = UserEmailConfig(
            user_id="test123",
            forwarding_address="user-abc123@jobforge.com",
            created_at=datetime.now(),
        )

        assert config.user_id == "test123"
        assert config.forwarding_address == "user-abc123@jobforge.com"
        assert config.email_count == 0
        assert config.is_active is True

    def test_config_to_dict(self):
        """Test serialization to dict."""
        now = datetime.now()
        config = UserEmailConfig(
            user_id="test123",
            forwarding_address="user-abc123@jobforge.com",
            created_at=now,
            email_count=5,
        )

        data = config.to_dict()
        assert data["user_id"] == "test123"
        assert data["email_count"] == 5
        assert data["created_at"] == now.isoformat()

    def test_config_from_dict(self):
        """Test deserialization from dict."""
        now = datetime.now()
        data = {
            "user_id": "test123",
            "forwarding_address": "user-abc123@jobforge.com",
            "created_at": now.isoformat(),
            "email_count": 5,
            "is_active": True,
        }

        config = UserEmailConfig.from_dict(data)
        assert config.user_id == "test123"
        assert config.email_count == 5
        assert config.created_at == now


class TestInboundEmail:
    """Test InboundEmail dataclass."""

    def test_create_email(self):
        """Test creating inbound email."""
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="jobs@linkedin.com",
            subject="New jobs for you",
            body_text="Check out these listings...",
            body_html="<html>...</html>",
            received_at=datetime.now(),
        )

        assert email.to_address == "user-abc123@jobforge.com"
        assert email.from_address == "jobs@linkedin.com"
        assert email.subject == "New jobs for you"

    def test_email_to_dict(self):
        """Test serialization."""
        now = datetime.now()
        email = InboundEmail(
            to_address="user-abc123@jobforge.com",
            from_address="jobs@linkedin.com",
            subject="Test",
            body_text="Body",
            body_html=None,
            received_at=now,
        )

        data = email.to_dict()
        assert data["received_at"] == now.isoformat()


class TestEmailWebhookManager:
    """Test EmailWebhookManager class."""

    def test_init_creates_directories(self, tmp_path):
        """Test manager creates data directories."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        assert manager.data_dir.exists()
        assert manager.inbox_dir.exists()

    def test_generate_forwarding_address(self, tmp_path):
        """Test generating unique forwarding address."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        address = manager.generate_forwarding_address("user123")

        assert address.startswith("user-")
        assert "@" in address
        assert manager.domain in address

    def test_generate_unique_addresses(self, tmp_path):
        """Test multiple addresses are unique."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        addr1 = manager.generate_forwarding_address("user1")
        addr2 = manager.generate_forwarding_address("user2")

        assert addr1 != addr2

    def test_get_config(self, tmp_path):
        """Test retrieving config by address."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        config = manager.get_config(address)

        assert config is not None
        assert config.user_id == "user123"
        assert config.forwarding_address == address

    def test_get_user_config(self, tmp_path):
        """Test retrieving config by user ID."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        config = manager.get_user_config("user123")

        assert config is not None
        assert config.forwarding_address == address

    def test_validate_address(self, tmp_path):
        """Test address validation."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        assert manager.validate_address(address) is True
        assert manager.validate_address("invalid@jobforge.com") is False

    def test_store_inbound_email(self, tmp_path):
        """Test storing inbound email."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        email = InboundEmail(
            to_address=address,
            from_address="test@example.com",
            subject="Test",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )

        email_id = manager.store_inbound_email(email)

        assert email_id
        assert (manager.inbox_dir / f"{email_id}.json").exists()

        # Check config updated
        config = manager.get_config(address)
        assert config.email_count == 1
        assert config.last_email_at is not None

    def test_get_user_stats(self, tmp_path):
        """Test getting user statistics."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        stats = manager.get_user_stats("user123")

        assert stats["forwarding_address"] == address
        assert stats["emails_processed"] == 0
        assert stats["is_active"] is True

    def test_disable_address(self, tmp_path):
        """Test disabling forwarding address."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        assert manager.disable_address(address) is True
        assert manager.validate_address(address) is False

    def test_list_pending_emails(self, tmp_path):
        """Test listing pending emails."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        email = InboundEmail(
            to_address=address,
            from_address="test@example.com",
            subject="Test",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )

        email_id = manager.store_inbound_email(email)
        pending = manager.list_pending_emails("user123")

        assert email_id in pending

    def test_get_email(self, tmp_path):
        """Test retrieving stored email."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        address = manager.generate_forwarding_address("user123")

        original = InboundEmail(
            to_address=address,
            from_address="test@example.com",
            subject="Test Subject",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )

        email_id = manager.store_inbound_email(original)
        retrieved = manager.get_email(email_id)

        assert retrieved is not None
        assert retrieved.subject == "Test Subject"
        assert retrieved.from_address == "test@example.com"

    def test_persistence(self, tmp_path):
        """Test configs persist across manager instances."""
        manager1 = EmailWebhookManager(data_dir=tmp_path)
        address = manager1.generate_forwarding_address("user123")

        # Create new manager instance
        manager2 = EmailWebhookManager(data_dir=tmp_path)
        config = manager2.get_config(address)

        assert config is not None
        assert config.user_id == "user123"
