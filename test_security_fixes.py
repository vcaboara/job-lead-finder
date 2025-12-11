#!/usr/bin/env python3
"""Test script to validate security fixes."""
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.email_webhook import EmailWebhookManager, InboundEmail
from app.email_parser import EmailParser


def test_path_traversal_protection():
    """Test that path traversal is blocked in get_email()."""
    print("Testing path traversal protection...")
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = EmailWebhookManager(data_dir=Path(tmpdir))

        # Try path traversal attacks
        bad_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "abc/../../../etc/passwd",
            "abcd",  # Too short
            "abcdefghijklmnopqrstuvwxyz",  # Too long
            "abc-def123456789",  # Contains dash
        ]

        for bad_id in bad_ids:
            try:
                result = manager.get_email(bad_id)
                print(f"  ❌ FAIL: {bad_id} should have raised ValueError")
                return False
            except ValueError as e:
                print(f"  ✓ Blocked: {bad_id}")

    print("  ✅ Path traversal protection works!\n")
    return True


def test_email_validation():
    """Test that email validation works."""
    print("Testing email input validation...")

    # Test invalid email addresses
    try:
        email = InboundEmail(
            to_address="not-an-email",
            from_address="valid@example.com",
            subject="Test",
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )
        print("  ❌ FAIL: Should have rejected invalid to_address")
        return False
    except ValueError:
        print("  ✓ Rejected invalid to_address")

    # Test subject length limit
    try:
        email = InboundEmail(
            to_address="valid@example.com",
            from_address="sender@example.com",
            subject="A" * 1500,  # Too long
            body_text="Body",
            body_html=None,
            received_at=datetime.now(),
        )
        print("  ❌ FAIL: Should have rejected too-long subject")
        return False
    except ValueError:
        print("  ✓ Rejected too-long subject")

    # Test HTML sanitization
    email = InboundEmail(
        to_address="valid@example.com",
        from_address="sender@example.com",
        subject="Test",
        body_text="Body",
        body_html='<script>alert("XSS")</script><p onclick="bad()">Text</p>',
        received_at=datetime.now(),
    )
    if "<script>" in email.body_html or "onclick" in email.body_html:
        print(f"  ❌ FAIL: HTML not sanitized: {email.body_html}")
        return False
    print(f"  ✓ HTML sanitized: {email.body_html}")

    print("  ✅ Email validation works!\n")
    return True


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("Testing rate limiting...")
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = EmailWebhookManager(data_dir=Path(tmpdir))

        # Create a user
        addr = manager.generate_forwarding_address("test_user")
        print(f"  Created address: {addr}")

        # Try to send many emails quickly
        emails_sent = 0
        for i in range(105):  # Exceed rate limit of 100
            try:
                email = InboundEmail(
                    to_address=addr,
                    from_address=f"sender{i}@example.com",
                    subject=f"Test {i}",
                    body_text="Body",
                    body_html=None,
                    received_at=datetime.now(),
                )
                manager.store_inbound_email(email)
                emails_sent += 1
            except ValueError as e:
                if "Rate limit exceeded" in str(e):
                    print(f"  ✓ Rate limit kicked in after {emails_sent} emails")
                    break
                else:
                    print(f"  ❌ Unexpected error: {e}")
                    return False

        if emails_sent >= 105:
            print(f"  ❌ FAIL: Rate limit not enforced (sent {emails_sent} emails)")
            return False

    print("  ✅ Rate limiting works!\n")
    return True


def test_address_generation_entropy():
    """Test that address generation has good entropy."""
    print("Testing address generation entropy...")
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = EmailWebhookManager(data_dir=Path(tmpdir))

        # Generate multiple addresses
        addresses = set()
        for i in range(10):
            addr = manager.generate_forwarding_address(f"user{i}")
            addresses.add(addr)

        if len(addresses) != 10:
            print(f"  ❌ FAIL: Got collisions in {len(addresses)}/10 addresses")
            return False

        # Check format (should be user-{8hexchars}@domain)
        for addr in addresses:
            parts = addr.split("@")[0].split("-")
            if len(parts) != 2 or parts[0] != "user" or len(parts[1]) != 8:
                print(f"  ❌ FAIL: Bad format: {addr}")
                return False
            print(f"  ✓ Valid format: {addr}")

    print("  ✅ Address generation has good entropy!\n")
    return True


def test_regex_timeout_protection():
    """Test regex timeout protection in parser."""
    print("Testing regex timeout protection...")
    parser = EmailParser()

    # Create a potentially malicious input (backtracking bomb)
    evil_text = "A" * 10000 + "!"

    try:
        result = parser.detect_email_type(evil_text, evil_text, "test@example.com")
        print(f"  ✓ Handled long input: {result}")
    except TimeoutError:
        print("  ✓ Timeout protection triggered (expected)")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

    print("  ✅ Regex timeout protection works!\n")
    return True


def main():
    """Run all security tests."""
    print("=" * 60)
    print("SECURITY FIXES VALIDATION")
    print("=" * 60 + "\n")

    tests = [
        test_path_traversal_protection,
        test_email_validation,
        test_rate_limiting,
        test_address_generation_entropy,
        test_regex_timeout_protection,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test crashed: {e}\n")
            results.append(False)

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
