"""Tests for email webhook integration."""
from datetime import datetime

import pytest

from app.email_webhook import EmailWebhookManager, InboundEmail, UserEmailConfig


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


class TestSecurityFixes:
    """Test security fixes for email webhook."""

    def test_path_traversal_protection(self, tmp_path):
        """Test that path traversal attacks are blocked."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        # Test various path traversal attempts
        attack_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "abc/../../../etc/passwd",
            "abcd",  # Too short
            "abcdefghijklmnopqrstuvwxyz",  # Too long
            "abc-def123456789",  # Contains invalid chars
            "abc@def12345678",  # Contains invalid chars
        ]

        for attack in attack_patterns:
            with pytest.raises(ValueError, match="Invalid email_id"):
                manager.get_email(attack)

    def test_email_address_validation(self):
        """Test that invalid email addresses are rejected."""
        # Invalid to_address
        with pytest.raises(ValueError, match="Invalid to_address"):
            InboundEmail(
                to_address="not-an-email",
                from_address="valid@example.com",
                subject="Test",
                body_text="Body",
                body_html=None,
                received_at=datetime.now(),
            )

        # Invalid from_address
        with pytest.raises(ValueError, match="Invalid from_address"):
            InboundEmail(
                to_address="valid@example.com",
                from_address="not-an-email",
                subject="Test",
                body_text="Body",
                body_html=None,
                received_at=datetime.now(),
            )

    def test_subject_length_validation(self):
        """Test that too-long subjects are rejected."""
        with pytest.raises(ValueError, match="Subject too long"):
            InboundEmail(
                to_address="valid@example.com",
                from_address="sender@example.com",
                subject="A" * 1500,  # Exceeds MAX_SUBJECT_LENGTH
                body_text="Body",
                body_html=None,
                received_at=datetime.now(),
            )

    def test_email_size_validation(self):
        """Test that too-large emails are rejected."""
        with pytest.raises(ValueError, match="Email too large"):
            InboundEmail(
                to_address="valid@example.com",
                from_address="sender@example.com",
                subject="Test",
                body_text="A" * 1000000,  # 1MB
                body_html="B" * 100,  # Exceeds limit
                received_at=datetime.now(),
            )

    def test_date_validation(self):
        """Test that unreasonable dates are rejected."""
        from datetime import timedelta

        # Future date
        with pytest.raises(ValueError, match="future"):
            InboundEmail(
                to_address="valid@example.com",
                from_address="sender@example.com",
                subject="Test",
                body_text="Body",
                body_html=None,
                received_at=datetime.now() + timedelta(days=2),
            )

        # Very old date
        with pytest.raises(ValueError, match="too old"):
            InboundEmail(
                to_address="valid@example.com",
                from_address="sender@example.com",
                subject="Test",
                body_text="Body",
                body_html=None,
                received_at=datetime.now() - timedelta(days=400),
            )

    def test_html_sanitization(self):
        """Test that dangerous HTML content is sanitized."""
        email = InboundEmail(
            to_address="valid@example.com",
            from_address="sender@example.com",
            subject="Test",
            body_text="Body",
            body_html='<script>alert("XSS")</script><p onclick="bad()">Text</p><iframe src="evil.com"></iframe>',
            received_at=datetime.now(),
        )

        # Check that dangerous elements are removed
        assert "<script>" not in email.body_html
        assert "alert" not in email.body_html
        assert "onclick" not in email.body_html
        assert "<iframe>" not in email.body_html
        assert "evil.com" not in email.body_html

    def test_html_sanitization_with_whitespace(self):
        """Test that script tags with whitespace variations are sanitized."""
        # Test various whitespace patterns in closing tags
        test_cases = [
            "<script>alert(1)</script >",  # Space before >
            "<script>alert(2)</script\t>",  # Tab before >
            "<script>alert(3)</script\n>",  # Newline before >
            "<iframe>content</iframe >",  # Space in iframe closing
        ]

        for html in test_cases:
            email = InboundEmail(
                to_address="valid@example.com",
                from_address="sender@example.com",
                subject="Test",
                body_text="Body",
                body_html=html,
                received_at=datetime.now(),
            )
            # All variations should be removed
            assert "<script>" not in email.body_html.lower()
            assert "<iframe>" not in email.body_html.lower()
            assert "alert" not in email.body_html

    def test_rate_limiting(self, tmp_path):
        """Test that rate limiting is enforced."""
        manager = EmailWebhookManager(data_dir=tmp_path)
        addr = manager.generate_forwarding_address("test_user")

        # Send emails up to the limit
        for i in range(100):
            email = InboundEmail(
                to_address=addr,
                from_address=f"sender{i}@example.com",
                subject=f"Test {i}",
                body_text="Body",
                body_html=None,
                received_at=datetime.now(),
            )
            manager.store_inbound_email(email)

        # 101st email should be rate limited
        email = InboundEmail(
            to_address=addr,
            from_address="sender101@example.com",
            subject="Test 101",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )
        with pytest.raises(ValueError, match="Rate limit exceeded"):
            manager.store_inbound_email(email)

    def test_address_generation_format(self, tmp_path):
        """Test that generated addresses have correct format and entropy."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        # Generate multiple addresses
        addresses = set()
        for i in range(10):
            addr = manager.generate_forwarding_address(f"user{i}")
            addresses.add(addr)

            # Check format: user-{8hexchars}@domain
            import string

            parts = addr.split("@")
            assert len(parts) == 2
            local_parts = parts[0].split("-")
            assert len(local_parts) == 2
            assert local_parts[0] == "user"
            assert len(local_parts[1]) == 8
            assert all(c in string.hexdigits.lower() for c in local_parts[1])

        # No collisions
        assert len(addresses) == 10

    def test_config_corruption_handling(self, tmp_path):
        """Test that corrupt config files are handled properly."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        # Create corrupt config file
        with open(manager.config_file, "w") as f:
            f.write("{ invalid json !@#$")

        # Should recover by creating new manager
        manager2 = EmailWebhookManager(data_dir=tmp_path)
        assert len(manager2._configs) == 0

    def test_no_config_for_address(self, tmp_path):
        """Test that storing email without config raises error."""
        manager = EmailWebhookManager(data_dir=tmp_path)

        email = InboundEmail(
            to_address="unknown@example.com",
            from_address="sender@example.com",
            subject="Test",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="No config found"):
            manager.store_inbound_email(email)
