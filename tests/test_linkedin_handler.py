"""Tests for LinkedIn handler and Technical Gatekeeper identification."""
import json
import tempfile
from pathlib import Path

import pytest

from app.linkedin_handler import (
    Company,
    Contact,
    LinkedInHandler,
    OutreachDraft,
)


class TestDataModels:
    """Test data model classes."""

    def test_company_creation(self):
        """Test Company dataclass creation."""
        company = Company(
            name="Test Corp",
            industry="Pulp and Paper Mills",
            esg_score=45.5,
            carbon_liability_estimate=100_000_000,
        )
        assert company.name == "Test Corp"
        assert company.industry == "Pulp and Paper Mills"
        assert company.esg_score == 45.5
        assert company.carbon_liability_estimate == 100_000_000

    def test_contact_creation(self):
        """Test Contact dataclass creation."""
        contact = Contact(
            name="John Doe",
            title="CTO",
            company="Test Corp",
            keywords_matched=["Pyrolysis", "Biochar"],
        )
        assert contact.name == "John Doe"
        assert contact.title == "CTO"
        assert contact.company == "Test Corp"
        assert len(contact.keywords_matched) == 2

    def test_outreach_draft_creation(self):
        """Test OutreachDraft creation."""
        contact = Contact(
            name="Jane Smith", title="Director of Process Engineering", company="Test Corp"
        )
        draft = OutreachDraft(
            contact=contact, subject="Test Subject", body="Test Body", notes="Test Notes"
        )
        assert draft.contact.name == "Jane Smith"
        assert draft.subject == "Test Subject"
        assert draft.body == "Test Body"
        assert draft.notes == "Test Notes"


