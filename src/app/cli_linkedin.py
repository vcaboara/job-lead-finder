#!/usr/bin/env python3
"""CLI tool for LinkedIn Technical Gatekeeper identification.

Usage:
    python -m app.cli_linkedin search --industry "Pulp and Paper Mills" --limit 10
    python -m app.cli_linkedin pipeline --industry "Steel Manufacturing" --output results.csv
    python -m app.cli_linkedin demo --output demo_results.json
"""
import argparse
import logging
import sys
from pathlib import Path

from app.linkedin_handler import LinkedInHandler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def search_companies(args):
    """Search for companies in target industry."""
    handler = LinkedInHandler(mode=args.mode)

    logger.info(f"Searching for companies in: {args.industry}")
    companies = handler.identify_target_companies(args.industry, args.limit)

    if not companies:
        logger.warning("No companies found")
        return 1

    # Enrich with ESG data
    companies_with_esg = handler.cross_reference_esg_data(companies)

    logger.info(f"\nFound {len(companies_with_esg)} companies:\n")
    for i, company in enumerate(companies_with_esg, 1):
        liability = company.carbon_liability_estimate / 1_000_000
        print(f"{i}. {company.name}")
        print(f"   Industry: {company.industry}")
        print(f"   ESG Score: {company.esg_score}")
        print(f"   Carbon Liability: ${liability:.1f}M")
        if company.location:
            print(f"   Location: {company.location}")
        print()

    return 0


def extract_contacts(args):
    """Extract technical gatekeepers from a specific company."""
    handler = LinkedInHandler(mode=args.mode)

    # First find the company
    companies = handler.identify_target_companies(args.industry, limit=50)
    target_company = None

    for company in companies:
        if args.company.lower() in company.name.lower():
            target_company = company
            break

    if not target_company:
        logger.error(f"Company '{args.company}' not found")
        return 1

    # Enrich with ESG data
    enriched = handler.cross_reference_esg_data([target_company])
    if enriched:
        target_company = enriched[0]

    logger.info(f"Extracting contacts from: {target_company.name}")
    contacts = handler.extract_technical_gatekeepers(target_company, args.count)

    if not contacts:
        logger.warning("No contacts found")
        return 1

    logger.info(f"\nFound {len(contacts)} technical gatekeepers:\n")
    for i, contact in enumerate(contacts, 1):
        print(f"{i}. {contact.name} - {contact.title}")
        print(f"   Company: {contact.company}")
        if contact.linkedin_url:
            print(f"   LinkedIn: {contact.linkedin_url}")
        if contact.keywords_matched:
            print(f"   Keywords: {', '.join(contact.keywords_matched)}")
        print()

    return 0


def run_pipeline(args):
    """Run the full LinkedIn handler pipeline."""
    handler = LinkedInHandler(
        mode=args.mode, esg_data_path=args.esg_data if hasattr(args, "esg_data") else None
    )

    logger.info("Running full pipeline...")
    results = handler.run_full_pipeline(
        industry=args.industry,
        company_limit=args.company_limit,
        contacts_per_company=args.contacts_per_company,
    )

    # Display statistics
    stats = results["stats"]
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline Results")
    logger.info("=" * 60)
    logger.info(f"Companies found: {stats['companies_found']}")
    logger.info(f"Companies with ESG data: {stats['companies_with_esg']}")
    logger.info(f"Total contacts extracted: {stats['total_contacts']}")
    logger.info(f"Outreach drafts generated: {stats['outreach_drafts_generated']}")
    logger.info("=" * 60 + "\n")

    # Export results if output file specified
    if args.output:
        output_path = Path(args.output)
        contacts = results["contacts"]

        if output_path.suffix.lower() == ".json":
            handler.export_to_json(contacts, str(output_path))
        elif output_path.suffix.lower() == ".csv":
            handler.export_to_csv(contacts, str(output_path))
        else:
            logger.warning(f"Unknown output format: {output_path.suffix}")
            logger.info("Defaulting to CSV format")
            csv_path = output_path.with_suffix(".csv")
            handler.export_to_csv(contacts, str(csv_path))

        logger.info(f"✓ Results exported to {args.output}")

        # Also export outreach drafts if available
        if results["outreach_drafts"]:
            drafts_path = output_path.parent / f"{output_path.stem}_outreach_drafts.json"
            import json

            drafts_data = []
            for draft in results["outreach_drafts"]:
                drafts_data.append(
                    {
                        "contact_name": draft.contact.name,
                        "contact_title": draft.contact.title,
                        "company": draft.contact.company,
                        "subject": draft.subject,
                        "body": draft.body,
                        "notes": draft.notes,
                    }
                )

            with open(drafts_path, "w", encoding="utf-8") as f:
                json.dump(drafts_data, f, indent=2)

            logger.info(f"✓ Outreach drafts exported to {drafts_path}")

    return 0


