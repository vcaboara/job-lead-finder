"""Tests for CompanyStore database operations."""

import sqlite3
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.discovery import Company, CompanySize, CompanyStore, IndustryType


@pytest.fixture
def temp_db():
    """Create temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup with Windows file lock retry
    for _ in range(3):
        try:
            if db_path.exists():
                db_path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture
def store(temp_db):
    """Create initialized CompanyStore."""
    store = CompanyStore(temp_db)
    store.initialize()
    yield store
    # Explicitly cleanup database connections
    store.close()


@pytest.fixture
def sample_company():
    """Sample company for testing."""
    return Company(
        name="Acme Corp",
        website="https://acme.com",
        careers_url="https://acme.com/careers",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        description="AI-powered widgets",
        tech_stack=["Python", "React"],
        locations=["San Francisco", "Remote"],
        funding_stage="Series A",
        discovered_via="hackernews",
        discovered_at=datetime.now(UTC),
        metadata={"hn_thread_id": "12345"},
    )


def test_initialize_creates_schema(temp_db):
    """Test database initialization."""
    store = CompanyStore(temp_db)
    store.initialize()

    # Use with statement to ensure connection closes properly
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = {row[0] for row in cursor.fetchall()}

    assert {"companies", "jobs", "discovery_log", "custom_industries"}.issubset(tables)

    # Explicitly close to prevent resource leaks
    store.close()


def test_save_and_get_company(store, sample_company):
    """Test saving and retrieving a company."""
    company_id = store.save_company(sample_company)
    retrieved = store.get_company(company_id)

    assert retrieved is not None
    assert retrieved.name == "Acme Corp"
    assert retrieved.website == "https://acme.com"
    assert retrieved.tech_stack == ["Python", "React"]


def test_save_duplicate_updates(store, sample_company):
    """Test that duplicate website updates existing record."""
    id1 = store.save_company(sample_company)

    sample_company.description = "Updated"
    id2 = store.save_company(sample_company)

    assert id1 == id2
    assert store.get_company(id1).description == "Updated"


def test_get_nonexistent_company(store):
    """Test getting company that doesn't exist."""
    assert store.get_company(999) is None


