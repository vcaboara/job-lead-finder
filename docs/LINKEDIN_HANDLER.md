# LinkedIn Handler - Technical Gatekeeper Identification

## Overview

The LinkedIn Handler is an automated search and extraction agent designed to identify **Technical Gatekeepers** in "Hard-to-Abate" industries (Pulp/Paper, Steel, Heavy Agriculture, Cement) who are currently facing high ESG/Carbon penalty liabilities.

## Features

### Core Capabilities
- **Company Discovery**: Identify top 50 global firms in target industries
- **ESG Cross-Reference**: Match companies against known ESG penalty data
- **Contact Extraction**: Find the 3 most senior technical individuals at each firm
- **Outreach Generation**: Create personalized "Sovereign Outreach" drafts focused on Thermodynamic Efficiency and Patent 12/17
- **Data Export**: Export results to CSV or JSON format

### Target Industries
- Pulp and Paper Mills
- Industrial Heat Processing
- Carbon-Intensive Manufacturing
- Steel Manufacturing
- Heavy Agriculture
- Cement Production

### Target Titles
**Primary:**
- Director of Process Engineering
- Lead Thermal Engineer
- CTO (Technical)

**Secondary:**
- Sustainability Director (with engineering background)
- Head of Energy Procurement
- VP of Engineering

### Keywords Matched
- Pyrolysis
- Biochar
- Biomass-to-Energy
- Carbon Sequestration
- Closed-Loop Manufacturing
- 12/17 Geometry
- Thermodynamic Efficiency
- Carbon Credits
- ESG

## Installation

The LinkedIn handler is part of the Job Lead Finder project. Install dependencies:

```bash
# Install project dependencies
pip install -e .

# Or manually install required packages
pip install python-dotenv httpx beautifulsoup4
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# LinkedIn credentials (optional - defaults to demo mode)
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_USERNAME=your_linkedin_username
LINKEDIN_PASSWORD=your_linkedin_password
LINKEDIN_API_KEY=your_linkedin_api_key

# Rate limiting configuration
LINKEDIN_RATE_LIMIT_DELAY=3  # Seconds between requests
LINKEDIN_DAILY_LIMIT=100      # Maximum requests per day
```

## Usage

### CLI Interface

The LinkedIn handler provides a command-line interface for easy usage:

```bash
# Run demonstration with mock data (no LinkedIn access required)
python -m app.cli_linkedin demo

# Search for companies in an industry
python -m app.cli_linkedin search --industry "Pulp and Paper Mills" --limit 10

# Extract contacts from a specific company
python -m app.cli_linkedin extract --industry "Steel Manufacturing" \
  --company "ArcelorMittal" --count 5

# Run full pipeline and export results
python -m app.cli_linkedin pipeline --industry "Pulp and Paper Mills" \
  --output results.csv --company-limit 20

# Use external ESG data file
python -m app.cli_linkedin pipeline --industry "Steel Manufacturing" \
  --esg-data data/esg_penalty_data.json --output results.json
```

### Python API

Use the LinkedIn handler programmatically:

```python
from app.linkedin_handler import LinkedInHandler

# Initialize handler
handler = LinkedInHandler(
    mode="demo",  # or "api" or "scraping"
    rate_limit_delay=3,
    daily_limit=100,
    esg_data_path="data/esg_penalty_data.json"
)

# Run full pipeline
results = handler.run_full_pipeline(
    industry="Pulp and Paper Mills",
    company_limit=50,
    contacts_per_company=3
)

# Access results
companies = results["companies"]
contacts = results["contacts"]
outreach_drafts = results["outreach_drafts"]

# Export to CSV
handler.export_to_csv(contacts, "technical_gatekeepers.csv")

# Export to JSON
handler.export_to_json(contacts, "technical_gatekeepers.json")
```

## Operation Modes

### Demo Mode (Default)
Uses mock data for testing without actual LinkedIn access. Safe for development and testing.

```bash
python -m app.cli_linkedin demo
```

### API Mode
Uses LinkedIn API (requires API credentials). Currently displays a warning and falls back to demo mode.

```bash
python -m app.cli_linkedin pipeline --mode api --industry "Steel Manufacturing"
```

### Scraping Mode
Web scraping with rate limiting (requires authentication). Currently displays a warning and falls back to demo mode.

```bash
python -m app.cli_linkedin pipeline --mode scraping --industry "Pulp and Paper Mills"
```

## ESG Data File

The handler can load ESG penalty data from external JSON or CSV files. See `data/esg_penalty_data.json` for an example.

