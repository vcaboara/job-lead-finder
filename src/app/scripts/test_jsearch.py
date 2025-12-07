"""Quick test script for JSearch provider.

Usage:
    python -m src.app.scripts.test_jsearch [--query "python developer"] [--limit 10]
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.app.discovery.providers.jsearch_provider import JSearchProvider

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def main():
    """Test JSearch provider with real API calls."""
    parser = argparse.ArgumentParser(description="Test JSearch provider")
    parser.add_argument(
        "--query",
        default="python developer",
        help="Job search query (default: python developer)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of companies to return (default: 10)")
    parser.add_argument("--location", default="remote", help="Location to search (default: remote)")
    parser.add_argument(
        "--date-posted",
        default="week",
        choices=["all", "today", "3days", "week", "month"],
        help="Date posted filter (default: week)",
    )
    parser.add_argument(
        "--remote-only",
        action="store_true",
        help="Only show remote jobs",
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    if not os.getenv("RAPIDAPI_KEY"):
        print("ERROR: RAPIDAPI_KEY environment variable not found")
        print("Please add your RapidAPI key to .env file")
        print("Get your key at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        sys.exit(1)

    print("[JSearch Test] Initializing provider...")
    provider = JSearchProvider()

    print(f"[JSearch Test] Searching for: '{args.query}' in '{args.location}'")
    print(
        f"[JSearch Test] Filters: limit={args.limit}, "
        f"date_posted={args.date_posted}, remote_only={args.remote_only}"
    )
    print()

    try:
        result = provider.discover_companies(
            {
                "query": args.query,
                "locations": [args.location],
                "limit": args.limit,
                "date_posted": args.date_posted,
                "remote_jobs_only": args.remote_only,
            }
        )

        print("[JSearch Test] Discovery complete!")
        print(f"[JSearch Test] Found {len(result.companies)} unique companies")
        print()

        if result.companies:
            print("=" * 80)
            for i, company in enumerate(result.companies, 1):
                print(f"\n{i}. {company.name}")
                print(f"   Website: {company.website or 'N/A'}")
                print(f"   Careers: {company.careers_url or 'N/A'}")
                print(f"   Industry: {company.industry.value}")
                print(f"   Size: {company.size.value}")
                print(f"   Locations: {', '.join(company.locations) if company.locations else 'N/A'}")
                print(f"   Tech Stack: {', '.join(company.tech_stack) if company.tech_stack else 'N/A'}")
                if company.metadata.get("job_title"):
                    print(f"   Job Title: {company.metadata['job_title']}")
            print("=" * 80)

            # Save to JSON file
            output_file = Path("jsearch_discovery_results.json")
            with output_file.open("w", encoding="utf-8") as f:
                # Convert to serializable format
                companies_data = [
                    {
                        "name": c.name,
                        "website": c.website,
                        "careers_url": c.careers_url,
                        "industry": c.industry.value,
                        "size": c.size.value,
                        "locations": c.locations,
                        "tech_stack": c.tech_stack,
                        "description": c.description,
                        "metadata": c.metadata,
                    }
                    for c in result.companies
                ]
                json.dump(
                    {
                        "source": result.source,
                        "total_found": result.total_found,
                        "timestamp": result.timestamp.isoformat(),
                        "companies": companies_data,
                        "metadata": result.metadata,
                    },
                    f,
                    indent=2,
                )

            print(f"\n[JSearch Test] Results saved to: {output_file}")
        else:
            print("[JSearch Test] No companies found. Try a different search query.")

    except Exception as e:
        print(f"[JSearch Test] ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
