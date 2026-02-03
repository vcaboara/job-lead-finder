"""LinkedIn Handler for Technical Gatekeeper Identification.

This module implements an automated search and extraction agent to identify
Technical Gatekeepers in "Hard-to-Abate" industries (Pulp/Paper, Steel, Heavy Ag)
who are currently facing high ESG/Carbon penalty liabilities.

## Core Objective

Build an automated search and extraction agent to identify **Technical Gatekeepers** 
in "Hard-to-Abate" industries (Pulp/Paper, Steel, Heavy Ag) who are currently facing 
high ESG/Carbon penalty liabilities.

## Target Parameters (The Audit Filter)

* **Industry Focus:** Pulp and Paper Mills, Industrial Heat Processing, 
  Carbon-Intensive Manufacturing.
* **Target Titles:**
  * *Primary:* Director of Process Engineering, Lead Thermal Engineer, CTO (Technical).
  * *Secondary:* Sustainability Director (must have 'Engineer' in profile), 
    Head of Energy Procurement.
* **Keywords:** Pyrolysis, Biochar, Biomass-to-Energy, Carbon Sequestration, 
  Closed-Loop Manufacturing, 12/17 Geometry.

## Operational Logic (The 7:3 Ratio)

* **Step A (Scrape):** Identify the top 50 global firms in the Pulp and Paper sector.
* **Step B (Cross-Reference):** Match firms against known **ESG Penalty Data** 
  (Companies with high carbon-credit expenditures).
* **Step C (Extract):** Identify the 3 most senior technical individuals at each firm.
* **Step D (Payload Prep):** Generate a "Sovereign Outreach" draft focused on 
  **Thermodynamic Efficiency** and **Patent 12/17**, avoiding "pitch" language.

## Technical Stack Requirements

* **Integration:** Use LinkedIn API or LinkedIn Sales Navigator MCP 
  (with fallback to mock/demo mode).
* **Data Structure:** Output to a CSV/JSON file with columns: `Name`, `Title`, 
  `Company`, `Estimated Carbon Liability`, `Technical Direct Contact (if available)`.
* **Privacy:** Ensure all scraping adheres to rate-limiting to protect the 
  LinkedIn profile from detection/flagging.
"""

import csv
import json
import logging
import os
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class Company:
    """Represents a target company with ESG data."""

    name: str
    industry: str
    esg_score: float = 0.0
    carbon_liability_estimate: float = 0.0  # in USD
    location: Optional[str] = None
    employee_count: Optional[int] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None


@dataclass
class Contact:
    """Represents a technical gatekeeper contact."""

    name: str
    title: str
    company: str
    carbon_liability_estimate: float = 0.0
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    keywords_matched: List[str] = field(default_factory=list)
    profile_summary: Optional[str] = None


@dataclass
class OutreachDraft:
    """Represents an outreach message draft."""

    contact: Contact
    subject: str
    body: str
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# LinkedIn Handler Class
# ============================================================================


