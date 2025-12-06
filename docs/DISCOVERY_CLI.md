# Company Discovery CLI Guide

The `discover` command enables passive job discovery by searching for real-time job listings and extracting company information. This is powered by the JSearch API via RapidAPI.

## Setup

1. **Get RapidAPI Key**:
   - Sign up at https://rapidapi.com
   - Subscribe to JSearch API: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
   - Copy your API key

2. **Add to .env file**:
   ```bash
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

## Basic Usage

```bash
# Search for companies hiring Python developers
python -m app.main discover -q "Python developer"

# Search in specific location
python -m app.main discover -q "DevOps engineer" -l "San Francisco, CA"

# Search remote positions
python -m app.main discover -q "Machine Learning" -l "Remote"

# Limit results
python -m app.main discover -q "Frontend developer" -n 10

# Save to database
python -m app.main discover -q "Backend engineer" --save

# Verbose output
python -m app.main discover -q "Data scientist" --verbose
```

## Advanced Filtering

```bash
# Filter by tech stack
python -m app.main discover -q "Full stack" -t Python React AWS

# Filter by industry
python -m app.main discover -q "Software engineer" -i tech

# Combine filters
python -m app.main discover -q "Cloud engineer" -l "Austin, TX" -t AWS Docker Kubernetes -n 20 --save --verbose
```

## Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--query` | `-q` | Job search query | "Software Engineer" |
| `--location` | `-l` | Location filter | None (all locations) |
| `--industry` | `-i` | Industry filter (tech, finance, etc.) | None |
| `--tech-stack` | `-t` | Tech stack filter (space-separated) | None |
| `--max-results` | `-n` | Maximum results to fetch | 20 |
| `--save` | `-s` | Save results to database | False |
| `--verbose` | `-v` | Show detailed output | False |

## Output Format

For each company discovered, you'll see:

- Company name
- Website (if available)
- Careers URL (if available)
- Locations
- Industry
- Company size
- Tech stack (detected from job descriptions)
- Description (first 150 characters)

## Database Storage

When using `--save`, companies are stored in `data/discovery.db` (SQLite).

**Note**: Companies without websites are automatically skipped during save, as the database schema requires a unique website URL for each company.

## Examples

### Find AI/ML Companies in Silicon Valley
```bash
python -m app.main discover -q "Machine Learning Engineer" -l "San Francisco" -t Python TensorFlow PyTorch -n 15 --save
```

### Find Remote DevOps Positions
```bash
python -m app.main discover -q "DevOps" -l "Remote" -t Kubernetes AWS Docker -n 25 --save --verbose
```

### Find Startups Hiring Backend Engineers
```bash
python -m app.main discover -q "Backend developer startup" -l "New York" -t Python Go -n 10
```

## Tips

1. **Be specific**: More specific queries yield better results
   - Good: "Senior Python developer Django"
   - Less specific: "developer"

2. **Use location strategically**:
   - "Remote" finds remote positions
   - City names find local opportunities
   - Combine for hybrid: "San Francisco OR Remote"

3. **Tech stack detection**: The system automatically detects 30+ technologies including:
   - Languages: Python, JavaScript, Go, Rust, Java, C++, etc.
   - Frameworks: React, Vue, Django, FastAPI, etc.
   - Cloud: AWS, GCP, Azure
   - Tools: Docker, Kubernetes, Terraform, etc.

4. **Save for later**: Use `--save` to build a database of companies you can query later

## Troubleshooting

### "RAPIDAPI_KEY not found"
Make sure you've added your RapidAPI key to the `.env` file in the project root.

### No results returned
- Check your query is not too specific
- Try a broader location (e.g., state instead of city)
- Remove tech stack filters temporarily

### Companies skipped during save
Companies without websites can't be saved to the database due to schema constraints. This is expected behavior and will be shown in verbose mode.

## Next Steps

After discovering companies:
1. Review the database: `sqlite3 data/discovery.db "SELECT * FROM companies;"`
2. Filter by tech stack: Search for companies using specific technologies
3. Track job applications: Use the web UI to track applications
4. Set up monitoring: (Coming soon) Automated daily discovery runs

## Related Documentation

- [JSearch Provider Documentation](JSEARCH_PROVIDER.md) - Technical details
- [Company Store API](../src/app/discovery/company_store.py) - Database schema
- [Discovery Configuration](../src/app/discovery/config.py) - Discovery settings