def test_find_by_industry(store):
    """Test filtering by industry."""
    tech = Company(
        name="Tech Co",
        website="https://tech.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    health = Company(
        name="Health Co",
        website="https://health.com",
        industry=IndustryType.HEALTHCARE,
        size=CompanySize.SMALL,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(tech)
    store.save_company(health)

    results = store.find_companies(industries=[IndustryType.TECH])
    assert len(results) == 1
    assert results[0].name == "Tech Co"


def test_find_by_size(store):
    """Test filtering by company size."""
    startup = Company(
        name="Startup",
        website="https://startup.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    enterprise = Company(
        name="Enterprise",
        website="https://enterprise.com",
        industry=IndustryType.TECH,
        size=CompanySize.LARGE,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(startup)
    store.save_company(enterprise)

    results = store.find_companies(sizes=[CompanySize.STARTUP])
    assert len(results) == 1
    assert results[0].name == "Startup"


def test_find_by_location(store):
    """Test filtering by location."""
    sf = Company(
        name="SF Co",
        website="https://sf.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        locations=["San Francisco", "Remote"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    ny = Company(
        name="NY Co",
        website="https://ny.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        locations=["New York"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(sf)
    store.save_company(ny)

    results = store.find_companies(locations=["San Francisco"])
    assert len(results) == 1
    assert results[0].name == "SF Co"


def test_find_by_tech_stack(store):
    """Test filtering by technology."""
    python_shop = Company(
        name="Python Shop",
        website="https://python.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        tech_stack=["Python", "Django"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    js_shop = Company(
        name="JS Shop",
        website="https://js.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        tech_stack=["JavaScript", "React"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(python_shop)
    store.save_company(js_shop)

    results = store.find_companies(tech_stack=["Python"])
    assert len(results) == 1
    assert results[0].name == "Python Shop"


def test_find_with_limit(store):
    """Test result limiting."""
    for i in range(5):
        company = Company(
            name=f"Company {i}",
            website=f"https://company{i}.com",
            industry=IndustryType.TECH,
            size=CompanySize.STARTUP,
            discovered_via="test",
            discovered_at=datetime.now(UTC),
        )
        store.save_company(company)

    results = store.find_companies(limit=3)
    assert len(results) == 3


def test_update_careers_url(store, sample_company):
    """Test updating careers URL."""
    company_id = store.save_company(sample_company)

    success = store.update_careers_url(company_id, "https://acme.com/jobs")
    assert success is True
    assert store.get_company(company_id).careers_url == "https://acme.com/jobs"


def test_mark_company_checked(store, sample_company):
    """Test marking company as checked."""
    company_id = store.save_company(sample_company)
    store.mark_company_checked(company_id)

    with sqlite3.connect(str(store.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_checked FROM companies WHERE id = ?", (company_id,))
        assert cursor.fetchone()[0] is not None


def test_log_discovery(store):
    """Test logging discovery operation."""
    store.log_discovery(
        source="hackernews",
        companies_found=10,
        companies_new=5,
        companies_updated=3,
        errors=["rate limit"],
        metadata={"thread_id": "123"},
        duration_seconds=15.5,
    )

    with sqlite3.connect(str(store.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM discovery_log ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        assert row[1] == "hackernews"  # source
        assert row[3] == 10  # companies_found


def test_get_stats(store):
    """Test statistics aggregation."""
    for i in range(3):
        store.save_company(
            Company(
                name=f"Tech {i}",
                website=f"https://tech{i}.com",
                industry=IndustryType.TECH,
                size=CompanySize.STARTUP,
                discovered_via="test",
                discovered_at=datetime.now(UTC),
            )
        )

    store.save_company(
        Company(
            name="Health",
            website="https://health.com",
            industry=IndustryType.HEALTHCARE,
            size=CompanySize.SMALL,
            discovered_via="test",
            discovered_at=datetime.now(UTC),
        )
    )

    stats = store.get_stats()
    assert stats["total_companies"] == 4
    assert stats["by_industry"][IndustryType.TECH.value] == 3
    assert stats["by_size"][CompanySize.STARTUP.value] == 3


def test_find_active_only(store):
    """Test filtering by active status."""
    active = Company(
        name="Active Co",
        website="https://active.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    inactive = Company(
        name="Inactive Co",
        website="https://inactive.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(active)
    inactive_id = store.save_company(inactive)

    # Mark one as inactive
    with sqlite3.connect(str(store.db_path)) as conn:
        conn.execute("UPDATE companies SET active = 0 WHERE id = ?", (inactive_id,))
        conn.commit()

    # active_only=True (default) should filter out inactive
    results = store.find_companies(active_only=True)
    assert len(results) == 1
    assert results[0].name == "Active Co"

    # active_only=False should include all
    results = store.find_companies(active_only=False)
    assert len(results) == 2


def test_update_careers_url_nonexistent(store):
    """Test updating careers URL for non-existent company returns False."""
    success = store.update_careers_url(999, "https://example.com/careers")
    assert success is False


def test_find_combined_filters(store):
    """Test combining multiple filter parameters."""
    # Create diverse companies
    matching = Company(
        name="Matching Co",
        website="https://matching.com",
        industry=IndustryType.TECH,
        size=CompanySize.STARTUP,
        locations=["San Francisco"],
        tech_stack=["Python"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    wrong_industry = Company(
        name="Wrong Industry",
        website="https://wrong-industry.com",
        industry=IndustryType.HEALTHCARE,
        size=CompanySize.STARTUP,
        locations=["San Francisco"],
        tech_stack=["Python"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )
    wrong_size = Company(
        name="Wrong Size",
        website="https://wrong-size.com",
        industry=IndustryType.TECH,
        size=CompanySize.LARGE,
        locations=["San Francisco"],
        tech_stack=["Python"],
        discovered_via="test",
        discovered_at=datetime.now(UTC),
    )

    store.save_company(matching)
    store.save_company(wrong_industry)
    store.save_company(wrong_size)

    # Combined filter should only return the matching company
    results = store.find_companies(
        industries=[IndustryType.TECH],
        sizes=[CompanySize.STARTUP],
        locations=["San Francisco"],
        tech_stack=["Python"],
    )
    assert len(results) == 1
    assert results[0].name == "Matching Co"