class LinkedInHandler:
    """Handler for LinkedIn Technical Gatekeeper identification.
    
    This class implements the complete workflow for identifying and extracting
    technical gatekeepers in hard-to-abate industries with ESG penalties.
    
    Supports three modes:
    1. LinkedIn API (if credentials available)
    2. Web scraping with rate limiting (requires authentication)
    3. Mock/Demo mode for testing without actual LinkedIn access
    """

    # Target industries for search
    TARGET_INDUSTRIES = [
        "Pulp and Paper Mills",
        "Industrial Heat Processing",
        "Carbon-Intensive Manufacturing",
        "Steel Manufacturing",
        "Heavy Agriculture",
        "Cement Production",
    ]

    # Primary target titles
    PRIMARY_TITLES = [
        "Director of Process Engineering",
        "Lead Thermal Engineer",
        "CTO",
        "Chief Technology Officer",
        "VP of Engineering",
    ]

    # Secondary target titles
    SECONDARY_TITLES = [
        "Sustainability Director",
        "Head of Energy Procurement",
        "Director of Operations",
        "VP of Operations",
        "Engineering Manager",
    ]

    # Target keywords for profile matching
    TARGET_KEYWORDS = [
        "Pyrolysis",
        "Biochar",
        "Biomass-to-Energy",
        "Carbon Sequestration",
        "Closed-Loop Manufacturing",
        "12/17 Geometry",
        "Thermodynamic Efficiency",
        "Carbon Credits",
        "ESG",
        "Sustainability",
    ]

    def __init__(
        self,
        mode: str = "demo",
        rate_limit_delay: int = 3,
        daily_limit: int = 100,
        esg_data_path: Optional[str] = None,
    ):
        """Initialize the LinkedIn Handler.
        
        Args:
            mode: Operation mode - 'api', 'scraping', or 'demo'
            rate_limit_delay: Delay between requests in seconds (default: 3)
            daily_limit: Maximum requests per day (default: 100)
            esg_data_path: Path to ESG penalty data JSON/CSV file
        """
        self.mode = mode
        self.rate_limit_delay = rate_limit_delay
        self.daily_limit = daily_limit
        self.request_count = 0
        self.last_request_time = 0.0
        self.esg_data: Dict[str, Company] = {}

        # Load configuration from environment
        self.linkedin_email = os.getenv("LINKEDIN_EMAIL", "")
        self.linkedin_username = os.getenv("LINKEDIN_USERNAME", "")
        self.linkedin_password = os.getenv("LINKEDIN_PASSWORD", "")
        self.linkedin_api_key = os.getenv("LINKEDIN_API_KEY", "")

        # Load ESG data if provided
        if esg_data_path:
            self._load_esg_data(esg_data_path)
        else:
            self._initialize_mock_esg_data()

        logger.info(
            f"LinkedInHandler initialized in {mode} mode with "
            f"{len(self.esg_data)} ESG records"
        )

    def _load_esg_data(self, filepath: str) -> None:
        """Load ESG penalty data from file.
        
        Args:
            filepath: Path to JSON or CSV file containing ESG data
        """
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"ESG data file not found: {filepath}")
            self._initialize_mock_esg_data()
            return

        try:
            if path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        company = Company(**item)
                        self.esg_data[company.name.lower()] = company
            elif path.suffix.lower() == ".csv":
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        company = Company(
                            name=row["name"],
                            industry=row["industry"],
                            esg_score=float(row.get("esg_score", 0)),
                            carbon_liability_estimate=float(
                                row.get("carbon_liability_estimate", 0)
                            ),
                            location=row.get("location"),
                            employee_count=int(row["employee_count"])
                            if row.get("employee_count")
                            else None,
                            website=row.get("website"),
                            linkedin_url=row.get("linkedin_url"),
                        )
                        self.esg_data[company.name.lower()] = company
            logger.info(f"Loaded {len(self.esg_data)} ESG records from {filepath}")
        except Exception as e:
            logger.error(f"Error loading ESG data: {e}")
            self._initialize_mock_esg_data()

    def _initialize_mock_esg_data(self) -> None:
        """Initialize mock ESG data for demo/testing purposes."""
        mock_companies = [
            Company(
                name="International Paper",
                industry="Pulp and Paper Mills",
                esg_score=45.2,
                carbon_liability_estimate=125_000_000,
                location="Memphis, TN",
                employee_count=50000,
            ),
            Company(
                name="Georgia-Pacific",
                industry="Pulp and Paper Mills",
                esg_score=42.8,
                carbon_liability_estimate=98_000_000,
                location="Atlanta, GA",
                employee_count=35000,
            ),
            Company(
                name="ArcelorMittal",
                industry="Steel Manufacturing",
                esg_score=38.5,
                carbon_liability_estimate=350_000_000,
                location="Luxembourg",
                employee_count=190000,
            ),
            Company(
                name="Nucor Corporation",
                industry="Steel Manufacturing",
                esg_score=52.1,
                carbon_liability_estimate=85_000_000,
                location="Charlotte, NC",
                employee_count=25000,
            ),
            Company(
                name="WestRock",
                industry="Pulp and Paper Mills",
                esg_score=48.3,
                carbon_liability_estimate=72_000_000,
                location="Atlanta, GA",
                employee_count=51000,
            ),
        ]
        for company in mock_companies:
            self.esg_data[company.name.lower()] = company

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to prevent API abuse."""
        if self.request_count >= self.daily_limit:
            raise Exception(
                f"Daily request limit ({self.daily_limit}) reached. "
                "Please try again tomorrow."
            )

        # Calculate time since last request
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Add jitter to avoid detection patterns
        jitter = random.uniform(0, 1)
        required_delay = self.rate_limit_delay + jitter

        if time_since_last < required_delay:
            sleep_time = required_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def identify_target_companies(
        self, industry: str, limit: int = 50
    ) -> List[Company]:
        """Identify top companies in target industry.
        
        Step A: Scrape/Search for top firms in specified industry.
        
        Args:
            industry: Target industry sector
            limit: Maximum number of companies to return
            
        Returns:
            List of Company objects
        """
        logger.info(f"Identifying top {limit} companies in {industry}")
        self._apply_rate_limit()

        if self.mode == "demo":
            # Return mock data filtered by industry
            companies = [
                c
                for c in self.esg_data.values()
                if industry.lower() in c.industry.lower()
            ]
            return companies[:limit]

        elif self.mode == "api":
            # LinkedIn API implementation would go here
            logger.warning("LinkedIn API mode not yet implemented, using demo data")
            return self.identify_target_companies(industry, limit)

        elif self.mode == "scraping":
            # Web scraping implementation would go here
            logger.warning("Web scraping mode not yet implemented, using demo data")
            return self.identify_target_companies(industry, limit)

        return []

    def cross_reference_esg_data(self, companies: List[Company]) -> List[Company]:
        """Match companies against ESG penalty database.
        
        Step B: Cross-reference companies with known ESG penalty data.
        
        Args:
            companies: List of companies to cross-reference
            
        Returns:
            List of companies with ESG data, sorted by carbon liability
        """
        logger.info(f"Cross-referencing {len(companies)} companies with ESG data")
        self._apply_rate_limit()

        enriched_companies = []
        for company in companies:
            company_key = company.name.lower()
            if company_key in self.esg_data:
                # Use ESG data from database
                esg_company = self.esg_data[company_key]
                company.esg_score = esg_company.esg_score
                company.carbon_liability_estimate = (
                    esg_company.carbon_liability_estimate
                )
                enriched_companies.append(company)
            else:
                # Estimate carbon liability based on industry if not in database
                company.carbon_liability_estimate = self._estimate_carbon_liability(
                    company
                )
                enriched_companies.append(company)

        # Sort by carbon liability (highest first)
        enriched_companies.sort(
            key=lambda x: x.carbon_liability_estimate, reverse=True
        )
        return enriched_companies

    def _estimate_carbon_liability(self, company: Company) -> float:
        """Estimate carbon liability for a company not in ESG database.
        
        Args:
            company: Company object
            
        Returns:
            Estimated carbon liability in USD
        """
        # Simple estimation based on industry and size
        base_estimates = {
            "pulp and paper": 50_000_000,
            "steel": 100_000_000,
            "cement": 80_000_000,
            "agriculture": 30_000_000,
            "manufacturing": 40_000_000,
        }

        estimate = 20_000_000  # Default
        for key, value in base_estimates.items():
            if key in company.industry.lower():
                estimate = value
                break

        # Adjust based on employee count if available
        if company.employee_count:
            if company.employee_count > 100000:
                estimate *= 1.5
            elif company.employee_count > 50000:
                estimate *= 1.2
            elif company.employee_count < 10000:
                estimate *= 0.7

        return estimate

    def extract_technical_gatekeepers(
        self, company: Company, count: int = 3
    ) -> List[Contact]:
        """Extract senior technical contacts from a company.
        
        Step C: Identify the most senior technical individuals at each firm.
        
        Args:
            company: Target company
            count: Number of contacts to extract (default: 3)
            
        Returns:
            List of Contact objects
        """
        logger.info(
            f"Extracting {count} technical gatekeepers from {company.name}"
        )
        self._apply_rate_limit()

        if self.mode == "demo":
            # Return mock contacts for demonstration
            return self._generate_mock_contacts(company, count)

        elif self.mode == "api":
            # LinkedIn API implementation would go here
            logger.warning("LinkedIn API mode not yet implemented, using demo data")
            return self.extract_technical_gatekeepers(company, count)

        elif self.mode == "scraping":
            # Web scraping implementation would go here
            logger.warning("Web scraping mode not yet implemented, using demo data")
            return self.extract_technical_gatekeepers(company, count)

        return []

    def _generate_mock_contacts(self, company: Company, count: int) -> List[Contact]:
        """Generate mock contacts for demonstration.
        
        Args:
            company: Company to generate contacts for
            count: Number of contacts to generate
            
        Returns:
            List of mock Contact objects
        """
        contacts = []
        titles = self.PRIMARY_TITLES + self.SECONDARY_TITLES
        names = [
            "John Smith",
            "Sarah Johnson",
            "Michael Chen",
            "Emily Williams",
            "David Brown",
            "Lisa Garcia",
        ]

        for i in range(min(count, len(titles))):
            keywords_matched = random.sample(
                self.TARGET_KEYWORDS, k=random.randint(2, 4)
            )
            contact = Contact(
                name=names[i % len(names)],
                title=titles[i],
                company=company.name,
                carbon_liability_estimate=company.carbon_liability_estimate,
                linkedin_url=f"https://linkedin.com/in/{names[i % len(names)].lower().replace(' ', '-')}",
                keywords_matched=keywords_matched,
                profile_summary=f"Experienced {titles[i]} with background in {', '.join(keywords_matched[:2])}",
            )
            contacts.append(contact)

        return contacts

    def generate_outreach_draft(self, contact: Contact) -> OutreachDraft:
        """Generate outreach message for a contact.
        
        Step D: Generate a "Sovereign Outreach" draft focused on
        Thermodynamic Efficiency and Patent 12/17.
        
        Args:
            contact: Contact to generate outreach for
            
        Returns:
            OutreachDraft object with subject, body, and notes
        """
        logger.info(f"Generating outreach draft for {contact.name} at {contact.company}")

        # Format carbon liability as readable number
        liability_str = f"${contact.carbon_liability_estimate / 1_000_000:.1f}M"

        subject = (
            f"Thermodynamic Efficiency Opportunity for {contact.company} "
            f"[Patent 12/17]"
        )

        body = f"""Dear {contact.name.split()[0]},