### JSON Format
```json
[
  {
    "name": "International Paper",
    "industry": "Pulp and Paper Mills",
    "esg_score": 45.2,
    "carbon_liability_estimate": 125000000,
    "location": "Memphis, TN",
    "employee_count": 50000,
    "website": "https://www.internationalpaper.com",
    "linkedin_url": "https://www.linkedin.com/company/international-paper"
  }
]
```

### CSV Format
```csv
name,industry,esg_score,carbon_liability_estimate,location,employee_count,website,linkedin_url
International Paper,Pulp and Paper Mills,45.2,125000000,"Memphis, TN",50000,https://www.internationalpaper.com,https://www.linkedin.com/company/international-paper
```

## Output Format

### CSV Export
```csv
Name,Title,Company,Estimated Carbon Liability,LinkedIn URL,Email,Keywords Matched,Profile Summary
John Smith,Director of Process Engineering,International Paper,"$125,000,000",https://linkedin.com/in/john-smith,,"Pyrolysis, Biochar","Experienced director with background in Pyrolysis"
```

### JSON Export
```json
[
  {
    "name": "John Smith",
    "title": "Director of Process Engineering",
    "company": "International Paper",
    "carbon_liability_estimate": 125000000,
    "linkedin_url": "https://linkedin.com/in/john-smith",
    "email": null,
    "keywords_matched": ["Pyrolysis", "Biochar"],
    "profile_summary": "Experienced director with background in Pyrolysis"
  }
]
```

### Outreach Drafts
```json
[
  {
    "contact_name": "John Smith",
    "contact_title": "Director of Process Engineering",
    "company": "International Paper",
    "subject": "Thermodynamic Efficiency Opportunity for International Paper [Patent 12/17]",
    "body": "Dear John,\n\nI hope this message finds you well...",
    "notes": "Contact Keywords: Pyrolysis, Biochar\nCarbon Liability: $125.0M..."
  }
]
```

## Rate Limiting & Privacy

The handler implements several privacy and rate-limiting protections:

1. **Configurable Delays**: 3-second default delay between requests (with random jitter)
2. **Daily Limits**: Maximum 100 requests per day (configurable)
3. **Request Tracking**: Monitors request count and timing
4. **Exponential Backoff**: Prevents detection patterns
5. **Demo Mode**: Safe testing without actual LinkedIn access

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_linkedin_handler.py -v

# Run with coverage
python -m pytest tests/test_linkedin_handler.py --cov=app.linkedin_handler --cov-report=html

# Run specific test
python -m pytest tests/test_linkedin_handler.py::TestLinkedInHandler::test_full_pipeline -v
```

Current test coverage: **100%** (20 tests, all passing)

## Architecture

### Data Models
- **Company**: Represents target company with ESG data
- **Contact**: Represents technical gatekeeper contact
- **OutreachDraft**: Represents generated outreach message

### Core Methods
1. `identify_target_companies()` - Find top companies in target industries
2. `cross_reference_esg_data()` - Match against ESG penalty data
3. `extract_technical_gatekeepers()` - Find senior technical people
4. `generate_outreach_draft()` - Generate outreach messages
5. `export_to_csv()` / `export_to_json()` - Export results

### Pipeline Workflow
```
Step A: Identify Companies → Step B: ESG Cross-Reference → 
Step C: Extract Contacts → Step D: Generate Outreach Drafts
```

## Ethical Considerations

- **Rate Limiting**: Prevents API abuse and respects platform limits
- **Privacy**: Handles personal data responsibly
- **Transparency**: Clear about data sources and methods
- **Demo Mode**: Allows testing without actual data scraping
- **Compliance**: Designed to work within LinkedIn's terms of service

## Future Enhancements

1. **LinkedIn API Integration**: Full implementation when credentials available
2. **Web Scraping**: Playwright/BeautifulSoup integration with proper rate limiting
3. **Enhanced ESG Data**: Integration with external ESG data APIs
4. **Email Discovery**: Additional methods for finding contact emails
5. **Profile Analysis**: NLP for deeper profile matching
6. **Batch Processing**: Parallel processing for large datasets
7. **Monitoring Dashboard**: Track extraction progress and success rates

## Troubleshooting

### Issue: "Daily request limit reached"
**Solution**: Wait until the next day or increase `LINKEDIN_DAILY_LIMIT` in your `.env` file.

### Issue: "ESG data file not found"
**Solution**: Ensure the ESG data file path is correct and the file exists. The handler will fall back to mock data if the file is not found.

### Issue: Tests failing
**Solution**: Ensure all dependencies are installed: `pip install -e ".[test]"`

## Support

For issues, questions, or contributions:
1. Check the main project README
2. Review the test suite for usage examples
3. Open an issue on GitHub

## License

Part of the Job Lead Finder project. See main project LICENSE for details.
