# AI Search Match Framework (ASMF)

A reusable framework for AI-powered search and analysis applications. Provides common infrastructure for job finding, patent evaluation, grant finding, and similar use cases.

## Features

### 1. AI Provider Abstraction (`smf.providers`)

- **BaseAIProvider**: Abstract base class for AI providers
- **AIProviderFactory**: Factory with automatic fallback between providers
- Built-in support for Ollama (local) and Gemini (cloud)
- Easy to extend with new providers (OpenAI, Anthropic, etc.)

**Usage:**

```python
from smf.providers import get_factory

# Get factory instance
factory = get_factory()

# Auto-select best available provider (Ollama -> Gemini)
provider = factory.create_with_fallback()

# Or create specific provider
provider = factory.create_provider('ollama')

# Use provider
result = provider.evaluate(item, profile_text)
print(f"Score: {result['score']}, Reasoning: {result['reasoning']}")
```

### 2. Document Parsing (`smf.parsers`)

- **PDFParser**: Extract text from PDF files (uses pypdf)
- **DOCXParser**: Extract text from DOCX files with macro detection (uses python-docx)
- **TXTParser**: Handle plain text and markdown files

**Usage:**

```python
from smf.parsers import PDFParser, DOCXParser, TXTParser

# Parse PDF
pdf_parser = PDFParser()
text = pdf_parser.parse(pdf_bytes)

# Parse DOCX (with macro security check)
docx_parser = DOCXParser()
text = docx_parser.parse(docx_bytes)

# Get metadata
metadata = pdf_parser.get_metadata(pdf_bytes)
print(f"Pages: {metadata['pages']}")
```

### 3. Analysis Patterns (`smf.analyzers`)

- **BaseAnalyzer**: Abstract pattern for domain-specific analysis
- Supports single-item and batch analysis
- Built-in validation and feature extraction

**Usage:**

```python
from smf.analyzers import BaseAnalyzer
from smf.providers import get_factory

class MyAnalyzer(BaseAnalyzer):
    def analyze_single(self, item, profile):
        return self.provider.evaluate(item, profile)
    
    def extract_key_features(self, item):
        return [item['title'], item['technology']]
    
    def get_required_fields(self):
        return ['title', 'company']

# Use analyzer
provider = get_factory().create_with_fallback()
analyzer = MyAnalyzer(provider)

# Analyze single item
result = analyzer.analyze_single(job, resume)

# Analyze batch with top N results
results = analyzer.analyze_batch(jobs, resume, top_n=10)
```

### 4. Configuration & Logging (`smf.utils`)

- JSON configuration management
- Environment variable support
- Structured logging setup

**Usage:**

```python
from smf.utils import load_config, save_config, setup_logging, get_logger

# Setup logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Load configuration
config = load_config('config.json', default={'threshold': 0.7})

# Save configuration
save_config({'threshold': 0.8}, 'config.json')
```

## Architecture

ASMF follows a modular architecture:

```
smf/
├── providers/       # AI provider abstraction
│   ├── base_provider.py      # Abstract base class
│   └── factory.py            # Factory with fallback
├── parsers/         # Document parsing
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   └── txt_parser.py
├── analyzers/       # Analysis patterns
│   └── base.py               # BaseAnalyzer
└── utils/           # Utilities
    ├── config.py
    └── logging.py
```

## Benefits

1. **Consistency**: Same patterns across all projects
2. **Maintainability**: Bug fixes in ASMF benefit all projects
3. **Reduced Duplication**: Less code to maintain in each project
4. **Better Testing**: Rely on ASMF's tested components
5. **Easy Extension**: Add new providers, parsers, or analyzers easily

## Integration Example: Job Lead Finder

See how job-lead-finder uses ASMF:

```python
# 1. Provider usage (job_finder.py)
from smf.providers import get_factory

def _get_evaluation_provider():
    factory = get_factory()
    return factory.create_with_fallback()

# 2. Custom analyzer (job_lead_analyzer.py)
from smf.analyzers import BaseAnalyzer

class JobLeadAnalyzer(BaseAnalyzer):
    def analyze_single(self, job, resume):
        return self.provider.evaluate(job, resume)
    
    def get_required_fields(self):
        return ['title', 'company']

# 3. Document parsing (ui_server.py)
from smf.parsers import PDFParser, DOCXParser

pdf_parser = PDFParser()
resume_text = pdf_parser.parse(pdf_content)
```

## Extending ASMF

### Adding a New Provider

```python
from smf.providers import BaseAIProvider

class MyCustomProvider(BaseAIProvider):
    def __init__(self, api_key=None, model=None, request_timeout=90):
        self.api_key = api_key
        self.model = model
        
    def query(self, prompt, **options):
        # Implement API call
        pass
    
    def evaluate(self, item, profile_text):
        # Implement evaluation logic
        pass
    
    def is_available(self):
        # Check if provider is configured and available
        return self.api_key is not None

# Register with factory
factory = get_factory()
factory.register_provider('my_custom', MyCustomProvider, priority=2)
```

### Adding a New Parser

```python
from smf.parsers import DocumentParser

class XMLParser(DocumentParser):
    def parse(self, content):
        # Parse XML content
        pass
    
    def supports_format(self, filename):
        return filename.lower().endswith('.xml')
```

## Future Enhancements

- Add more providers (OpenAI, Anthropic, Claude)
- Add streaming support for long-running analyses
- Add caching layer for provider responses
- Add retry logic with exponential backoff
- Add rate limiting and quota management
- Extract to separate PyPI package

## Related Projects

- **job-lead-finder**: Job search with AI evaluation
- **ai-patent-eval**: Patent analysis and commercialization
- **grant-finder**: Research grant matching

All use ASMF for consistency and code reuse.