I hope this message finds you well. I'm reaching out regarding innovative solutions 
in thermodynamic efficiency that may align with {contact.company}'s operational 
objectives in the {contact.company} sector.

Given your background in {', '.join(contact.keywords_matched[:2]) if contact.keywords_matched else 'process engineering'}, 
I believe you'll find our Patent 12/17 technology particularly relevant. This 
approach addresses key challenges in:

• Thermodynamic Efficiency optimization
• Carbon sequestration integration
• Closed-loop manufacturing systems

Our analysis indicates that firms in your sector are managing approximately 
{liability_str} in carbon-related obligations. The 12/17 Geometry framework 
offers a pathway to substantially reduce these liabilities while enhancing 
operational efficiency.

Would you be open to a brief technical discussion about how these principles 
might apply to {contact.company}'s specific process architecture?

Best regards
"""

        notes = (
            f"Contact Keywords: {', '.join(contact.keywords_matched)}\n"
            f"Carbon Liability: {liability_str}\n"
            f"Company ESG Context: High carbon-intensive operations\n"
            f"Recommended Follow-up: Technical white paper on 12/17 Geometry"
        )

        return OutreachDraft(
            contact=contact, subject=subject, body=body, notes=notes
        )

    def export_to_csv(self, data: List[Contact], filepath: str) -> None:
        """Export contact data to CSV file.
        
        Args:
            data: List of Contact objects to export
            filepath: Output CSV file path
        """
        logger.info(f"Exporting {len(data)} contacts to CSV: {filepath}")

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "Name",
                "Title",
                "Company",
                "Estimated Carbon Liability",
                "LinkedIn URL",
                "Email",
                "Keywords Matched",
                "Profile Summary",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for contact in data:
                writer.writerow(
                    {
                        "Name": contact.name,
                        "Title": contact.title,
                        "Company": contact.company,
                        "Estimated Carbon Liability": f"${contact.carbon_liability_estimate:,.0f}",
                        "LinkedIn URL": contact.linkedin_url or "",
                        "Email": contact.email or "",
                        "Keywords Matched": ", ".join(contact.keywords_matched),
                        "Profile Summary": contact.profile_summary or "",
                    }
                )

        logger.info(f"Successfully exported to {filepath}")

    def export_to_json(self, data: List[Contact], filepath: str) -> None:
        """Export contact data to JSON file.
        
        Args:
            data: List of Contact objects to export
            filepath: Output JSON file path
        """
        logger.info(f"Exporting {len(data)} contacts to JSON: {filepath}")

        contacts_dict = [asdict(contact) for contact in data]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(contacts_dict, f, indent=2, default=str)

        logger.info(f"Successfully exported to {filepath}")

    def run_full_pipeline(
        self, industry: str, company_limit: int = 50, contacts_per_company: int = 3
    ) -> Dict[str, Any]:
        """Run the complete LinkedIn handler pipeline.
        
        This executes all steps:
        A. Identify target companies
        B. Cross-reference ESG data
        C. Extract technical gatekeepers
        D. Generate outreach drafts
        
        Args:
            industry: Target industry sector
            company_limit: Maximum companies to process
            contacts_per_company: Contacts to extract per company
            
        Returns:
            Dictionary containing companies, contacts, and outreach drafts
        """
        logger.info(
            f"Starting full pipeline for {industry} "
            f"(limit: {company_limit} companies, {contacts_per_company} contacts each)"
        )

        # Step A: Identify companies
        companies = self.identify_target_companies(industry, company_limit)
        logger.info(f"Step A: Found {len(companies)} companies")

        # Step B: Cross-reference ESG data
        companies_with_esg = self.cross_reference_esg_data(companies)
        logger.info(
            f"Step B: Enriched {len(companies_with_esg)} companies with ESG data"
        )

        # Step C: Extract technical gatekeepers
        all_contacts = []
        for company in companies_with_esg[:10]:  # Limit to top 10 for demo
            contacts = self.extract_technical_gatekeepers(
                company, contacts_per_company
            )
            all_contacts.extend(contacts)

        logger.info(f"Step C: Extracted {len(all_contacts)} technical contacts")

        # Step D: Generate outreach drafts
        outreach_drafts = []
        for contact in all_contacts[:20]:  # Limit drafts for demo
            draft = self.generate_outreach_draft(contact)
            outreach_drafts.append(draft)

        logger.info(f"Step D: Generated {len(outreach_drafts)} outreach drafts")

        return {
            "companies": companies_with_esg,
            "contacts": all_contacts,
            "outreach_drafts": outreach_drafts,
            "stats": {
                "companies_found": len(companies),
                "companies_with_esg": len(companies_with_esg),
                "total_contacts": len(all_contacts),
                "outreach_drafts_generated": len(outreach_drafts),
            },
        }