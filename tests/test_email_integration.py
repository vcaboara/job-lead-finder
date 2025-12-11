"""Tests for email integration module."""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.email_integration import EmailConfig, EmailIntegration, ParsedEmail, create_email_config_from_env


class TestEmailConfig:
    """Tests for EmailConfig dataclass."""

    def test_email_config_defaults(self):
        """Test EmailConfig default values."""
        config = EmailConfig(imap_server="imap.gmail.com", email_address="test@example.com", password="secret")

        assert config.port == 993
        assert config.use_ssl is True
        assert config.folder == "INBOX"

    def test_email_config_custom(self):
        """Test EmailConfig with custom values."""
        config = EmailConfig(
            imap_server="imap.outlook.com",
            email_address="test@outlook.com",
            password="secret",
            port=143,
            use_ssl=False,
            folder="Sent",
        )

        assert config.port == 143
        assert config.use_ssl is False
        assert config.folder == "Sent"


class TestParsedEmail:
    """Tests for ParsedEmail dataclass."""

    def test_parsed_email_required_fields(self):
        """Test ParsedEmail with required fields."""
        email = ParsedEmail(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            date=datetime.now(),
            body="Test body",
        )

        assert email.subject == "Test Subject"
        assert email.company_name is None
        assert email.job_title is None

    def test_parsed_email_all_fields(self):
        """Test ParsedEmail with all fields."""
        email = ParsedEmail(
            subject="Application: Senior Developer",
            from_addr="me@example.com",
            to_addr="careers@techcorp.com",
            date=datetime.now(),
            body="I am applying...",
            company_name="TechCorp",
            job_title="Senior Developer",
            application_url="https://techcorp.com/apply/123",
        )

        assert email.company_name == "TechCorp"
        assert email.job_title == "Senior Developer"
        assert email.application_url is not None
        assert "techcorp.com" in email.application_url


class TestEmailIntegration:
    """Tests for EmailIntegration class."""

    @pytest.fixture
    def email_config(self):
        """Create test email configuration."""
        return EmailConfig(imap_server="imap.test.com", email_address="test@test.com", password="testpass")

    @pytest.fixture
    def integration(self, email_config):
        """Create EmailIntegration instance."""
        return EmailIntegration(email_config)

    def test_initialization(self, integration, email_config):
        """Test EmailIntegration initialization."""
        assert integration.config == email_config
        assert integration.connection is None
        assert integration.tracker is not None

    @patch("imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap, integration):
        """Test successful email server connection."""
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection

        result = integration.connect()

        assert result is True
        assert integration.connection is not None
        mock_connection.login.assert_called_once()

    @patch("imaplib.IMAP4_SSL")
    def test_connect_failure(self, mock_imap, integration):
        """Test failed email server connection."""
        mock_imap.side_effect = Exception("Connection failed")

        result = integration.connect()

        assert result is False
        assert integration.connection is None

    def test_disconnect(self, integration):
        """Test email server disconnection."""
        mock_connection = MagicMock()
        integration.connection = mock_connection

        integration.disconnect()

        mock_connection.logout.assert_called_once()

    def test_extract_company_name_from_email(self, integration):
        """Test company name extraction from email address."""
        company = integration._extract_company_name("jobs@techcorp.com", "")

        assert company == "Techcorp"

    def test_extract_company_name_from_body(self, integration):
        """Test company name extraction from email body."""
        body = "Thank you for your application at Acme Corp"
        company = integration._extract_company_name("", body)

        assert company == "Acme Corp"

    def test_extract_job_title_from_subject(self, integration):
        """Test job title extraction from subject."""
        title = integration._extract_job_title("Application for Senior Python Developer", "")

        assert title == "Senior Python Developer"

    def test_extract_application_url(self, integration):
        """Test application URL extraction."""
        body = """
        Apply at: https://greenhouse.io/apply/123
        or visit our website
        """

        url = integration._extract_application_url(body)

        assert url == "https://greenhouse.io/apply/123"

    def test_extract_application_url_filters_irrelevant(self, integration):
        """Test URL extraction filters non-job URLs."""
        body = """
        Check out https://example.com and
        https://google.com for more info
        """

        url = integration._extract_application_url(body)

        assert url is None

    @patch.object(EmailIntegration, "connect")
    @patch.object(EmailIntegration, "disconnect")
    @patch.object(EmailIntegration, "fetch_recent_sent_emails")
    @patch.object(EmailIntegration, "match_emails_to_jobs")
    def test_auto_update_job_status(self, mock_match, mock_fetch, mock_disconnect, mock_connect, integration):
        """Test automatic job status update."""
        mock_connect.return_value = True

        # Mock emails
        mock_emails = [
            ParsedEmail(
                subject="Application: Developer",
                from_addr="me@test.com",
                to_addr="jobs@company.com",
                date=datetime.now(),
                body="",
                company_name="Company",
                job_title="Developer",
            )
        ]
        mock_fetch.return_value = mock_emails

        # Mock matches
        mock_match.return_value = [(mock_emails[0], "job123")]

        stats = integration.auto_update_job_status(days=7)

        assert stats["emails_checked"] == 1
        assert stats["jobs_updated"] == 1
        assert stats["jobs_not_found"] == 0

        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()


class TestCreateEmailConfigFromEnv:
    """Tests for create_email_config_from_env function."""

    def test_config_from_env_complete(self):
        """Test config creation with complete environment variables."""
        with patch.dict(
            "os.environ",
            {"EMAIL_ADDRESS": "test@example.com", "EMAIL_PASSWORD": "secret123", "IMAP_SERVER": "imap.custom.com"},
        ):
            config = create_email_config_from_env()

            assert config is not None
            assert config.email_address == "test@example.com"
            assert config.password == "secret123"
            assert config.imap_server == "imap.custom.com"

    def test_config_from_env_defaults(self):
        """Test config creation with default IMAP server."""
        with patch.dict("os.environ", {"EMAIL_ADDRESS": "test@gmail.com", "EMAIL_PASSWORD": "secret"}, clear=True):
            config = create_email_config_from_env()

            assert config is not None
            assert config.imap_server == "imap.gmail.com"

    def test_config_from_env_missing_credentials(self):
        """Test config creation fails without credentials."""
        with patch.dict("os.environ", {}, clear=True):
            config = create_email_config_from_env()

            assert config is None