class TestLinkedInHandler:
    """Test LinkedInHandler class."""

    def test_handler_initialization_demo_mode(self):
        """Test handler initialization in demo mode."""
        handler = LinkedInHandler(mode="demo")
        assert handler.mode == "demo"
        assert handler.rate_limit_delay == 3
        assert handler.daily_limit == 100
        assert len(handler.esg_data) > 0

    def test_handler_initialization_with_params(self):
        """Test handler with custom parameters."""
        handler = LinkedInHandler(mode="api", rate_limit_delay=5, daily_limit=50)
        assert handler.mode == "api"
        assert handler.rate_limit_delay == 5
        assert handler.daily_limit == 50

    def test_load_mock_esg_data(self):
        """Test mock ESG data initialization."""
        handler = LinkedInHandler(mode="demo")
        assert "international paper" in handler.esg_data
        assert "arcelormittal" in handler.esg_data

        # Check data structure
        company = handler.esg_data["international paper"]
        assert company.name == "International Paper"
        assert company.carbon_liability_estimate > 0
        assert company.esg_score > 0

    def test_identify_target_companies(self):
        """Test company identification."""
        handler = LinkedInHandler(mode="demo")
        companies = handler.identify_target_companies("Pulp and Paper Mills", limit=5)

        assert len(companies) > 0
        assert all(isinstance(c, Company) for c in companies)
        assert all("paper" in c.industry.lower() or "pulp" in c.industry.lower() for c in companies)

    def test_cross_reference_esg_data(self):
        """Test ESG data cross-referencing."""
        handler = LinkedInHandler(mode="demo")
        companies = handler.identify_target_companies("Pulp and Paper Mills", limit=3)
        enriched = handler.cross_reference_esg_data(companies)

        assert len(enriched) == len(companies)
        assert all(c.carbon_liability_estimate > 0 for c in enriched)
        # Should be sorted by carbon liability (highest first)
        liabilities = [c.carbon_liability_estimate for c in enriched]
        assert liabilities == sorted(liabilities, reverse=True)

    def test_estimate_carbon_liability(self):
        """Test carbon liability estimation."""
        handler = LinkedInHandler(mode="demo")

        # Test with different industries
        paper_company = Company(
            name="Test Paper Co", industry="Pulp and Paper Mills", employee_count=50000
        )
        steel_company = Company(
            name="Test Steel Co", industry="Steel Manufacturing", employee_count=100000
        )

        paper_liability = handler._estimate_carbon_liability(paper_company)
        steel_liability = handler._estimate_carbon_liability(steel_company)

        assert paper_liability > 0
        assert steel_liability > 0
        # Steel typically has higher carbon liability
        assert steel_liability > paper_liability

    def test_extract_technical_gatekeepers(self):
        """Test technical gatekeeper extraction."""
        handler = LinkedInHandler(mode="demo")
        company = Company(
            name="Test Corp",
            industry="Steel Manufacturing",
            carbon_liability_estimate=100_000_000,
        )

        contacts = handler.extract_technical_gatekeepers(company, count=3)

        assert len(contacts) == 3
        assert all(isinstance(c, Contact) for c in contacts)
        assert all(c.company == company.name for c in contacts)
        assert all(c.carbon_liability_estimate == company.carbon_liability_estimate for c in contacts)
        assert all(len(c.keywords_matched) > 0 for c in contacts)

    def test_generate_outreach_draft(self):
        """Test outreach draft generation."""
        handler = LinkedInHandler(mode="demo")
        contact = Contact(
            name="John Smith",
            title="Director of Process Engineering",
            company="Test Corp",
            carbon_liability_estimate=100_000_000,
            keywords_matched=["Pyrolysis", "Biochar"],
        )

        draft = handler.generate_outreach_draft(contact)

        assert isinstance(draft, OutreachDraft)
        assert draft.contact == contact
        assert "John" in draft.body
        assert "Test Corp" in draft.body
        assert "12/17" in draft.subject or "12/17" in draft.body
        assert "Thermodynamic Efficiency" in draft.body or "Thermodynamic Efficiency" in draft.subject
        assert len(draft.notes) > 0

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        handler = LinkedInHandler(mode="demo", rate_limit_delay=0.1, daily_limit=5)

        # Make several requests
        for i in range(3):
            handler._apply_rate_limit()

        assert handler.request_count == 3

        # Test daily limit
        with pytest.raises(Exception, match="Daily request limit"):
            for i in range(10):
                handler._apply_rate_limit()

    def test_export_to_csv(self):
        """Test CSV export functionality."""
        handler = LinkedInHandler(mode="demo")
        contacts = [
            Contact(
                name="John Doe",
                title="CTO",
                company="Test Corp",
                carbon_liability_estimate=50_000_000,
                linkedin_url="https://linkedin.com/in/johndoe",
                keywords_matched=["Pyrolysis", "Biochar"],
            ),
            Contact(
                name="Jane Smith",
                title="VP Engineering",
                company="Test Corp 2",
                carbon_liability_estimate=75_000_000,
                email="jane@example.com",
                keywords_matched=["Carbon Sequestration"],
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_export.csv"
            handler.export_to_csv(contacts, str(filepath))

            assert filepath.exists()

            # Verify CSV content
            import csv

            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["Name"] == "John Doe"
            assert rows[0]["Title"] == "CTO"
            assert rows[1]["Name"] == "Jane Smith"

    def test_export_to_json(self):
        """Test JSON export functionality."""
        handler = LinkedInHandler(mode="demo")
        contacts = [
            Contact(
                name="John Doe",
                title="CTO",
                company="Test Corp",
                carbon_liability_estimate=50_000_000,
                keywords_matched=["Pyrolysis"],
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_export.json"
            handler.export_to_json(contacts, str(filepath))

            assert filepath.exists()

            # Verify JSON content
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["name"] == "John Doe"
            assert data[0]["title"] == "CTO"
            assert data[0]["keywords_matched"] == ["Pyrolysis"]

    def test_load_esg_data_from_json(self):
        """Test loading ESG data from JSON file."""
        esg_data = [
            {
                "name": "Test Company",
                "industry": "Test Industry",
                "esg_score": 50.0,
                "carbon_liability_estimate": 100000000,
                "location": "Test Location",
                "employee_count": 10000,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "esg_data.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(esg_data, f)

            handler = LinkedInHandler(mode="demo", esg_data_path=str(filepath))
            assert "test company" in handler.esg_data
            assert handler.esg_data["test company"].esg_score == 50.0

    def test_load_esg_data_from_csv(self):
        """Test loading ESG data from CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "esg_data.csv"

            import csv

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "name",
                        "industry",
                        "esg_score",
                        "carbon_liability_estimate",
                        "location",
                        "employee_count",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "name": "CSV Test Company",
                        "industry": "Test Industry",
                        "esg_score": "45.5",
                        "carbon_liability_estimate": "200000000",
                        "location": "Test Location",
                        "employee_count": "20000",
                    }
                )

            handler = LinkedInHandler(mode="demo", esg_data_path=str(filepath))
            assert "csv test company" in handler.esg_data
            assert handler.esg_data["csv test company"].esg_score == 45.5

    def test_full_pipeline(self):
        """Test complete pipeline execution."""
        handler = LinkedInHandler(mode="demo")
        results = handler.run_full_pipeline(
            industry="Pulp and Paper Mills", company_limit=5, contacts_per_company=2
        )

        assert "companies" in results
        assert "contacts" in results
        assert "outreach_drafts" in results
        assert "stats" in results

        stats = results["stats"]
        assert stats["companies_found"] > 0
        assert stats["total_contacts"] > 0
        assert stats["outreach_drafts_generated"] > 0

        # Verify data types
        assert all(isinstance(c, Company) for c in results["companies"])
        assert all(isinstance(c, Contact) for c in results["contacts"])
        assert all(isinstance(d, OutreachDraft) for d in results["outreach_drafts"])

    def test_target_keywords(self):
        """Test that target keywords are defined."""
        assert len(LinkedInHandler.TARGET_KEYWORDS) > 0
        assert "Pyrolysis" in LinkedInHandler.TARGET_KEYWORDS
        assert "Biochar" in LinkedInHandler.TARGET_KEYWORDS
        assert "12/17 Geometry" in LinkedInHandler.TARGET_KEYWORDS

    def test_target_industries(self):
        """Test that target industries are defined."""
        assert len(LinkedInHandler.TARGET_INDUSTRIES) > 0
        assert "Pulp and Paper Mills" in LinkedInHandler.TARGET_INDUSTRIES
        assert "Steel Manufacturing" in LinkedInHandler.TARGET_INDUSTRIES

    def test_target_titles(self):
        """Test that target titles are defined."""
        assert len(LinkedInHandler.PRIMARY_TITLES) > 0
        assert len(LinkedInHandler.SECONDARY_TITLES) > 0
        assert "Director of Process Engineering" in LinkedInHandler.PRIMARY_TITLES
        assert "CTO" in LinkedInHandler.PRIMARY_TITLES
        assert "Sustainability Director" in LinkedInHandler.SECONDARY_TITLES