def run_demo(args):
    """Run a demonstration with mock data."""
    logger.info("Running demonstration mode with mock data...")
    logger.info("This will showcase the full pipeline without actual LinkedIn access\n")

    handler = LinkedInHandler(mode="demo")

    # Demo: Search multiple industries
    for industry in ["Pulp and Paper Mills", "Steel Manufacturing"]:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Demo: {industry}")
        logger.info("=" * 60)

        companies = handler.identify_target_companies(industry, limit=3)
        companies_with_esg = handler.cross_reference_esg_data(companies)

        for company in companies_with_esg:
            print(f"\n{company.name}")
            print(f"  Industry: {company.industry}")
            print(f"  Carbon Liability: ${company.carbon_liability_estimate / 1_000_000:.1f}M")

            # Extract contacts
            contacts = handler.extract_technical_gatekeepers(company, count=2)
            for contact in contacts:
                print(f"  • {contact.name} - {contact.title}")

                # Generate outreach
                draft = handler.generate_outreach_draft(contact)
                print(f"    Outreach Subject: {draft.subject}")

    # Export demo results if output specified
    if args.output:
        results = handler.run_full_pipeline("Pulp and Paper Mills", 5, 2)
        output_path = Path(args.output)

        if output_path.suffix.lower() == ".json":
            handler.export_to_json(results["contacts"], str(output_path))
        else:
            handler.export_to_csv(results["contacts"], str(output_path))

        logger.info(f"\n✓ Demo results exported to {args.output}")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Technical Gatekeeper identification tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for companies in an industry
  python -m app.cli_linkedin search --industry "Pulp and Paper Mills" --limit 10

  # Extract contacts from a specific company
  python -m app.cli_linkedin extract --industry "Steel Manufacturing" \\
    --company "ArcelorMittal" --count 5

  # Run full pipeline and export results
  python -m app.cli_linkedin pipeline --industry "Pulp and Paper Mills" \\
    --output results.csv --company-limit 20

  # Run demonstration with mock data
  python -m app.cli_linkedin demo --output demo_results.json

Environment Variables:
  LINKEDIN_EMAIL              Your LinkedIn email/username
  LINKEDIN_PASSWORD           Your LinkedIn password (for scraping mode)
  LINKEDIN_API_KEY            LinkedIn API key (for API mode)
  LINKEDIN_RATE_LIMIT_DELAY   Delay between requests in seconds (default: 3)
  LINKEDIN_DAILY_LIMIT        Maximum requests per day (default: 100)

Modes:
  demo      - Use mock data (default, no LinkedIn access required)
  api       - Use LinkedIn API (requires API key)
  scraping  - Web scraping with rate limiting (requires credentials)
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for companies")
    search_parser.add_argument(
        "--industry", "-i", required=True, help="Target industry"
    )
    search_parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Number of companies to find"
    )
    search_parser.add_argument(
        "--mode", "-m", choices=["demo", "api", "scraping"], default="demo", help="Operation mode"
    )

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract contacts from a company")
    extract_parser.add_argument(
        "--industry", "-i", required=True, help="Industry sector"
    )
    extract_parser.add_argument(
        "--company", "-c", required=True, help="Company name"
    )
    extract_parser.add_argument(
        "--count", "-n", type=int, default=3, help="Number of contacts to extract"
    )
    extract_parser.add_argument(
        "--mode", "-m", choices=["demo", "api", "scraping"], default="demo", help="Operation mode"
    )

    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipeline_parser.add_argument(
        "--industry", "-i", required=True, help="Target industry"
    )
    pipeline_parser.add_argument(
        "--company-limit", type=int, default=50, help="Max companies to process"
    )
    pipeline_parser.add_argument(
        "--contacts-per-company", type=int, default=3, help="Contacts per company"
    )
    pipeline_parser.add_argument(
        "--output", "-o", help="Output file path (CSV or JSON)"
    )
    pipeline_parser.add_argument(
        "--esg-data", help="Path to ESG penalty data file (JSON or CSV)"
    )
    pipeline_parser.add_argument(
        "--mode", "-m", choices=["demo", "api", "scraping"], default="demo", help="Operation mode"
    )

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demonstration with mock data")
    demo_parser.add_argument(
        "--output", "-o", help="Output file path (CSV or JSON)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "search":
            return search_companies(args)
        elif args.command == "extract":
            return extract_contacts(args)
        elif args.command == "pipeline":
            return run_pipeline(args)
        elif args.command == "demo":
            return run_demo(args)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
