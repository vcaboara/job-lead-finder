# Patent Analysis Framework

AI-powered patent analysis framework for pyrolysis technologies and waste-to-energy systems.

## Purpose

Analyze patent claims for:
- **Technical validity** - Verify claims against pyrolysis engineering principles
- **Prior art conflicts** - Search Google Patents for conflicting existing patents
- **Commercial viability** - Assess market potential and licensee opportunities
- **Claim quality** - Evaluate clarity, scope, and patentability

## Key Features

- 📄 **Patent Document Parser** - Extract claims from PDF documents
- 🔍 **Prior Art Search** - Google Patents API integration with semantic search
- 🔬 **Technical Feasibility** - Pyrolysis domain expert validation
- ✍️ **Claim Drafting** - AI-assisted claim generation from technical briefs
- 📊 **Market Analysis** - Identify potential licensees and assess TRL
- 🤖 **AI Providers** - Gemini API and Ollama support with fallback chains

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Run tests
pytest

# Start web UI
python -m src.ui.server
```

## Usage

### Upload and Analyze Patent Draft

```python
from src.analyzers.patent_analyzer import PatentAnalyzer
from src.parsers.pdf_parser import PDFPatentParser

# Parse patent PDF
parser = PDFPatentParser()
patent = parser.parse("my_pyrolysis_patent.pdf")

# Analyze claims
analyzer = PatentAnalyzer()
results = analyzer.analyze(
    claims=patent.claims,
    domain="pyrolysis",
    check_prior_art=True,
    assess_feasibility=True
)

# Review report
print(results.summary)
print(f"Prior art conflicts: {len(results.prior_art)}")
print(f"Technical issues: {len(results.technical_issues)}")
```

### Draft New Claims from Technical Brief

```python
from src.drafting.claim_generator import ClaimGenerator

generator = ClaimGenerator()
claims = generator.generate_from_brief(
    technical_brief="technical_description.txt",
    examples=["example_patent1.pdf", "example_patent2.pdf"],
    domain="pyrolysis"
)

print(claims.independent_claims)
print(claims.dependent_claims)
```

## Project Structure

```
patent-analysis-framework/
├── src/
│   ├── analyzers/       # Patent claim analysis
│   ├── parsers/         # PDF and document parsers
│   ├── search/          # Prior art search
│   ├── drafting/        # Claim drafting assistant
│   ├── providers/       # AI provider integrations
│   ├── knowledge/       # Pyrolysis domain expertise
│   └── ui/              # Flask web interface
├── data/                # Patent documents and results
├── tests/               # Test suite
└── docs/                # Documentation
```

## Pyrolysis Domain

This framework includes specialized knowledge for:
- **Thermal decomposition systems** (300-900°C)
- **Reactor types**: Fixed bed, fluidized bed, rotary kiln, microwave
- **Products**: Bio-oil, syngas, biochar
- **Applications**: Waste-to-energy, carbon sequestration, green fuels
- **Feedstocks**: Biomass, plastics, tires, agricultural waste

## AI Integration

Supports multiple AI providers:
- **Gemini API** - Primary provider for analysis and drafting
- **Ollama** - Local LLM for privacy-sensitive operations
- **Fallback chains** - Automatic failover for reliability

## Configuration

Create `.env` file:

```bash
# AI Providers
GEMINI_API_KEY=your_gemini_api_key
OLLAMA_BASE_URL=http://localhost:11434

# Google Patents
GOOGLE_PATENTS_API_KEY=optional_for_higher_rate_limits

# Application
FLASK_PORT=8000
DEBUG=False
```

## Development

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Format code
black src tests
isort src tests

# Type checking
mypy src

# Lint
flake8 src tests
```

## License

MIT License - See LICENSE file

## Contributing

This project is designed to help bring pollution-reducing, regenerative technologies to market faster. Contributions welcome!

## Goals

1. Review patent drafts for technical and legal validity
2. Draft new patent claims from technical briefs
3. Find first licensees for pyrolysis innovations
4. Accelerate deployment of waste-to-energy solutions
