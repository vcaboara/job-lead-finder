#!/usr/bin/env python3
"""CLI tool for email integration.

Usage:
    python -m app.cli_email check        # Check for new applications
    python -m app.cli_email sync         # Sync job status from emails
    python -m app.cli_email test         # Test email connection
"""
import argparse
import logging
import sys
from pathlib import Path

from app.email_integration import EmailIntegration, create_email_config_from_env

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_connection():
    """Test email server connection."""
    config = create_email_config_from_env()
    if not config:
        logger.error("Email credentials not configured")
        logger.error("Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env")
        return 1

    integration = EmailIntegration(config)

    logger.info(f"Testing connection to {config.imap_server}...")
    if integration.connect():
        logger.info("✓ Connection successful")
        integration.disconnect()
        return 0
    else:
        logger.error("✗ Connection failed")
        return 1


def check_emails(days: int = 7):
    """Check recent sent emails."""
    config = create_email_config_from_env()
    if not config:
        logger.error("Email credentials not configured")
        return 1

    integration = EmailIntegration(config)

    if not integration.connect():
        logger.error("Failed to connect to email server")
        return 1

    try:
        logger.info(f"Fetching emails from last {days} days...")
        emails = integration.fetch_recent_sent_emails(days)

        logger.info(f"Found {len(emails)} sent emails")

        for email in emails:
            print(f"\n{'='*60}")
            print(f"Date: {email.date}")
            print(f"Subject: {email.subject}")
            print(f"To: {email.to_addr}")
            if email.company_name:
                print(f"Company: {email.company_name}")
            if email.job_title:
                print(f"Job Title: {email.job_title}")
            if email.application_url:
                print(f"Application URL: {email.application_url}")

        return 0

    finally:
        integration.disconnect()


def sync_job_status(days: int = 7):
    """Sync job status from sent emails."""
    config = create_email_config_from_env()
    if not config:
        logger.error("Email credentials not configured")
        return 1

    integration = EmailIntegration(config)

    logger.info(f"Syncing job status from last {days} days...")
    stats = integration.auto_update_job_status(days)

    logger.info(f"\nSync Results:")
    logger.info(f"  Emails checked: {stats['emails_checked']}")
    logger.info(f"  Jobs updated: {stats['jobs_updated']}")
    logger.info(f"  Jobs not found: {stats['jobs_not_found']}")

    if stats["jobs_updated"] > 0:
        logger.info(f"✓ Successfully updated {stats['jobs_updated']} jobs")
    else:
        logger.warning("No jobs were updated")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Email integration for job application tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test email connection
  python -m app.cli_email test

  # Check recent sent emails
  python -m app.cli_email check --days 7

  # Sync job status from emails
  python -m app.cli_email sync --days 14

Environment Variables:
  EMAIL_ADDRESS     Your email address
  EMAIL_PASSWORD    Your email password or app-specific password
  IMAP_SERVER       IMAP server (default: imap.gmail.com)
        """,
    )

    parser.add_argument("command", choices=["test", "check", "sync"], help="Command to run")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")

    args = parser.parse_args()

    try:
        if args.command == "test":
            return test_connection()
        elif args.command == "check":
            return check_emails(args.days)
        elif args.command == "sync":
            return sync_job_status(args.days)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
